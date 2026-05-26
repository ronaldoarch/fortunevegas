"""
Módulo para integração com a API Keiko Exchange (Keiko Bank)
Documentação: https://api.keikobank.com
"""
import httpx
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class KeikoAPI:
    DEFAULT_BASE_URL = "https://api.keikobank.com"

    def __init__(self, client_id: str, client_secret: str, api_url: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = (api_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self.headers = {"Content-Type": "application/json"}

    async def _authenticate(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/auth/integrations/token",
                    headers={"Content-Type": "application/json"},
                    json={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                )
                print(f"Keiko Auth Response Status: {response.status_code}")
                print(f"Keiko Auth Response: {response.text}")

                if response.status_code >= 400:
                    return False

                auth_data = response.json()
                self._access_token = auth_data.get("access_token")
                expires_in = auth_data.get("expires_in", 3600)
                self._token_expires_at = datetime.utcnow() + timedelta(seconds=max(expires_in - 60, 60))
                return bool(self._access_token)
        except Exception as e:
            print(f"Erro ao autenticar Keiko: {str(e)}")
            return False

    async def _ensure_authenticated(self):
        if self._access_token and self._token_expires_at and datetime.utcnow() < self._token_expires_at:
            return
        if not await self._authenticate():
            raise Exception("Falha na autenticação com Keiko Exchange")

    def _auth_headers(self) -> Dict[str, str]:
        return {
            **self.headers,
            "Authorization": f"Bearer {self._access_token}",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        await self._ensure_authenticated()
        url = f"{self.api_url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method,
                    url,
                    headers=self._auth_headers(),
                    json=payload,
                    params=params,
                )
                print(f"Keiko {method} {endpoint}")
                if payload:
                    print(f"Keiko Payload: {json.dumps(payload, indent=2)}")
                print(f"Keiko Response Status: {response.status_code}")
                print(f"Keiko Response: {response.text}")

                if response.status_code >= 400:
                    try:
                        error_json = response.json()
                    except Exception:
                        error_json = {}
                    error_message = (
                        error_json.get("message")
                        or error_json.get("error")
                        or response.text
                    )
                    return {
                        "error": True,
                        "status_code": response.status_code,
                        "detail": error_message,
                        "keiko_response": error_json,
                    }

                if not response.text:
                    return {}
                return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else "Sem resposta"
            return {"error": True, "status_code": e.response.status_code, "detail": error_detail}
        except Exception as e:
            print(f"Erro ao chamar Keiko {endpoint}: {str(e)}")
            return {"error": True, "detail": str(e)}

    async def create_pix_charge(
        self,
        amount: float,
        payer_name: str,
        payer_document: str,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """POST /pix/in/charges - Gera cobrança PIX dinâmica (Cash-in)"""
        payload: Dict[str, Any] = {
            "client_id": self.client_id,
            "amount": amount,
            "currency": "BRL",
            "payer": {
                "name": payer_name,
                "document": payer_document,
            },
        }
        if description:
            payload["description"] = description
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key

        return await self._request("POST", "/pix/in/charges", payload=payload)

    async def create_pix_transfer(
        self,
        amount: float,
        beneficiary_name: str,
        pix_key: str,
        pix_key_type: str,
        beneficiary_document: Optional[str] = None,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """POST /pix/out/transfers - Cria saque PIX (Cash-out)"""
        beneficiary: Dict[str, Any] = {
            "name": beneficiary_name,
            "pix_key": pix_key,
            "pix_key_type": pix_key_type,
        }
        if beneficiary_document:
            beneficiary["document"] = beneficiary_document

        payload: Dict[str, Any] = {
            "client_id": self.client_id,
            "amount": amount,
            "currency": "BRL",
            "beneficiary": beneficiary,
        }
        if description:
            payload["description"] = description
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key

        return await self._request("POST", "/pix/out/transfers", payload=payload)

    async def get_transaction(
        self,
        transaction_id: str,
    ) -> Optional[Dict[str, Any]]:
        """GET /transactions - Consulta transação normalizada"""
        return await self._request(
            "GET",
            "/transactions",
            params={
                "client_id": self.client_id,
                "transaction_id": transaction_id,
            },
        )

    async def get_balance_summary(self) -> Optional[Dict[str, Any]]:
        """GET /clients/{client_id}/balance-summary"""
        return await self._request(
            "GET",
            f"/clients/{self.client_id}/balance-summary",
        )
