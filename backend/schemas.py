from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import TransactionStatus, UserRole, MediaType


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    cpf: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    balance: Optional[float] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    id: int
    role: UserRole
    balance: float
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


# Gateway Schemas
class GatewayBase(BaseModel):
    name: str
    type: str
    is_active: bool = True
    credentials: Optional[str] = None


class GatewayCreate(GatewayBase):
    pass


class GatewayUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    credentials: Optional[str] = None


class GatewayResponse(GatewayBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# IGameWin Agent Schemas
class IGameWinAgentBase(BaseModel):
    agent_code: str
    agent_key: str
    api_url: str = "https://api.igamewin.com"
    is_active: bool = True
    credentials: Optional[str] = None


class IGameWinAgentCreate(IGameWinAgentBase):
    pass


class IGameWinAgentUpdate(BaseModel):
    agent_code: Optional[str] = None
    agent_key: Optional[str] = None
    api_url: Optional[str] = None
    is_active: Optional[bool] = None
    credentials: Optional[str] = None


class IGameWinAgentResponse(IGameWinAgentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Deposit Schemas
class DepositBase(BaseModel):
    user_id: int
    gateway_id: Optional[int] = None
    amount: float
    metadata_json: Optional[str] = None


class DepositCreate(DepositBase):
    pass


class DepositUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    external_id: Optional[str] = None
    metadata_json: Optional[str] = None


class DepositResponse(DepositBase):
    id: int
    status: TransactionStatus
    transaction_id: str
    external_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Withdrawal Schemas
class WithdrawalBase(BaseModel):
    user_id: int
    gateway_id: Optional[int] = None
    amount: float
    metadata_json: Optional[str] = None


class WithdrawalCreate(WithdrawalBase):
    pass


class WithdrawalUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    external_id: Optional[str] = None
    metadata_json: Optional[str] = None


class WithdrawalResponse(WithdrawalBase):
    id: int
    status: TransactionStatus
    transaction_id: str
    external_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# FTD Schemas
class FTDBase(BaseModel):
    user_id: int
    deposit_id: int
    amount: float
    pass_rate: float = 0.0


class FTDCreate(FTDBase):
    pass


class FTDUpdate(BaseModel):
    pass_rate: Optional[float] = None
    status: Optional[TransactionStatus] = None


class FTDResponse(FTDBase):
    id: int
    is_first_deposit: bool
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# FTD Settings Schemas
class FTDSettingsBase(BaseModel):
    pass_rate: float = 0.0
    min_amount: float = 0.0
    is_active: bool = True


class FTDSettingsCreate(FTDSettingsBase):
    pass


class FTDSettingsUpdate(FTDSettingsBase):
    pass


class FTDSettingsResponse(FTDSettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Media Asset Schemas
class MediaAssetResponse(BaseModel):
    id: int
    type: str
    url: str
    filename: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    is_active: bool
    position: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Game Layout Schemas
class GameLayoutBase(BaseModel):
    game_code: str
    provider_code: Optional[str] = None
    position: int = 0
    is_featured: bool = False
    section: str = "home"
    is_active: bool = True


class GameLayoutCreate(GameLayoutBase):
    pass


class GameLayoutUpdate(BaseModel):
    position: Optional[int] = None
    is_featured: Optional[bool] = None
    section: Optional[str] = None
    is_active: Optional[bool] = None


class GameLayoutResponse(GameLayoutBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Theme Schemas
class ThemeBase(BaseModel):
    name: str
    is_default: bool = False
    is_active: bool = True
    colors_json: str  # JSON string com as cores


class ThemeCreate(ThemeBase):
    pass


class ThemeUpdate(BaseModel):
    name: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    colors_json: Optional[str] = None


class ThemeResponse(ThemeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Affiliate Schemas
class AffiliateBase(BaseModel):
    code: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    commission_rate: float = 0.0
    is_active: bool = True
    metadata_json: Optional[str] = None


class AffiliateCreate(AffiliateBase):
    pass


class AffiliateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    commission_rate: Optional[float] = None
    is_active: Optional[bool] = None
    metadata_json: Optional[str] = None


class AffiliateResponse(AffiliateBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
