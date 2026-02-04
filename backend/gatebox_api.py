"""
Módulo para integração com a API Gatebox
Documentação: https://api.gatebox.com.br
"""
import httpx
import json
from typing import Optional, Dict, Any
import os


class GateboxAPI:
    def __init__(self, username: str, password: str, api_url: str = "https://api.gatebox.com.br"):
        """
        Inicializa a API Gatebox
        
        Args:
            username: Username da conta Gatebox
            password: Password da conta Gatebox
            api_url: URL base da API (padrão: https://api.gatebox.com.br)
        """
        self.username = username
        self.password = password
        self.api_url = api_url.rstrip('/')
        self.token = None
        self.headers = {
            "Content-Type": "application/json"
        }
    
    async def _authenticate(self) -> bool:
        """
        Autentica na API Gatebox e obtém o token de acesso
        
        Returns:
            True se autenticação foi bem-sucedida, False caso contrário
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/v1/customers/auth/sign-in",
                    headers=self.headers,
                    json={
                        "username": self.username,
                        "password": self.password
                    }
                )
                
                print(f"Gatebox Auth Response Status: {response.status_code}")
                print(f"Gatebox Auth Response: {response.text}")
                
                response.raise_for_status()
                auth_data = response.json()
                
                self.token = auth_data.get("access_token")
                if self.token:
                    self.headers["Authorization"] = f"Bearer {self.token}"
                    return True
                return False
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else "Sem resposta"
            print(f"Erro HTTP Gatebox Auth: {e.response.status_code} - {error_detail}")
            return False
        except Exception as e:
            print(f"Erro ao autenticar Gatebox: {str(e)}")
            return False
    
    async def _ensure_authenticated(self):
        """Garante que está autenticado antes de fazer requisições"""
        if not self.token:
            if not await self._authenticate():
                raise Exception("Falha na autenticação com Gatebox")
    
    async def _post(self, endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Faz requisição POST para a API Gatebox"""
        await self._ensure_authenticated()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}{endpoint}",
                    headers=self.headers,
                    json=payload
                )
                
                # Log detalhado para debug
                print(f"Gatebox Request: {endpoint}")
                print(f"Gatebox Payload: {json.dumps(payload, indent=2)}")
                print(f"Gatebox Response Status: {response.status_code}")
                print(f"Gatebox Response: {response.text}")
                
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else "Sem resposta"
            print(f"Erro HTTP Gatebox {endpoint}: {e.response.status_code} - {error_detail}")
            try:
                error_json = e.response.json() if e.response else {}
                error_message = error_json.get("message") or error_json.get("error") or error_detail
                return {
                    "error": True,
                    "status_code": e.response.status_code,
                    "detail": error_message,
                    "gatebox_response": error_json
                }
            except:
                return {"error": True, "status_code": e.response.status_code, "detail": error_detail}
        except Exception as e:
            print(f"Erro ao chamar Gatebox {endpoint}: {str(e)}")
            return {"error": True, "detail": str(e)}
    
    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Faz requisição GET para a API Gatebox"""
        await self._ensure_authenticated()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.api_url}{endpoint}",
                    headers=self.headers,
                    params=params or {}
                )
                
                print(f"Gatebox GET Request: {endpoint}")
                print(f"Gatebox GET Params: {params}")
                print(f"Gatebox GET Response Status: {response.status_code}")
                print(f"Gatebox GET Response: {response.text}")
                
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else "Sem resposta"
            print(f"Erro HTTP Gatebox GET {endpoint}: {e.response.status_code} - {error_detail}")
            try:
                error_json = e.response.json() if e.response else {}
                error_message = error_json.get("message") or error_json.get("error") or error_detail
                return {
                    "error": True,
                    "status_code": e.response.status_code,
                    "detail": error_message,
                    "gatebox_response": error_json
                }
            except:
                return {"error": True, "status_code": e.response.status_code, "detail": error_detail}
        except Exception as e:
            print(f"Erro ao chamar Gatebox GET {endpoint}: {str(e)}")
            return {"error": True, "detail": str(e)}
    
    async def create_immediate_qrcode(
        self,
        external_id: str,
        amount: float,
        name: str,
        expire: int = 3600,
        document: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        identification: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Cria QR Code PIX imediato (Cash-in)
        Endpoint: POST /v1/customers/pix/create-immediate-qrcode
        
        Args:
            external_id: ID de conciliação único
            amount: Valor do depósito
            name: Nome completo do pagador
            expire: Tempo de expiração em segundos (padrão: 3600 = 1 hora)
            document: CPF/CNPJ do pagador (opcional, sem pontuação)
            email: Email do pagador (opcional)
            phone: Telefone do pagador (opcional, formato: +5514987654321)
            identification: Descrição a ser exibida no momento do pagamento (opcional)
            description: Descrição da transação (opcional)
        
        Returns:
            Dict com dados do PIX ou None em caso de erro
        """
        import re
        
        payload = {
            "externalId": external_id,
            "amount": amount,
            "name": name,
            "expire": expire
        }
        
        # Só adicionar document se fornecido e válido (CPF tem 11 dígitos, CNPJ tem 14)
        if document:
            document_clean = re.sub(r'[^0-9]', '', document)
            # Validar se é CPF (11 dígitos) ou CNPJ (14 dígitos)
            if len(document_clean) == 11 or len(document_clean) == 14:
                payload["document"] = document_clean
        
        if email:
            payload["email"] = email
        if phone:
            payload["phone"] = phone
        if identification:
            payload["identification"] = identification
        if description:
            payload["description"] = description
        
        result = await self._post("/v1/customers/pix/create-immediate-qrcode", payload)
        
        if result and result.get("error"):
            return result
        
        return result
    
    async def withdraw_pix(
        self,
        external_id: str,
        key: str,
        name: str,
        amount: float,
        document_number: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Realiza transferência via PIX (Cash-out)
        Endpoint: POST /v1/customers/pix/withdraw
        
        Args:
            external_id: ID de conciliação único
            key: Chave PIX do recebedor
            name: Nome completo do recebedor
            amount: Valor do saque
            document_number: CPF/CNPJ do recebedor (obrigatório apenas se validação de chave pix estiver ativa)
            description: Descrição da transação (opcional)
        
        Returns:
            Dict com dados da transferência ou None em caso de erro
        """
        import re
        
        payload = {
            "externalId": external_id,
            "key": key,
            "name": name,
            "amount": amount
        }
        
        if document_number:
            # Limpar documento (remover pontuação)
            document_clean = re.sub(r'[^0-9]', '', document_number)
            payload["documentNumber"] = document_clean
        
        if description:
            payload["description"] = description
        
        result = await self._post("/v1/customers/pix/withdraw", payload)
        
        if result and result.get("error"):
            return result
        
        return result
    
    async def get_pix_status(
        self,
        transaction_id: Optional[str] = None,
        external_id: Optional[str] = None,
        end_to_end: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Consulta status de transação PIX
        Endpoint: GET /v1/customers/pix/status
        
        Args:
            transaction_id: ID da transação (opcional)
            external_id: ID externo de conciliação (opcional)
            end_to_end: EndToEnd da transação (opcional)
        
        Returns:
            Dict com status da transação ou None em caso de erro
        """
        params = {}
        if transaction_id:
            params["transactionId"] = transaction_id
        if external_id:
            params["externalId"] = external_id
        if end_to_end:
            params["endToEnd"] = end_to_end
        
        if not params:
            return {"error": True, "detail": "É necessário informar pelo menos um parâmetro: transactionId, externalId ou endToEnd"}
        
        return await self._get("/v1/customers/pix/status", params)
    
    async def validate_pix_key(self, pix_key: str) -> Optional[Dict[str, Any]]:
        """
        Valida chave PIX
        Endpoint: GET /v1/customers/pix/pix-search
        
        Args:
            pix_key: Chave PIX a ser verificada (sem pontuação)
        
        Returns:
            Dict com dados da chave PIX ou None em caso de erro
        """
        import re
        
        # Limpar chave (remover pontuação)
        pix_key_clean = re.sub(r'[^0-9a-zA-Z@.]', '', pix_key)
        
        return await self._get("/v1/customers/pix/pix-search", {"dict": pix_key_clean})
    
    async def get_balance(self) -> Optional[Dict[str, Any]]:
        """
        Consulta saldo da conta
        Endpoint: POST /v1/customers/account/balance
        
        Returns:
            Dict com saldo da conta ou None em caso de erro
        """
        return await self._post("/v1/customers/account/balance", {})