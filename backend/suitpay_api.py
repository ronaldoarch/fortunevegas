"""
Módulo para integração com a API SuitPay
Documentação: https://sandbox.ws.suitpay.app (sandbox) ou https://ws.suitpay.app (produção)
"""
import httpx
import json
from typing import Optional, Dict, Any
import os


class SuitPayAPI:
    def __init__(self, client_id: str, client_secret: str, sandbox: bool = True):
        """
        Inicializa a API SuitPay
        
        Args:
            client_id: Client ID (ci) da SuitPay
            client_secret: Client Secret (cs) da SuitPay
            sandbox: Se True, usa ambiente sandbox, senão usa produção
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://sandbox.ws.suitpay.app" if sandbox else "https://ws.suitpay.app"
        self.headers = {
            "ci": client_id,
            "cs": client_secret,
            "Content-Type": "application/json"
        }
    
    async def _post(self, endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Faz requisição POST para a API SuitPay"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    json=payload
                )
                
                # Log detalhado para debug
                print(f"SuitPay Request: {endpoint}")
                print(f"SuitPay Payload: {json.dumps(payload, indent=2)}")
                print(f"SuitPay Response Status: {response.status_code}")
                print(f"SuitPay Response: {response.text}")
                
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else "Sem resposta"
            print(f"Erro HTTP SuitPay {endpoint}: {e.response.status_code} - {error_detail}")
            # Retornar dict com erro para melhor tratamento
            try:
                error_json = e.response.json() if e.response else {}
                return {"error": True, "status_code": e.response.status_code, "detail": error_json.get("message") or error_detail}
            except:
                return {"error": True, "status_code": e.response.status_code, "detail": error_detail}
        except Exception as e:
            print(f"Erro ao chamar SuitPay {endpoint}: {str(e)}")
            return {"error": True, "detail": str(e)}
    
    async def generate_pix_payment(
        self,
        value: float,
        payer_name: str,
        payer_tax_id: str,
        payer_email: str,
        request_number: str,
        url_callback: Optional[str] = None,
        payer_phone: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Gera código de pagamento PIX (Cash-in)
        Endpoint: POST /api/v1/gateway/request-qrcode
        
        Args:
            value: Valor do pagamento
            payer_name: Nome do pagador
            payer_tax_id: CPF/CNPJ do pagador (será limpo automaticamente)
            payer_email: Email do pagador
            request_number: Número único da requisição (para controle)
            url_callback: URL do webhook (opcional)
            payer_phone: Telefone do pagador (opcional, formato: DDD+TELEFONE)
            due_date: Data de vencimento (opcional, formato: AAAA-MM-DD)
        
        Returns:
            Dict com dados do PIX ou None em caso de erro
        """
        from datetime import datetime, timedelta
        import re
        
        # Limpar CPF/CNPJ (remover pontos, traços e espaços)
        payer_tax_id_clean = re.sub(r'[^0-9]', '', payer_tax_id) if payer_tax_id else ""
        
        # Limpar telefone se fornecido (remover parênteses, traços, espaços)
        payer_phone_clean = None
        if payer_phone:
            payer_phone_clean = re.sub(r'[^0-9]', '', payer_phone)
        
        # Se não informada, usar data de hoje + 1 dia
        if not due_date:
            due_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        payload = {
            "requestNumber": request_number,
            "dueDate": due_date,
            "amount": value,
            "shippingAmount": 0.0,
            "discountAmount": 0.0,
            "client": {
                "name": payer_name,
                "document": payer_tax_id_clean,
                "email": payer_email
            }
        }
        
        if payer_phone_clean:
            payload["client"]["phoneNumber"] = payer_phone_clean
        
        if url_callback:
            payload["callbackUrl"] = url_callback
        
        # Endpoint correto conforme documentação SuitPay
        # POST /api/v1/gateway/request-qrcode
        result = await self._post("/api/v1/gateway/request-qrcode", payload)
        
        # Verificar se retornou erro
        if result and result.get("error"):
            return None
        
        return result
    
    async def transfer_pix(
        self,
        value: float,
        pix_key: str,
        type_key: str,
        url_callback: Optional[str] = None,
        document_validation: Optional[str] = None,
        external_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Realiza transferência via PIX (Cash-out)
        Endpoint: POST /api/v1/gateway/pix-payment
        
        Args:
            value: Valor da transferência
            pix_key: Chave PIX (CPF, CNPJ, telefone, email ou chave aleatória)
            type_key: Tipo da chave PIX: "document", "phoneNumber", "email", "randomKey", "paymentCode"
            url_callback: URL do webhook (opcional)
            document_validation: CPF/CNPJ para validar se pertence à chave PIX (opcional)
            external_id: ID externo para controle de duplicidade (opcional)
        
        Returns:
            Dict com dados da transferência ou None em caso de erro
        """
        payload = {
            "value": value,
            "key": pix_key,
            "typeKey": type_key
        }
        
        if url_callback:
            payload["callbackUrl"] = url_callback
        
        if document_validation:
            payload["documentValidation"] = document_validation
        
        if external_id:
            payload["externalId"] = external_id
        
        # Endpoint correto conforme documentação SuitPay
        # POST /api/v1/gateway/pix-payment
        return await self._post("/api/v1/gateway/pix-payment", payload)
    
    @staticmethod
    def validate_webhook_hash(data: Dict[str, Any], client_secret: str) -> bool:
        """
        Valida o hash do webhook recebido da SuitPay
        
        Args:
            data: Dados do webhook (JSON)
            client_secret: Client Secret (cs) da SuitPay
        
        Returns:
            True se o hash for válido, False caso contrário
        """
        import hashlib
        
        # Remove o hash do dict para calcular
        received_hash = data.pop("hash", None)
        if not received_hash:
            return False
        
        # Concatena todos os valores (exceto hash) em ordem
        values = []
        for key in sorted(data.keys()):
            value = data.get(key)
            if value is not None:
                values.append(str(value))
        
        # Concatena com client_secret
        string_to_hash = "".join(values) + client_secret
        
        # Calcula SHA-256
        calculated_hash = hashlib.sha256(string_to_hash.encode()).hexdigest()
        
        # Restaura o hash no dict
        data["hash"] = received_hash
        
        # Compara hashes
        return calculated_hash.lower() == received_hash.lower()
