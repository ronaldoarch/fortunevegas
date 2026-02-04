"""
Utilitário para disparar webhooks configurados quando eventos acontecem
"""
import httpx
import json
import base64
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from models import Webhook, WebhookEventType


async def dispatch_webhook(
    db: Session,
    event_type: WebhookEventType,
    payload: Dict[str, Any]
) -> None:
    """
    Dispara webhooks configurados para um tipo de evento específico
    
    Args:
        db: Sessão do banco de dados
        event_type: Tipo de evento (PIX_PAY_IN, PIX_PAY_OUT, etc)
        payload: Dados a serem enviados no webhook
    """
    # Buscar webhooks ativos para este tipo de evento
    webhooks = db.query(Webhook).filter(
        Webhook.event_type == event_type,
        Webhook.is_active == True
    ).all()
    
    if not webhooks:
        print(f"Nenhum webhook ativo encontrado para evento: {event_type}")
        return
    
    # Disparar cada webhook
    for webhook in webhooks:
        try:
            await _send_webhook(webhook, payload)
            print(f"Webhook {webhook.id} disparado com sucesso para {webhook.url}")
        except Exception as e:
            print(f"Erro ao disparar webhook {webhook.id} ({webhook.url}): {str(e)}")
            # Continuar com outros webhooks mesmo se um falhar


async def _send_webhook(webhook: Webhook, payload: Dict[str, Any]) -> None:
    """
    Envia requisição HTTP para um webhook específico
    
    Args:
        webhook: Instância do Webhook
        payload: Dados a serem enviados
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    # Adicionar autenticação HTTP Basic se username/password estiverem configurados
    if webhook.username and webhook.password:
        credentials = f"{webhook.username}:{webhook.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_credentials}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            webhook.url,
            json=payload,
            headers=headers
        )
        response.raise_for_status()
