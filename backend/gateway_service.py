"""
Serviço de abstração para gateways de pagamento PIX (Gatebox, Keiko Exchange).
"""
import json
import re
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException, status

from models import Gateway
from gatebox_api import GateboxAPI
from keiko_api import KeikoAPI


PROVIDER_GATEBOX = "gatebox"
PROVIDER_KEIKO = "keiko"


def parse_gateway_credentials(gateway: Gateway) -> Dict[str, Any]:
    try:
        return json.loads(gateway.credentials) if gateway.credentials else {}
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credenciais do gateway inválidas",
        )


def detect_gateway_provider(credentials: Dict[str, Any], gateway_name: str = "") -> str:
    provider = (credentials.get("provider") or "").strip().lower()
    if provider in (PROVIDER_GATEBOX, PROVIDER_KEIKO):
        return provider

    if credentials.get("client_id") and credentials.get("client_secret"):
        return PROVIDER_KEIKO

    if credentials.get("username") and credentials.get("password"):
        return PROVIDER_GATEBOX

    name_lower = (gateway_name or "").lower()
    if "keiko" in name_lower:
        return PROVIDER_KEIKO
    if "gatebox" in name_lower:
        return PROVIDER_GATEBOX

    return PROVIDER_GATEBOX


def get_gateway_provider(gateway: Gateway) -> str:
    credentials = parse_gateway_credentials(gateway)
    return detect_gateway_provider(credentials, gateway.name)


def get_gatebox_client(gateway: Gateway) -> GateboxAPI:
    credentials = parse_gateway_credentials(gateway)
    username = credentials.get("username")
    password = credentials.get("password")
    api_url = credentials.get("api_url", "https://api.gatebox.com.br")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credenciais Gatebox não configuradas (username e password são obrigatórios)",
        )

    return GateboxAPI(username=username, password=password, api_url=api_url)


def get_keiko_client(gateway: Gateway) -> KeikoAPI:
    credentials = parse_gateway_credentials(gateway)
    client_id = credentials.get("client_id")
    client_secret = credentials.get("client_secret")
    api_url = credentials.get("api_url", KeikoAPI.DEFAULT_BASE_URL)

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credenciais Keiko não configuradas (client_id e client_secret são obrigatórios)",
        )

    return KeikoAPI(client_id=client_id, client_secret=client_secret, api_url=api_url)


def map_pix_key_type_to_keiko(type_key: str) -> str:
    mapping = {
        "CPF": "cpf",
        "CNPJ": "cnpj",
        "EMAIL": "email",
        "TELEFONE": "phone",
        "ALEATORIA": "random",
        "RANDOM": "random",
        "PHONE": "phone",
    }
    return mapping.get((type_key or "").upper(), "random")


def format_phone_for_keiko(pix_key: str) -> str:
    pix_key_clean = re.sub(r"[^0-9+]", "", pix_key.strip())
    if pix_key_clean.startswith("+"):
        if not pix_key_clean.startswith("+55"):
            digits = re.sub(r"[^0-9]", "", pix_key_clean)
            if digits.startswith("55"):
                return f"+{digits}"
            return f"+55{digits}"
        return pix_key_clean

    digits = re.sub(r"[^0-9]", "", pix_key_clean)
    if digits.startswith("55"):
        return f"+{digits}"
    return f"+55{digits}"


def extract_pix_from_keiko_charge(response: Dict[str, Any]) -> Tuple[str, str, str]:
    """Retorna (br_code, pay_url, transaction_id)"""
    qr_code = response.get("qr_code") or {}
    br_code = qr_code.get("br_code") or ""
    pay_url = qr_code.get("pay_url") or ""
    transaction_id = (
        response.get("transaction_id")
        or response.get("provider_order")
        or ""
    )
    return br_code, pay_url, transaction_id


def normalize_keiko_status(status: Optional[str], event: Optional[str] = None) -> str:
    value = (status or event or "").lower()
    if value in ("succeeded", "success", "completed", "paid", "approved"):
        return "SUCCESS"
    if value in ("failed", "rejected", "error", "canceled", "cancelled"):
        return "FAILED"
    if "refunded" in value:
        return "REFUNDED"
    if value in ("pending", "processing", "created"):
        return "PENDING"
    return value.upper() if value else "PENDING"


def normalize_keiko_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """Converte payload Keiko para formato interno usado pelos processadores de webhook."""
    event = data.get("event") or ""
    status_raw = data.get("status") or ""
    transaction = data.get("transaction") or {}
    reference = data.get("reference") or {}

    transaction_id = transaction.get("id") or reference.get("transaction_ref")
    direction = (transaction.get("direction") or "").upper()
    end_to_end = reference.get("end2end_id") or reference.get("end_to_end_id")
    amount = transaction.get("amount")

    normalized_status = normalize_keiko_status(status_raw, event)

    return {
        "event": event,
        "status": normalized_status,
        "status_transaction": normalized_status,
        "transaction_id": transaction_id,
        "external_id": reference.get("transaction_ref"),
        "end_to_end": end_to_end,
        "amount": amount,
        "direction": direction,
        "keiko_raw": data,
    }
