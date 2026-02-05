import httpx
import json
from typing import Optional, Dict, Any, List
from models import IGameWinAgent
from sqlalchemy.orm import Session


class IGameWinAPI:
    def __init__(
        self,
        agent_code: str,
        agent_key: str,
        api_url: str = "https://igamewin.com",
        credentials: Optional[Dict[str, Any]] = None
    ):
        self.agent_code = agent_code
        self.agent_key = agent_key  # maps to agent_token in requests
        self.api_url = api_url.rstrip('/')
        # Detect base url for /api/v1 according to doc
        if self.api_url.endswith("/api/v1"):
            self.base_url = self.api_url
        elif self.api_url.endswith("/api"):
            self.base_url = f"{self.api_url}/v1"
        else:
            self.base_url = f"{self.api_url}/api/v1"
        self.credentials = credentials or {}
        self.last_error: Optional[str] = None
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json"
        }
    
    async def create_user(self, user_code: str, is_demo: bool = False) -> Optional[Dict[str, Any]]:
        """Create user in igamewin system - follows IGameWin API documentation"""
        payload = {
            "method": "user_create",
            "agent_code": self.agent_code,
            "agent_token": self.agent_key,
            "user_code": user_code
        }
        if is_demo:
            payload["is_demo"] = True
        
        data = await self._post(payload)
        if not data:
            return None
        
        # Verificar se status é 1 (sucesso)
        if data.get("status") == 1:
            return data
        
        return None
    
    async def get_agent_balance(self) -> Optional[float]:
        """Get agent balance from igamewin - follows IGameWin API documentation"""
        payload = {
            "method": "money_info",
            "agent_code": self.agent_code,
            "agent_token": self.agent_key
        }
        
        data = await self._post(payload)
        if not data:
            return None
        
        # A resposta tem estrutura: {"status": 1, "agent": {"agent_code": "...", "balance": ...}}
        agent_info = data.get("agent")
        if agent_info:
            return agent_info.get("balance", 0.0)
        
        return None

    async def get_user_balance(self, user_code: str) -> Optional[float]:
        """Get user balance from igamewin - follows IGameWin API documentation"""
        payload = {
            "method": "money_info",
            "agent_code": self.agent_code,
            "agent_token": self.agent_key,
            "user_code": user_code
        }
        
        data = await self._post(payload)
        if not data:
            return None
        
        # A resposta tem estrutura: {"status": 1, "agent": {...}, "user": {"user_code": "...", "balance": ...}}
        user_info = data.get("user")
        if user_info:
            return user_info.get("balance", 0.0)
        
        return None
    
    # Métodos de transferência removidos - sistema agora usa apenas modo Seamless
    # No modo Seamless, o saldo é gerenciado localmente via API /gold_api
    # e não há necessidade de transferir saldo para/do IGameWin
    
    # async def transfer_in(...) - REMOVIDO (modo transfer desabilitado)
    # async def transfer_out(...) - REMOVIDO (modo transfer desabilitado)
    
    async def _post(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        self.last_error = None
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                # API de business retorna status 1/0
                if isinstance(data, dict) and data.get("status") not in (None, 1):
                    self.last_error = f"status={data.get('status')} msg={data.get('msg')}"
                    return None
                return data
            except httpx.HTTPError as e:
                body_preview = ""
                try:
                    body_preview = e.response.text[:500] if hasattr(e, "response") and e.response else ""
                except Exception:
                    pass
                self.last_error = f"{e} {body_preview}"
                print(f"Error calling igamewin: {self.last_error}")
                return None

    async def get_providers(self) -> Optional[List[Dict[str, Any]]]:
        payload = {
            "method": "provider_list",
            "agent_code": self.agent_code,
            "agent_token": self.agent_key
        }
        data = await self._post(payload)
        if not data:
            return None
        return data.get("providers")

    async def get_games(self, provider_code: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        payload: Dict[str, Any] = {
            "method": "game_list",
            "agent_code": self.agent_code,
            "agent_token": self.agent_key
        }
        if provider_code:
            payload["provider_code"] = provider_code
        # Allow provider_code from credentials default
        if not provider_code and isinstance(self.credentials, dict):
            default_provider = self.credentials.get("provider_code")
            if default_provider:
                payload["provider_code"] = default_provider

        data = await self._post(payload)
        if not data:
            return None
        return data.get("games")

    async def launch_game(self, user_code: str, game_code: str, provider_code: Optional[str] = None, lang: str = "pt") -> Optional[str]:
        """Generate game launch URL for user - follows IGameWin API documentation"""
        payload: Dict[str, Any] = {
            "method": "game_launch",
            "agent_code": self.agent_code,
            "agent_token": self.agent_key,
            "user_code": user_code,
            "game_code": game_code,
            "lang": lang
        }
        if provider_code:
            payload["provider_code"] = provider_code
        
        data = await self._post(payload)
        if not data:
            return None
        
        # A resposta de sucesso tem "launch_url" conforme documentação
        launch_url = data.get("launch_url")
        if launch_url:
            return launch_url
        
        return None


def get_igamewin_api(db: Session) -> Optional[IGameWinAPI]:
    """Get active igamewin agent and return API instance"""
    agent = db.query(IGameWinAgent).filter(IGameWinAgent.is_active == True).first()
    if not agent:
        return None
    credentials_dict: Dict[str, Any] = {}
    if agent.credentials:
        try:
            credentials_dict = json.loads(agent.credentials)
        except Exception:
            credentials_dict = {}
    return IGameWinAPI(
        agent_code=agent.agent_code,
        agent_key=agent.agent_key,
        api_url=agent.api_url,
        credentials=credentials_dict
    )
