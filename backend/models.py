from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    cpf = Column(String(14), unique=True, index=True)
    phone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    affiliate_id = Column(Integer, ForeignKey("affiliates.id"), nullable=True)  # Afiliado que trouxe o usuário
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    deposits = relationship("Deposit", back_populates="user")
    withdrawals = relationship("Withdrawal", back_populates="user")
    ftds = relationship("FTD", back_populates="user")
    bets = relationship("Bet")
    notifications = relationship("Notification")
    affiliate = relationship("Affiliate")


class Gateway(Base):
    __tablename__ = "gateways"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(50), nullable=False)  # pix, card, etc
    is_active = Column(Boolean, default=True, nullable=False)
    credentials = Column(Text)  # JSON string with credentials
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IGameWinAgent(Base):
    __tablename__ = "igamewin_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_code = Column(String(100), unique=True, nullable=False)
    agent_key = Column(String(255), nullable=False)
    api_url = Column(String(255), default="https://api.igamewin.com", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    credentials = Column(Text)  # JSON string with additional credentials
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Deposit(Base):
    __tablename__ = "deposits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    gateway_id = Column(Integer, ForeignKey("gateways.id"))
    amount = Column(Float, nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    transaction_id = Column(String(255), unique=True, index=True)
    external_id = Column(String(255), index=True)  # ID from gateway
    metadata_json = Column(Text)  # JSON string with additional data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="deposits")
    gateway = relationship("Gateway")


class Withdrawal(Base):
    __tablename__ = "withdrawals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    gateway_id = Column(Integer, ForeignKey("gateways.id"))
    amount = Column(Float, nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    transaction_id = Column(String(255), unique=True, index=True)
    external_id = Column(String(255), index=True)
    metadata_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="withdrawals")
    gateway = relationship("Gateway")


class FTD(Base):
    __tablename__ = "ftds"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    deposit_id = Column(Integer, ForeignKey("deposits.id"), nullable=False)
    amount = Column(Float, nullable=False)
    is_first_deposit = Column(Boolean, default=True, nullable=False)
    pass_rate = Column(Float, default=0.0, nullable=False)  # Taxa de passagem
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="ftds")


class FTDSettings(Base):
    __tablename__ = "ftd_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    pass_rate = Column(Float, default=0.0, nullable=False)  # Taxa de passagem padrão
    min_amount = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MediaType(str, enum.Enum):
    LOGO = "logo"
    BANNER = "banner"


class MediaAsset(Base):
    __tablename__ = "media_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(MediaType), nullable=False, index=True)
    url = Column(String(500), nullable=False)  # URL relativa: /uploads/banners/arquivo.jpg
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer)  # Tamanho em bytes
    mime_type = Column(String(100))  # image/jpeg, image/png, etc
    is_active = Column(Boolean, default=True, nullable=False)
    position = Column(Integer, default=0, nullable=False)  # Ordem para banners
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BetStatus(str, enum.Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"


class Bet(Base):
    __tablename__ = "bets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(String(255))  # ID do jogo (IGameWin ou outro provider)
    game_name = Column(String(255))  # Nome do jogo
    provider = Column(String(100))  # IGameWin, Pragmatic, etc
    amount = Column(Float, nullable=False)  # Valor da aposta
    win_amount = Column(Float, default=0.0)  # Valor ganho (0 se perdeu)
    status = Column(Enum(BetStatus), default=BetStatus.PENDING, nullable=False)
    transaction_id = Column(String(255), unique=True, index=True)
    external_id = Column(String(255), index=True)  # ID do provider externo
    metadata_json = Column(Text)  # JSON com dados adicionais do jogo
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")


class NotificationType(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROMOTION = "promotion"


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), default=NotificationType.INFO, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null = notificação global
    is_read = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    link = Column(String(500))  # Link opcional (ex: /promo/bonus)
    metadata_json = Column(Text)  # JSON com dados adicionais
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")


class ProviderLayout(Base):
    """Configuração de ordem dos provedores na home"""
    __tablename__ = "provider_layouts"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_code = Column(String(100), unique=True, nullable=False, index=True)  # Código do provedor (ex: PGSOFT, PRAGMATIC)
    provider_name = Column(String(255), nullable=False)  # Nome exibido do provedor
    position = Column(Integer, default=0, nullable=False)  # Posição na home (0 = primeiro)
    max_games = Column(Integer, default=30, nullable=False)  # Máximo de jogos a exibir (0 = todos)
    is_active = Column(Boolean, default=True, nullable=False)  # Se o provedor aparece na home
    section = Column(String(100), default="home")  # Seção (home, featured, etc)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GameLayout(Base):
    """Configuração de layout da grade de jogos na home"""
    __tablename__ = "game_layouts"
    
    id = Column(Integer, primary_key=True, index=True)
    game_code = Column(String(255), nullable=False, index=True)  # Código do jogo (ex: vs20doghouse)
    provider_code = Column(String(100))  # Código do provedor (ex: PRAGMATIC)
    position = Column(Integer, default=0, nullable=False)  # Posição na grade (0 = primeiro)
    is_featured = Column(Boolean, default=False, nullable=False)  # Jogo em destaque
    section = Column(String(100), default="home")  # Seção (home, featured, etc)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Theme(Base):
    """Temas de cores da plataforma"""
    __tablename__ = "themes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)  # Tema padrão
    is_active = Column(Boolean, default=True, nullable=False)
    # Cores em JSON
    colors_json = Column(Text, nullable=False)  # JSON: {bg, surface, card, accent, accentSoft, text, muted}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Affiliate(Base):
    """Sistema de afiliados"""
    __tablename__ = "affiliates"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)  # Código único do afiliado
    name = Column(String(255), nullable=False)  # Nome do afiliado
    email = Column(String(255))
    phone = Column(String(20))
    commission_rate = Column(Float, default=0.0, nullable=False)  # Taxa de comissão (0-100)
    is_active = Column(Boolean, default=True, nullable=False)
    metadata_json = Column(Text)  # JSON com dados adicionais
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - linkar usuários a afiliados
    # user.affiliate_id seria adicionado em User se necessário
