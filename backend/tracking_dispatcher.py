"""
Utilitário para disparar eventos de tracking (pixels, APIs) para conversões
"""
import httpx
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from models import TrackingConfig, TrackingType


async def dispatch_tracking_event(
    db: Session,
    event_name: str,  # "registration", "first_deposit", "redeposit"
    payload: Dict[str, Any]
) -> None:
    """
    Dispara eventos de tracking para configurações ativas (pixels e APIs)
    
    Args:
        db: Sessão do banco de dados
        event_name: Nome do evento ("registration", "first_deposit", "redeposit")
        payload: Dados do evento (user_id, amount, etc)
    """
    # Buscar configurações de tracking ativas
    tracking_configs = db.query(TrackingConfig).filter(
        TrackingConfig.is_active == True
    ).all()
    
    if not tracking_configs:
        print(f"[TRACKING] Nenhuma configuração de tracking ativa encontrada para evento: {event_name}")
        return
    
    # Disparar cada configuração
    for config in tracking_configs:
        try:
            if config.type == TrackingType.PIXEL:
                await _send_pixel_event(config, event_name, payload)
            elif config.type == TrackingType.API:
                await _send_api_event(config, event_name, payload)
            elif config.type == TrackingType.WEBHOOK:
                await _send_webhook_event(config, event_name, payload)
            print(f"[TRACKING] Evento {event_name} enviado com sucesso para {config.name} (ID: {config.id})")
        except Exception as e:
            print(f"[TRACKING] Erro ao enviar evento {event_name} para {config.name} (ID: {config.id}): {str(e)}")
            # Continuar com outras configurações mesmo se uma falhar


async def _send_pixel_event(config: TrackingConfig, event_name: str, payload: Dict[str, Any]) -> None:
    """
    Envia evento para pixel (Facebook Pixel, Google Pixel, etc)
    """
    if not config.pixel_id:
        print(f"[TRACKING] Pixel ID não configurado para {config.name}")
        return
    
    # Para Facebook Pixel, usar Facebook Conversions API
    # Para outros pixels, pode precisar de implementação específica
    pixel_data = {
        "event_name": event_name,
        "event_id": f"{payload.get('user_id', 'unknown')}_{payload.get('timestamp', '')}",
        "user_data": {
            "external_id": str(payload.get("user_id", "")),
            "email": payload.get("email", ""),
            "phone_number": payload.get("phone", ""),
        },
        "custom_data": {
            "currency": "BRL",
            "value": payload.get("amount", 0),
        }
    }
    
    # Se tiver access_token, usar Conversions API
    if config.access_token:
        url = f"https://graph.facebook.com/v18.0/{config.pixel_id}/events"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "data": [pixel_data],
            "access_token": config.access_token
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
    else:
        # Se não tiver token, apenas logar (pixel pode ser implementado no frontend)
        print(f"[TRACKING] Pixel {config.name} - Evento: {event_name}, Dados: {json.dumps(pixel_data)}")


async def _send_api_event(config: TrackingConfig, event_name: str, payload: Dict[str, Any]) -> None:
    """
    Envia evento para API externa
    """
    if not config.url:
        print(f"[TRACKING] URL não configurada para API {config.name}")
        return
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Adicionar autenticação se disponível
    if config.access_token:
        headers["Authorization"] = f"Bearer {config.access_token}"
    elif config.api_key:
        headers["X-API-Key"] = config.api_key
    
    # Preparar dados do evento
    api_data = {
        "event": event_name,
        "timestamp": payload.get("timestamp"),
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "phone": payload.get("phone"),
        "amount": payload.get("amount"),
        "currency": "BRL",
        "metadata": payload.get("metadata", {})
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(config.url, json=api_data, headers=headers)
        response.raise_for_status()


async def _send_webhook_event(config: TrackingConfig, event_name: str, payload: Dict[str, Any]) -> None:
    """
    Envia evento para webhook customizado
    """
    if not config.url:
        print(f"[TRACKING] URL não configurada para webhook {config.name}")
        return
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Adicionar autenticação se disponível
    if config.access_token:
        headers["Authorization"] = f"Bearer {config.access_token}"
    elif config.api_key:
        headers["X-API-Key"] = config.api_key
    
    webhook_data = {
        "event": event_name,
        "timestamp": payload.get("timestamp"),
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "phone": payload.get("phone"),
        "amount": payload.get("amount"),
        "currency": "BRL",
        "metadata": payload.get("metadata", {})
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(config.url, json=webhook_data, headers=headers)
        response.raise_for_status()
