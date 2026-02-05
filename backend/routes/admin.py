from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import uuid
import json

from database import get_db
from dependencies import get_current_admin_user, get_current_user
from models import (
    Webhook,
    WebhookEventType,
    User, Deposit, Withdrawal, FTD, Gateway, IGameWinAgent, FTDSettings,
    TransactionStatus, UserRole, Bet, BetStatus, Notification, NotificationType,
    GameLayout, ProviderLayout, Theme, Affiliate,
    IGameWinProviderConfig, TrackingConfig, TrackingType,
    SubAffiliate, ManagerSettings, AffiliateMetric, AffiliateMetricType,
    Coupon, CouponUse, Promotion, PromotionUse, PromotionType
)
import schemas
from schemas import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    UserResponse, UserCreate, UserUpdate,
    DepositResponse, DepositCreate, DepositUpdate,
    WithdrawalResponse, WithdrawalCreate, WithdrawalUpdate,
    FTDResponse, FTDCreate, FTDUpdate,
    GatewayResponse, GatewayCreate, GatewayUpdate,
    IGameWinAgentResponse, IGameWinAgentCreate, IGameWinAgentUpdate,
    FTDSettingsResponse, FTDSettingsCreate, FTDSettingsUpdate,
    GameLayoutResponse, GameLayoutCreate, GameLayoutUpdate,
    ProviderLayoutResponse, ProviderLayoutCreate, ProviderLayoutUpdate,
    ThemeResponse, ThemeCreate, ThemeUpdate,
    AffiliateResponse, AffiliateCreate, AffiliateUpdate,
    IGameWinProviderConfigResponse, IGameWinProviderConfigCreate, IGameWinProviderConfigUpdate,
    TrackingConfigResponse, TrackingConfigCreate, TrackingConfigUpdate,
    AffiliateMetricResponse, AffiliateMetricCreate
)
from auth import get_password_hash
from igamewin_api import get_igamewin_api

router = APIRouter(prefix="/api/admin", tags=["admin"])
public_router = APIRouter(prefix="/api/public", tags=["public"])
seamless_router = APIRouter(prefix="", tags=["seamless"])  # Router sem prefixo para /gold_api


# ========== USERS ==========
@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    affiliate_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    query = db.query(User)
    if affiliate_id is not None:
        query = query.filter(User.affiliate_id == affiliate_id)
    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        cpf=user_data.cpf,
        phone=user_data.phone,
        password_hash=get_password_hash(user_data.password),
        role=UserRole.USER,
        balance=0.0,
        is_active=True,
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return None


# ========== DEPOSITS ==========
@router.get("/deposits", response_model=List[DepositResponse])
async def get_deposits(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[TransactionStatus] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    query = db.query(Deposit)
    if status_filter:
        query = query.filter(Deposit.status == status_filter)
    if user_id:
        query = query.filter(Deposit.user_id == user_id)
    deposits = query.order_by(desc(Deposit.created_at)).offset(skip).limit(limit).all()
    return deposits


@router.get("/deposits/{deposit_id}", response_model=DepositResponse)
async def get_deposit(
    deposit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    deposit = db.query(Deposit).filter(Deposit.id == deposit_id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    return deposit


@router.post("/deposits", response_model=DepositResponse, status_code=status.HTTP_201_CREATED)
async def create_deposit(
    deposit_data: DepositCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == deposit_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    transaction_id = f"DEP_{uuid.uuid4().hex[:16].upper()}"
    deposit = Deposit(
        user_id=deposit_data.user_id,
        gateway_id=deposit_data.gateway_id,
        amount=deposit_data.amount,
        status=TransactionStatus.PENDING,
        transaction_id=transaction_id,
        metadata_json=deposit_data.metadata_json
    )
    db.add(deposit)
    db.commit()
    db.refresh(deposit)
    return deposit


@router.put("/deposits/{deposit_id}", response_model=DepositResponse)
async def update_deposit(
    deposit_id: int,
    deposit_data: DepositUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    deposit = db.query(Deposit).filter(Deposit.id == deposit_id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    
    update_data = deposit_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deposit, field, value)
    
    # If approved, update user balance
    if deposit_data.status == TransactionStatus.APPROVED and deposit.status != TransactionStatus.APPROVED:
        user = db.query(User).filter(User.id == deposit.user_id).first()
        user.balance += deposit.amount
        
        # Check if this is first deposit (FTD)
        existing_ftd = db.query(FTD).filter(FTD.user_id == deposit.user_id).first()
        if not existing_ftd:
            # Create FTD
            ftd_settings = db.query(FTDSettings).filter(FTDSettings.is_active == True).first()
            pass_rate = ftd_settings.pass_rate if ftd_settings else 0.0
            
            ftd = FTD(
                user_id=deposit.user_id,
                deposit_id=deposit.id,
                amount=deposit.amount,
                is_first_deposit=True,
                pass_rate=pass_rate,
                status=TransactionStatus.APPROVED
            )
            db.add(ftd)
    
    db.commit()
    db.refresh(deposit)
    return deposit


# ========== WITHDRAWALS ==========
@router.get("/withdrawals", response_model=List[WithdrawalResponse])
async def get_withdrawals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[TransactionStatus] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    query = db.query(Withdrawal)
    if status_filter:
        query = query.filter(Withdrawal.status == status_filter)
    if user_id:
        query = query.filter(Withdrawal.user_id == user_id)
    withdrawals = query.order_by(desc(Withdrawal.created_at)).offset(skip).limit(limit).all()
    return withdrawals


@router.get("/withdrawals/{withdrawal_id}", response_model=WithdrawalResponse)
async def get_withdrawal(
    withdrawal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    withdrawal = db.query(Withdrawal).filter(Withdrawal.id == withdrawal_id).first()
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    return withdrawal


@router.post("/withdrawals", response_model=WithdrawalResponse, status_code=status.HTTP_201_CREATED)
async def create_withdrawal(
    withdrawal_data: WithdrawalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == withdrawal_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.balance < withdrawal_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    transaction_id = f"WD_{uuid.uuid4().hex[:16].upper()}"
    withdrawal = Withdrawal(
        user_id=withdrawal_data.user_id,
        gateway_id=withdrawal_data.gateway_id,
        amount=withdrawal_data.amount,
        status=TransactionStatus.PENDING,
        transaction_id=transaction_id,
        metadata_json=withdrawal_data.metadata_json
    )
    db.add(withdrawal)
    db.commit()
    db.refresh(withdrawal)
    return withdrawal


@router.put("/withdrawals/{withdrawal_id}", response_model=WithdrawalResponse)
async def update_withdrawal(
    withdrawal_id: int,
    withdrawal_data: WithdrawalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    withdrawal = db.query(Withdrawal).filter(Withdrawal.id == withdrawal_id).first()
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    update_data = withdrawal_data.model_dump(exclude_unset=True)
    
    # If approved, deduct from user balance
    if withdrawal_data.status == TransactionStatus.APPROVED and withdrawal.status != TransactionStatus.APPROVED:
        user = db.query(User).filter(User.id == withdrawal.user_id).first()
        if user.balance < withdrawal.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        user.balance -= withdrawal.amount
    # If rejected or cancelled and was approved, refund
    elif withdrawal_data.status in [TransactionStatus.REJECTED, TransactionStatus.CANCELLED] and withdrawal.status == TransactionStatus.APPROVED:
        user = db.query(User).filter(User.id == withdrawal.user_id).first()
        user.balance += withdrawal.amount
    
    for field, value in update_data.items():
        setattr(withdrawal, field, value)
    
    db.commit()
    db.refresh(withdrawal)
    return withdrawal


# ========== FTDs ==========
@router.get("/ftds", response_model=List[FTDResponse])
async def get_ftds(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    query = db.query(FTD)
    if user_id:
        query = query.filter(FTD.user_id == user_id)
    ftds = query.order_by(desc(FTD.created_at)).offset(skip).limit(limit).all()
    return ftds


@router.get("/ftds/{ftd_id}", response_model=FTDResponse)
async def get_ftd(
    ftd_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    ftd = db.query(FTD).filter(FTD.id == ftd_id).first()
    if not ftd:
        raise HTTPException(status_code=404, detail="FTD not found")
    return ftd


@router.put("/ftds/{ftd_id}", response_model=FTDResponse)
async def update_ftd(
    ftd_id: int,
    ftd_data: FTDUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    ftd = db.query(FTD).filter(FTD.id == ftd_id).first()
    if not ftd:
        raise HTTPException(status_code=404, detail="FTD not found")
    
    update_data = ftd_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ftd, field, value)
    
    db.commit()
    db.refresh(ftd)
    return ftd


@router.get("/ftd-settings", response_model=FTDSettingsResponse)
async def get_ftd_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    settings = db.query(FTDSettings).filter(FTDSettings.is_active == True).first()
    if not settings:
        # Create default settings
        settings = FTDSettings(pass_rate=0.0, min_amount=0.0, max_amount=0.0, min_withdrawal=0.0, is_active=True)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    # Retornar apenas os campos relevantes (sem pass_rate)
    return settings


@router.put("/ftd-settings", response_model=FTDSettingsResponse)
async def update_ftd_settings(
    settings_data: FTDSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    settings = db.query(FTDSettings).filter(FTDSettings.is_active == True).first()
    if not settings:
        # Criar novo com pass_rate padrão 0.0
        settings_data_dict = settings_data.model_dump()
        settings_data_dict['pass_rate'] = 0.0  # Manter pass_rate como 0.0 por padrão
        if 'max_amount' not in settings_data_dict:
            settings_data_dict['max_amount'] = 0.0  # Sem limite por padrão
        settings = FTDSettings(**settings_data_dict)
        db.add(settings)
    else:
        # Atualizar apenas os campos fornecidos, manter pass_rate se não fornecido
        update_data = settings_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        # Se pass_rate não foi fornecido, manter o valor atual (ou 0.0)
    
    db.commit()
    db.refresh(settings)
    return settings


# ========== GATEWAYS ==========
@router.get("/gateways", response_model=List[GatewayResponse])
async def get_gateways(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    gateways = db.query(Gateway).all()
    return gateways


@router.get("/gateways/{gateway_id}", response_model=GatewayResponse)
async def get_gateway(
    gateway_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    gateway = db.query(Gateway).filter(Gateway.id == gateway_id).first()
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return gateway


@router.post("/gateways", response_model=GatewayResponse, status_code=status.HTTP_201_CREATED)
async def create_gateway(
    gateway_data: GatewayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    existing = db.query(Gateway).filter(Gateway.name == gateway_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Gateway name already exists")
    
    gateway = Gateway(**gateway_data.model_dump())
    db.add(gateway)
    db.commit()
    db.refresh(gateway)
    return gateway


@router.put("/gateways/{gateway_id}", response_model=GatewayResponse)
async def update_gateway(
    gateway_id: int,
    gateway_data: GatewayUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    gateway = db.query(Gateway).filter(Gateway.id == gateway_id).first()
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    
    update_data = gateway_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(gateway, field, value)
    
    db.commit()
    db.refresh(gateway)
    return gateway


@router.delete("/gateways/{gateway_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gateway(
    gateway_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    gateway = db.query(Gateway).filter(Gateway.id == gateway_id).first()
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    db.delete(gateway)
    db.commit()
    return None


# ========== IGAMEWIN AGENTS ==========
@router.get("/igamewin-agents", response_model=List[IGameWinAgentResponse])
async def get_igamewin_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar todos os agentes IGameWin"""
    try:
        agents = db.query(IGameWinAgent).all()
        # Garantir que todos os agentes tenham RTP (caso campo não exista ainda no banco)
        for agent in agents:
            if not hasattr(agent, 'rtp') or agent.rtp is None:
                agent.rtp = 96.0
        return agents
    except Exception as e:
        print(f"[IGAMEWIN] Erro ao listar agentes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar agentes: {str(e)}")


@router.get("/igamewin-agents/{agent_id}", response_model=IGameWinAgentResponse)
async def get_igamewin_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    agent = db.query(IGameWinAgent).filter(IGameWinAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="IGameWin agent not found")
    return agent


@router.post("/igamewin-agents", response_model=IGameWinAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_igamewin_agent(
    agent_data: IGameWinAgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    existing = db.query(IGameWinAgent).filter(IGameWinAgent.agent_code == agent_data.agent_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Agent code already exists")
    
    agent = IGameWinAgent(**agent_data.model_dump())
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.put("/igamewin-agents/{agent_id}", response_model=IGameWinAgentResponse)
async def update_igamewin_agent(
    agent_id: int,
    agent_data: IGameWinAgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    agent = db.query(IGameWinAgent).filter(IGameWinAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="IGameWin agent not found")
    
    # Guardar RTP anterior para comparar (com fallback caso campo não exista ainda)
    try:
        old_rtp = getattr(agent, 'rtp', 96.0)
    except AttributeError:
        old_rtp = 96.0
    
    update_data = agent_data.model_dump(exclude_unset=True)
    
    # Se RTP está sendo atualizado, sincronizar com IGameWin
    if "rtp" in update_data:
        new_rtp = update_data["rtp"]
        # Só sincronizar se o valor realmente mudou
        if new_rtp != old_rtp:
            api = get_igamewin_api(db)
            if api:
                print(f"[IGAMEWIN] Atualizando RTP de {old_rtp}% para {new_rtp}% na IGameWin...")
                try:
                    rtp_result = await api.update_rtp(new_rtp)
                    if rtp_result:
                        print(f"[IGAMEWIN] ✅ RTP atualizado com sucesso na IGameWin: {rtp_result}")
                    else:
                        print(f"[IGAMEWIN] ⚠️ Aviso: Não foi possível atualizar RTP na IGameWin: {api.last_error}")
                        # Continuar mesmo assim - o RTP será salvo localmente
                except Exception as e:
                    print(f"[IGAMEWIN] ⚠️ Erro ao tentar atualizar RTP na IGameWin: {str(e)}")
                    # Continuar mesmo assim - o RTP será salvo localmente
            else:
                print(f"[IGAMEWIN] ⚠️ Aviso: Não foi possível obter instância da API IGameWin para atualizar RTP")
    
    # Atualizar campos no banco de dados
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    db.commit()
    db.refresh(agent)
    return agent


@router.delete("/igamewin-agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_igamewin_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    agent = db.query(IGameWinAgent).filter(IGameWinAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="IGameWin agent not found")
    db.delete(agent)
    db.commit()
    return None


# ========== IGAMEWIN GAMES ==========
def _choose_provider(providers: list, provider_code: Optional[str]) -> Optional[str]:
    chosen = provider_code
    if not chosen:
        active = [p for p in providers if str(p.get("status", 1)) in ["1", "true", "True"]]
        if active:
            chosen = active[0].get("code") or active[0].get("provider_code")
        elif providers:
            chosen = providers[0].get("code") or providers[0].get("provider_code")
    return chosen


def _normalize_games(games: list, chosen_provider: Optional[str]) -> list:
    if chosen_provider:
        for g in games:
            if not g.get("provider_code"):
                g["provider_code"] = chosen_provider
    return games


@router.get("/igamewin/agent-balance")
async def get_igamewin_agent_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get IGameWin agent balance - Cannot deposit via API, must use IGameWin admin"""
    api = get_igamewin_api(db)
    if not api:
        raise HTTPException(status_code=400, detail="Nenhum agente IGameWin ativo configurado")

    balance = await api.get_agent_balance()
    if balance is None:
        raise HTTPException(
            status_code=502,
            detail=f"Não foi possível obter saldo do agente da IGameWin ({api.last_error or 'erro desconhecido'})"
        )

    return {
        "agent_code": api.agent_code,
        "balance": balance,
        "note": "Para adicionar saldo ao agente, utilize o painel administrativo da IGameWin. Esta API permite apenas consultar o saldo."
    }


@router.get("/igamewin/games")
async def list_igamewin_games(
    provider_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar jogos e provedores do IGameWin"""
    try:
        api = get_igamewin_api(db)
        if not api:
            raise HTTPException(status_code=400, detail="Nenhum agente IGameWin ativo configurado")

        providers = await api.get_providers()
        if providers is None:
            raise HTTPException(
                status_code=502,
                detail=f"Não foi possível obter provedores da IGameWin ({api.last_error or 'erro desconhecido'})"
            )

        chosen_provider = _choose_provider(providers, provider_code)

        games = await api.get_games(provider_code=chosen_provider)
        if games is None:
            raise HTTPException(
                status_code=502,
                detail=f"Não foi possível obter jogos da IGameWin (verifique provider_code e credenciais do agente). {api.last_error or ''}".strip()
            )

        games = _normalize_games(games, chosen_provider)

        return {
            "providers": providers,
            "provider_code": chosen_provider,
            "games": games
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[IGAMEWIN] Erro ao listar jogos: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno ao listar jogos: {str(e)}")


@public_router.get("/games")
async def public_games(
    provider_code: Optional[str] = Query(None),
    section: Optional[str] = Query("home", description="Seção: home, featured"),
    db: Session = Depends(get_db)
):
    """
    Retorna lista de jogos públicos.
    Cache recomendado: 5 minutos (300 segundos)
    """
    api = get_igamewin_api(db)
    if not api:
        raise HTTPException(status_code=400, detail="Nenhum agente IGameWin ativo configurado")

    providers = await api.get_providers()
    if providers is None:
        raise HTTPException(
            status_code=502,
            detail=f"Não foi possível obter provedores da IGameWin ({api.last_error or 'erro desconhecido'})"
        )

    # Se provider_code específico foi solicitado, retorna jogos apenas desse provedor
    if provider_code:
        chosen_provider = _choose_provider(providers, provider_code)
        games = await api.get_games(provider_code=chosen_provider)
        if games is None:
            raise HTTPException(
                status_code=502,
                detail=f"Não foi possível obter jogos da IGameWin. {api.last_error or ''}".strip()
            )
        games = _normalize_games(games, chosen_provider)
        
        layouts = db.query(GameLayout).filter(
            GameLayout.section == section,
            GameLayout.is_active == True
        ).order_by(GameLayout.position).all()
        layout_map = {layout.game_code: layout for layout in layouts}
        
        public_games = []
        for g in games:
            status_val = g.get("status")
            is_active = (status_val == 1) or (status_val is True) or (str(status_val).lower() == "active")
            if not is_active:
                continue
            
            game_code = g.get("game_code") or g.get("code") or g.get("game_id") or g.get("id") or g.get("slug")
            layout = layout_map.get(game_code)
            position = layout.position if layout else 999999
            is_featured = layout.is_featured if layout else False
            
            public_games.append({
                "name": g.get("game_name") or g.get("name") or g.get("title") or g.get("gameTitle"),
                "code": game_code,
                "provider": chosen_provider,
                "banner": g.get("banner") or g.get("image") or g.get("icon"),
                "status": "active",
                "position": position,
                "is_featured": is_featured
            })
        
        public_games.sort(key=lambda x: x["position"])
        if section == "featured":
            public_games = [g for g in public_games if g["is_featured"]]
        
        # Limitar a 15 jogos por provedor
        public_games = public_games[:15]
        
        return {
            "providers": providers,
            "provider_code": chosen_provider,
            "games": public_games,
            "games_by_provider": {}  # Retorna vazio quando filtrado por provedor
        }
    
    # Caso contrário, retorna jogos organizados por provedor conforme configuração admin
    # Primeiro verificar se há configuração de provedores IGameWin (até 3)
    igamewin_provider_configs = db.query(IGameWinProviderConfig).filter(
        IGameWinProviderConfig.is_active == True
    ).order_by(IGameWinProviderConfig.position).all()
    
    # Se há configuração de provedores IGameWin, usar ela; senão usar ProviderLayout
    if igamewin_provider_configs:
        # Usar apenas os provedores configurados do IGameWin
        provider_codes = [config.provider_code for config in igamewin_provider_configs]
        # Buscar jogos apenas dos provedores configurados
        all_games = []
        for config in igamewin_provider_configs:
            games = await api.get_games(provider_code=config.provider_code)
            if games:
                games = _normalize_games(games, config.provider_code)
                for g in games:
                    status_val = g.get("status")
                    is_active = (status_val == 1) or (status_val is True) or (str(status_val).lower() == "active")
                    if not is_active:
                        continue
                    
                    game_code = g.get("game_code") or g.get("code") or g.get("game_id") or g.get("id") or g.get("slug")
                    all_games.append({
                        "name": g.get("game_name") or g.get("name") or g.get("title") or g.get("gameTitle"),
                        "code": game_code,
                        "provider": config.provider_code,
                        "banner": g.get("banner") or g.get("image") or g.get("icon"),
                        "status": "active"
                    })
        
        # Organizar jogos por provedor conforme configuração IGameWin
        games_by_provider = {}
        for config in igamewin_provider_configs:
            provider_games = [g for g in all_games if g["provider"] == config.provider_code]
            
            # Ordenar jogos dentro do provedor (usar layout se disponível)
            layouts = db.query(GameLayout).filter(
                GameLayout.section == section,
                GameLayout.is_active == True
            ).order_by(GameLayout.position).all()
            layout_map = {layout.game_code: layout for layout in layouts}
            
            for g in provider_games:
                layout = layout_map.get(g["code"])
                g["position"] = layout.position if layout else 999999
                g["is_featured"] = layout.is_featured if layout else False
            
            provider_games.sort(key=lambda x: x["position"])
            
            # Filtrar destaques se solicitado
            if section == "featured":
                provider_games = [g for g in provider_games if g.get("is_featured", False)]
            
            # Limitar a 15 jogos por provedor
            provider_games = provider_games[:15]
            
            if provider_games:
                games_by_provider[config.provider_code] = {
                    "provider_name": config.provider_name,
                    "position": config.position,
                    "games": provider_games
                }
        
        # Ordenar provedores por posição
        sorted_providers = sorted(games_by_provider.items(), key=lambda x: x[1]["position"])
        games_by_provider = {k: v for k, v in sorted_providers}
        
        # Retornar todos os jogos em uma lista também (para compatibilidade)
        all_public_games = []
        for provider_data in games_by_provider.values():
            all_public_games.extend(provider_data["games"])
        
        return {
            "providers": providers,
            "provider_code": None,
            "games": all_public_games,  # Lista plana para compatibilidade
            "games_by_provider": games_by_provider  # Organizado por provedor
        }
    
    # Se não há configuração IGameWin, usar ProviderLayout (comportamento anterior)
    provider_layouts = db.query(ProviderLayout).filter(
        ProviderLayout.section == section,
        ProviderLayout.is_active == True
    ).order_by(ProviderLayout.position).all()
    
    # Obter configurações de layout de jogos individuais
    layouts = db.query(GameLayout).filter(
        GameLayout.section == section,
        GameLayout.is_active == True
    ).order_by(GameLayout.position).all()
    layout_map = {layout.game_code: layout for layout in layouts}
    
    # Se há configuração de provedores, usar ela
    if provider_layouts:
        # Buscar jogos de cada provedor configurado
        all_games = []
        for pl in provider_layouts:
            games = await api.get_games(provider_code=pl.provider_code)
            if games:
                games = _normalize_games(games, pl.provider_code)
                for g in games:
                    status_val = g.get("status")
                    is_active = (status_val == 1) or (status_val is True) or (str(status_val).lower() == "active")
                    if not is_active:
                        continue
                    
                    game_code = g.get("game_code") or g.get("code") or g.get("game_id") or g.get("id") or g.get("slug")
                    all_games.append({
                        "name": g.get("game_name") or g.get("name") or g.get("title") or g.get("gameTitle"),
                        "code": game_code,
                        "provider": pl.provider_code,
                        "banner": g.get("banner") or g.get("image") or g.get("icon"),
                        "status": "active"
                    })
        
        # Organizar jogos por provedor conforme configuração
        games_by_provider = {}
        for pl in provider_layouts:
            provider_games = [g for g in all_games if g["provider"] == pl.provider_code]
            
            # Ordenar jogos dentro do provedor (usar layout se disponível)
            for g in provider_games:
                layout = layout_map.get(g["code"])
                g["position"] = layout.position if layout else 999999
                g["is_featured"] = layout.is_featured if layout else False
            
            provider_games.sort(key=lambda x: x["position"])
            
            # Limitar quantidade de jogos conforme configuração (máximo 15)
            max_games = min(pl.max_games, 15) if pl.max_games > 0 else 15
            provider_games = provider_games[:max_games]
            
            # Filtrar destaques se solicitado
            if section == "featured":
                provider_games = [g for g in provider_games if g.get("is_featured", False)]
            
            if provider_games:
                games_by_provider[pl.provider_code] = {
                    "provider_name": pl.provider_name,
                    "position": pl.position,
                    "games": provider_games
                }
        
        # Ordenar provedores por posição
        sorted_providers = sorted(games_by_provider.items(), key=lambda x: x[1]["position"])
        games_by_provider = {k: v for k, v in sorted_providers}
        
        # Retornar todos os jogos em uma lista também (para compatibilidade)
        all_public_games = []
        for provider_data in games_by_provider.values():
            all_public_games.extend(provider_data["games"])
        
        return {
            "providers": providers,
            "provider_code": None,
            "games": all_public_games,  # Lista plana para compatibilidade
            "games_by_provider": games_by_provider  # Organizado por provedor
        }
    else:
        # Se não há configuração, retornar todos os provedores disponíveis (comportamento antigo)
        # Usar primeiro provedor disponível
        chosen_provider = _choose_provider(providers, None)
        games = await api.get_games(provider_code=chosen_provider)
        if games is None:
            raise HTTPException(
                status_code=502,
                detail=f"Não foi possível obter jogos da IGameWin. {api.last_error or ''}".strip()
            )
        games = _normalize_games(games, chosen_provider)
        
        public_games = []
        for g in games:
            status_val = g.get("status")
            is_active = (status_val == 1) or (status_val is True) or (str(status_val).lower() == "active")
            if not is_active:
                continue
            
            game_code = g.get("game_code") or g.get("code") or g.get("game_id") or g.get("id") or g.get("slug")
            layout = layout_map.get(game_code)
            position = layout.position if layout else 999999
            is_featured = layout.is_featured if layout else False
            
            public_games.append({
                "name": g.get("game_name") or g.get("name") or g.get("title") or g.get("gameTitle"),
                "code": game_code,
                "provider": chosen_provider,
                "banner": g.get("banner") or g.get("image") or g.get("icon"),
                "status": "active",
                "position": position,
                "is_featured": is_featured
            })
        
        public_games.sort(key=lambda x: x["position"])
        if section == "featured":
            public_games = [g for g in public_games if g["is_featured"]]
        
        # Limitar a 15 jogos por provedor
        public_games = public_games[:15]
        
        return {
            "providers": providers,
            "provider_code": chosen_provider,
            "games": public_games,
            "games_by_provider": {}  # Retorna vazio quando não há configuração
        }


@public_router.get("/games/{game_code}/launch")
async def launch_game(
    game_code: str,
    provider_code: Optional[str] = Query(None),
    lang: str = Query("pt", description="Language code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Launch a game - Modo Seamless
    
    No modo Seamless:
    - Não transfere saldo para IGameWin
    - O saldo é gerenciado localmente via API /gold_api
    - Apenas gera URL de lançamento do jogo
    - Requer que o usuário tenha saldo > 0
    """
    # Verificar se usuário tem saldo
    if not current_user.balance or current_user.balance <= 0:
        raise HTTPException(
            status_code=400,
            detail="Você precisa ter saldo para jogar. Faça um depósito primeiro."
        )
    
    api = get_igamewin_api(db)
    if not api:
        raise HTTPException(status_code=400, detail="Nenhum agente IGameWin ativo configurado")
    
    # Criar usuário no IGameWin se não existir (necessário para seamless)
    user_create_result = await api.create_user(user_code=current_user.username, is_demo=False)
    if not user_create_result:
        print(f"[LAUNCH] Aviso: Não foi possível criar/verificar usuário no IGameWin: {api.last_error}")
        # Continuar mesmo assim, pode ser que o usuário já exista
    
    # Se provider_code não foi fornecido, buscar na lista de jogos
    if not provider_code:
        providers = await api.get_providers()
        if providers is None:
            raise HTTPException(
                status_code=502,
                detail=f"Não foi possível obter provedores da IGameWin ({api.last_error or 'erro desconhecido'})"
            )
        
        # Tentar encontrar o jogo em cada provider
        found_provider = None
        for provider in providers:
            provider_code_to_try = provider.get("code") or provider.get("provider_code")
            if not provider_code_to_try:
                continue
            
            games = await api.get_games(provider_code=provider_code_to_try)
            if games:
                for game in games:
                    game_code_from_api = game.get("game_code") or game.get("code") or game.get("game_id") or game.get("id")
                    if game_code_from_api == game_code:
                        found_provider = provider_code_to_try
                        break
                if found_provider:
                    break
        
        if found_provider:
            provider_code = found_provider
        else:
            # Se não encontrou, usar o primeiro provider ativo como fallback
            active_providers = [p for p in providers if str(p.get("status", 1)) in ["1", "true", "True"]]
            if active_providers:
                provider_code = active_providers[0].get("code") or active_providers[0].get("provider_code")
            elif providers:
                provider_code = providers[0].get("code") or providers[0].get("provider_code")
    
    # Se ainda não tem provider_code, retornar erro
    if not provider_code:
        raise HTTPException(
            status_code=400,
            detail="provider_code é obrigatório. Não foi possível determinar o provider do jogo."
        )
    
    # Gerar URL de lançamento do jogo usando user_code (username)
    # No modo seamless, não transferimos saldo - o saldo é gerenciado via /gold_api
    launch_url = await api.launch_game(
        user_code=current_user.username,
        game_code=game_code,
        provider_code=provider_code,
        lang=lang
    )
    
    if not launch_url:
        raise HTTPException(
            status_code=502,
            detail=f"Não foi possível iniciar o jogo. {api.last_error or 'Erro desconhecido'}"
        )
    
    return {
        "game_url": launch_url,
        "launch_url": launch_url,  # Mantém compatibilidade
        "game_code": game_code,
        "provider_code": provider_code,
        "username": current_user.username,
        "user_code": current_user.username,
        "mode": "seamless"  # Indica que está usando modo seamless
    }


# ========== SEAMLESS API (IGameWin) ==========
# Endpoint sem prefixo para IGameWin chamar diretamente /gold_api
@seamless_router.post("/gold_api")
async def seamless_api(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    API Seamless para IGameWin - Modo Seamless Completo
    Endpoints suportados:
    - user_balance: Retornar saldo do usuário
    - transaction: Processar transação (debit/credit/debit_credit)
    
    Tipos de jogos suportados:
    - slot: Slots
    - live: Jogos ao vivo (casino, baccarat, etc)
    - sport: Apostas esportivas
    - lottery: Loterias
    """
    import json as json_module
    print(f"[SEAMLESS] ========== REQUEST RECEBIDO ==========")
    print(f"[SEAMLESS] Request data: {json_module.dumps(request, indent=2)}")
    
    method = request.get("method")
    agent_code = request.get("agent_code")
    agent_secret = request.get("agent_secret")
    user_code = request.get("user_code")
    
    print(f"[SEAMLESS] Method: {method}, Agent Code: {agent_code}, User Code: {user_code}")
    
    if not method or not agent_code or not agent_secret or not user_code:
        print(f"[SEAMLESS] ❌ Parâmetros inválidos")
        return {"status": 0, "msg": "INVALID_PARAMETER"}
    
    # Verificar credenciais do agente
    agent = db.query(IGameWinAgent).filter(
        IGameWinAgent.agent_code == agent_code,
        IGameWinAgent.is_active == True
    ).first()
    
    if not agent:
        return {"status": 0, "msg": "INVALID_AGENT"}
    
    # Verificar agent_secret
    if agent_secret != agent.agent_key:
        if agent.credentials:
            try:
                creds = json.loads(agent.credentials)
                if creds.get("agent_secret") != agent_secret:
                    return {"status": 0, "msg": "INVALID_AGENT_SECRET"}
            except:
                if agent_secret != agent.agent_key:
                    return {"status": 0, "msg": "INVALID_AGENT_SECRET"}
        else:
            return {"status": 0, "msg": "INVALID_AGENT_SECRET"}
    
    # Buscar usuário
    user = db.query(User).filter(User.username == user_code).first()
    if not user:
        return {"status": 0, "user_balance": 0, "msg": "INVALID_USER"}
    
    # Método: user_balance
    if method == "user_balance":
        print(f"[SEAMLESS] ✅ Retornando saldo do usuário: {user.balance}")
        return {
            "status": 1,
            "user_balance": float(user.balance)
        }
    
    # Método: transaction
    if method == "transaction":
        game_type = request.get("game_type", "slot")
        
        # Processar diferentes tipos de jogos
        if game_type == "slot":
            return await _process_slot_transaction(request, user, db)
        elif game_type == "live":
            return await _process_live_transaction(request, user, db)
        elif game_type == "sport":
            return await _process_sport_transaction(request, user, db)
        elif game_type == "lottery":
            return await _process_lottery_transaction(request, user, db)
        else:
            return {"status": 0, "msg": f"UNSUPPORTED_GAME_TYPE: {game_type}"}
    
    return {"status": 0, "msg": "INVALID_METHOD"}


async def _process_slot_transaction(request: dict, user: User, db: Session):
    """Processar transação de slot"""
    slot_data = request.get("slot", {})
    provider_code = slot_data.get("provider_code")
    game_code = slot_data.get("game_code")
    txn_type = slot_data.get("txn_type")  # debit, credit, debit_credit
    bet_money = float(slot_data.get("bet_money", 0))
    win_money = float(slot_data.get("win_money", 0))
    txn_id = slot_data.get("txn_id")
    
    if not txn_id:
        return {"status": 0, "msg": "INVALID_PARAMETER"}
    
    # Converter txn_id para string para garantir compatibilidade
    txn_id = str(txn_id)
    
    # Verificar se transação já foi processada (idempotência)
    existing_bet = db.query(Bet).filter(Bet.transaction_id == txn_id).first()
    if existing_bet:
        return {
            "status": 1,
            "user_balance": float(user.balance)
        }
    
    try:
        bet_money_actual = bet_money
        win_amount = 0
        
        if txn_type == "debit":
            # Apenas aposta (debit)
            if user.balance < bet_money:
                return {"status": 0, "user_balance": float(user.balance), "msg": "INSUFFICIENT_USER_FUNDS"}
            user.balance -= bet_money
            win_amount = 0
            
        elif txn_type == "credit":
            # Apenas ganho (credit)
            user.balance += win_money
            bet_money_actual = 0
            win_amount = win_money
            
        elif txn_type == "debit_credit":
            # Aposta e ganho (debit_credit)
            if user.balance < bet_money:
                return {"status": 0, "user_balance": float(user.balance), "msg": "INSUFFICIENT_USER_FUNDS"}
            user.balance -= bet_money
            user.balance += win_money
            win_amount = win_money
            
        else:
            return {"status": 0, "msg": "INVALID_TXN_TYPE"}
        
        # Criar registro de aposta
        bet = Bet(
            user_id=user.id,
            game_id=game_code,
            game_name=game_code,
            provider=provider_code or "IGameWin",
            amount=bet_money_actual,
            win_amount=win_amount,
            status=BetStatus.WON if win_amount > 0 else BetStatus.LOST,
            transaction_id=txn_id,
            external_id=txn_id,
            metadata_json=json.dumps(slot_data)
        )
        db.add(bet)
        db.commit()
        db.refresh(user)
        
        return {
            "status": 1,
            "user_balance": float(user.balance)
        }
        
    except Exception as e:
        db.rollback()
        print(f"[SEAMLESS] Erro ao processar transação slot: {str(e)}")
        return {"status": 0, "msg": f"INTERNAL_ERROR: {str(e)}"}


async def _process_live_transaction(request: dict, user: User, db: Session):
    """Processar transação de jogo ao vivo (casino, baccarat, etc)"""
    live_data = request.get("live", {})
    provider_code = live_data.get("provider_code")
    game_code = live_data.get("game_code")
    txn_type = live_data.get("txn_type")
    bet_money = float(live_data.get("bet_money", 0))
    win_money = float(live_data.get("win_money", 0))
    txn_id = live_data.get("txn_id")
    
    if not txn_id:
        return {"status": 0, "msg": "INVALID_PARAMETER"}
    
    # Converter txn_id para string para garantir compatibilidade
    txn_id = str(txn_id)
    
    # Verificar se transação já foi processada
    existing_bet = db.query(Bet).filter(Bet.transaction_id == txn_id).first()
    if existing_bet:
        return {
            "status": 1,
            "user_balance": float(user.balance)
        }
    
    try:
        bet_money_actual = bet_money
        win_amount = 0
        
        if txn_type == "debit":
            if user.balance < bet_money:
                return {"status": 0, "user_balance": float(user.balance), "msg": "INSUFFICIENT_USER_FUNDS"}
            user.balance -= bet_money
            win_amount = 0
            
        elif txn_type == "credit":
            user.balance += win_money
            bet_money_actual = 0
            win_amount = win_money
            
        elif txn_type == "debit_credit":
            if user.balance < bet_money:
                return {"status": 0, "user_balance": float(user.balance), "msg": "INSUFFICIENT_USER_FUNDS"}
            user.balance -= bet_money
            user.balance += win_money
            win_amount = win_money
            
        else:
            return {"status": 0, "msg": "INVALID_TXN_TYPE"}
        
        bet = Bet(
            user_id=user.id,
            game_id=game_code,
            game_name=game_code,
            provider=provider_code or "IGameWin",
            amount=bet_money_actual,
            win_amount=win_amount,
            status=BetStatus.WON if win_amount > 0 else BetStatus.LOST,
            transaction_id=txn_id,
            external_id=txn_id,
            metadata_json=json.dumps(live_data)
        )
        db.add(bet)
        db.commit()
        db.refresh(user)
        
        return {
            "status": 1,
            "user_balance": float(user.balance)
        }
        
    except Exception as e:
        db.rollback()
        print(f"[SEAMLESS] Erro ao processar transação live: {str(e)}")
        return {"status": 0, "msg": f"INTERNAL_ERROR: {str(e)}"}


async def _process_sport_transaction(request: dict, user: User, db: Session):
    """Processar transação de aposta esportiva"""
    sport_data = request.get("sport", {})
    provider_code = sport_data.get("provider_code")
    game_code = sport_data.get("game_code") or sport_data.get("match_id")
    txn_type = sport_data.get("txn_type")
    bet_money = float(sport_data.get("bet_money", 0))
    win_money = float(sport_data.get("win_money", 0))
    txn_id = sport_data.get("txn_id")
    
    if not txn_id:
        return {"status": 0, "msg": "INVALID_PARAMETER"}
    
    # Converter txn_id para string para garantir compatibilidade
    txn_id = str(txn_id)
    
    existing_bet = db.query(Bet).filter(Bet.transaction_id == txn_id).first()
    if existing_bet:
        return {
            "status": 1,
            "user_balance": float(user.balance)
        }
    
    try:
        bet_money_actual = bet_money
        win_amount = 0
        
        if txn_type == "debit":
            if user.balance < bet_money:
                return {"status": 0, "user_balance": float(user.balance), "msg": "INSUFFICIENT_USER_FUNDS"}
            user.balance -= bet_money
            win_amount = 0
            
        elif txn_type == "credit":
            user.balance += win_money
            bet_money_actual = 0
            win_amount = win_money
            
        elif txn_type == "debit_credit":
            if user.balance < bet_money:
                return {"status": 0, "user_balance": float(user.balance), "msg": "INSUFFICIENT_USER_FUNDS"}
            user.balance -= bet_money
            user.balance += win_money
            win_amount = win_money
            
        else:
            return {"status": 0, "msg": "INVALID_TXN_TYPE"}
        
        bet = Bet(
            user_id=user.id,
            game_id=game_code,
            game_name=game_code,
            provider=provider_code or "IGameWin",
            amount=bet_money_actual,
            win_amount=win_amount,
            status=BetStatus.WON if win_amount > 0 else BetStatus.LOST,
            transaction_id=txn_id,
            external_id=txn_id,
            metadata_json=json.dumps(sport_data)
        )
        db.add(bet)
        db.commit()
        db.refresh(user)
        
        return {
            "status": 1,
            "user_balance": float(user.balance)
        }
        
    except Exception as e:
        db.rollback()
        print(f"[SEAMLESS] Erro ao processar transação sport: {str(e)}")
        return {"status": 0, "msg": f"INTERNAL_ERROR: {str(e)}"}


async def _process_lottery_transaction(request: dict, user: User, db: Session):
    """Processar transação de loteria"""
    lottery_data = request.get("lottery", {})
    provider_code = lottery_data.get("provider_code")
    game_code = lottery_data.get("game_code")
    txn_type = lottery_data.get("txn_type")
    bet_money = float(lottery_data.get("bet_money", 0))
    win_money = float(lottery_data.get("win_money", 0))
    txn_id = lottery_data.get("txn_id")
    
    if not txn_id:
        return {"status": 0, "msg": "INVALID_PARAMETER"}
    
    # Converter txn_id para string para garantir compatibilidade
    txn_id = str(txn_id)
    
    existing_bet = db.query(Bet).filter(Bet.transaction_id == txn_id).first()
    if existing_bet:
        return {
            "status": 1,
            "user_balance": float(user.balance)
        }
    
    try:
        bet_money_actual = bet_money
        win_amount = 0
        
        if txn_type == "debit":
            if user.balance < bet_money:
                return {"status": 0, "user_balance": float(user.balance), "msg": "INSUFFICIENT_USER_FUNDS"}
            user.balance -= bet_money
            win_amount = 0
            
        elif txn_type == "credit":
            user.balance += win_money
            bet_money_actual = 0
            win_amount = win_money
            
        elif txn_type == "debit_credit":
            if user.balance < bet_money:
                return {"status": 0, "user_balance": float(user.balance), "msg": "INSUFFICIENT_USER_FUNDS"}
            user.balance -= bet_money
            user.balance += win_money
            win_amount = win_money
            
        else:
            return {"status": 0, "msg": "INVALID_TXN_TYPE"}
        
        bet = Bet(
            user_id=user.id,
            game_id=game_code,
            game_name=game_code,
            provider=provider_code or "IGameWin",
            amount=bet_money_actual,
            win_amount=win_amount,
            status=BetStatus.WON if win_amount > 0 else BetStatus.LOST,
            transaction_id=txn_id,
            external_id=txn_id,
            metadata_json=json.dumps(lottery_data)
        )
        db.add(bet)
        db.commit()
        db.refresh(user)
        
        return {
            "status": 1,
            "user_balance": float(user.balance)
        }
        
    except Exception as e:
        db.rollback()
        print(f"[SEAMLESS] Erro ao processar transação lottery: {str(e)}")
        return {"status": 0, "msg": f"INTERNAL_ERROR: {str(e)}"}


# ========== STATS ==========
@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    from datetime import date, timedelta
    
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    
    # Total de usuários
    total_users = db.query(User).count()
    
    # Usuários registrados hoje
    usuarios_registrados_hoje = db.query(User).filter(
        func.date(User.created_at) == today
    ).count()
    
    # Balanço total dos jogadores com saldo
    users_with_balance = db.query(User).filter(User.balance > 0).all()
    balanco_jogador_total = sum(u.balance for u in users_with_balance)
    jogadores_com_saldo = len(users_with_balance)
    
    # Depósitos
    total_deposits = db.query(Deposit).filter(Deposit.status == TransactionStatus.APPROVED).count()
    total_deposit_amount = db.query(Deposit).filter(Deposit.status == TransactionStatus.APPROVED).with_entities(
        func.sum(Deposit.amount)
    ).scalar() or 0.0
    pending_deposits = db.query(Deposit).filter(Deposit.status == TransactionStatus.PENDING).count()
    
    # Depósitos recebidos (aprovados) hoje
    pagamentos_recebidos_hoje = db.query(Deposit).filter(
        Deposit.status == TransactionStatus.APPROVED,
        func.date(Deposit.created_at) == today
    ).count()
    valor_pagamentos_recebidos_hoje = db.query(Deposit).filter(
        Deposit.status == TransactionStatus.APPROVED,
        func.date(Deposit.created_at) == today
    ).with_entities(func.sum(Deposit.amount)).scalar() or 0.0
    
    # PIX recebido hoje (depósitos PIX aprovados hoje)
    pix_recebido_hoje = db.query(Deposit).join(Gateway).filter(
        Deposit.status == TransactionStatus.APPROVED,
        Gateway.type == "pix",
        func.date(Deposit.created_at) == today
    ).with_entities(func.sum(Deposit.amount)).scalar() or 0.0
    pix_recebido_count_hoje = db.query(Deposit).join(Gateway).filter(
        Deposit.status == TransactionStatus.APPROVED,
        Gateway.type == "pix",
        func.date(Deposit.created_at) == today
    ).count()
    
    # Saques
    total_withdrawals = db.query(Withdrawal).filter(Withdrawal.status == TransactionStatus.APPROVED).count()
    total_withdrawal_amount = db.query(Withdrawal).filter(Withdrawal.status == TransactionStatus.APPROVED).with_entities(
        func.sum(Withdrawal.amount)
    ).scalar() or 0.0
    pending_withdrawals = db.query(Withdrawal).filter(Withdrawal.status == TransactionStatus.PENDING).count()
    
    # Pagamentos feitos (saques aprovados) hoje
    pagamentos_feitos_hoje = db.query(Withdrawal).filter(
        Withdrawal.status == TransactionStatus.APPROVED,
        func.date(Withdrawal.created_at) == today
    ).count()
    valor_pagamentos_feitos_hoje = db.query(Withdrawal).filter(
        Withdrawal.status == TransactionStatus.APPROVED,
        func.date(Withdrawal.created_at) == today
    ).with_entities(func.sum(Withdrawal.amount)).scalar() or 0.0
    
    # PIX feito hoje (saques PIX aprovados hoje)
    pix_feito_hoje = db.query(Withdrawal).join(Gateway).filter(
        Withdrawal.status == TransactionStatus.APPROVED,
        Gateway.type == "pix",
        func.date(Withdrawal.created_at) == today
    ).with_entities(func.sum(Withdrawal.amount)).scalar() or 0.0
    pix_feito_count_hoje = db.query(Withdrawal).join(Gateway).filter(
        Withdrawal.status == TransactionStatus.APPROVED,
        Gateway.type == "pix",
        func.date(Withdrawal.created_at) == today
    ).count()
    
    # PIX gerado hoje (pendentes ou aprovados)
    pix_gerado_hoje = db.query(Deposit).join(Gateway).filter(
        Gateway.type == "pix",
        func.date(Deposit.created_at) == today
    ).count()
    pix_gerado_pago_hoje = db.query(Deposit).join(Gateway).filter(
        Gateway.type == "pix",
        Deposit.status == TransactionStatus.APPROVED,
        func.date(Deposit.created_at) == today
    ).count()
    pix_percentual_pago = (pix_gerado_pago_hoje / pix_gerado_hoje * 100) if pix_gerado_hoje > 0 else 0
    
    # FTDs
    total_ftds = db.query(FTD).count()
    ftd_hoje = db.query(FTD).filter(func.date(FTD.created_at) == today).count()
    
    # GGR (Gross Gaming Revenue) - receita bruta de jogos
    # Simplificado: diferença entre depósitos e saques aprovados
    ggr_gerado = total_deposit_amount - total_withdrawal_amount
    ggr_taxa = 17.0  # Taxa padrão de 17% (pode ser configurável)
    
    # Total pago em GGR (assumindo que GGR pago = saques aprovados)
    total_pago_ggr = total_withdrawal_amount
    pagamentos_feitos_total = total_withdrawals
    
    # Receita líquida / Lucro total
    net_revenue = total_deposit_amount - total_withdrawal_amount
    
    # Depósitos hoje
    depositos_hoje = db.query(Deposit).filter(func.date(Deposit.created_at) == today).count()
    
    return {
        # Métricas básicas
        "total_users": total_users,
        "total_deposits": total_deposits,
        "total_withdrawals": total_withdrawals,
        "total_ftds": total_ftds,
        "total_deposit_amount": total_deposit_amount,
        "total_withdrawal_amount": total_withdrawal_amount,
        "pending_deposits": pending_deposits,
        "pending_withdrawals": pending_withdrawals,
        "net_revenue": net_revenue,
        
        # Métricas expandidas
        "usuarios_na_casa": total_users,
        "usuarios_registrados_hoje": usuarios_registrados_hoje,
        "balanco_jogador_total": balanco_jogador_total,
        "jogadores_com_saldo": jogadores_com_saldo,
        "ggr_gerado": ggr_gerado,
        "ggr_taxa": ggr_taxa,
        "total_pago_ggr": total_pago_ggr,
        "pix_recebido_hoje": pix_recebido_hoje,
        "pix_recebido_count_hoje": pix_recebido_count_hoje,
        "pix_feito_hoje": pix_feito_hoje,
        "pix_feito_count_hoje": pix_feito_count_hoje,
        "pix_gerado_hoje": pix_gerado_hoje,
        "pix_percentual_pago": pix_percentual_pago,
        "pagamentos_recebidos_hoje": pagamentos_recebidos_hoje,
        "valor_pagamentos_recebidos_hoje": valor_pagamentos_recebidos_hoje,
        "pagamentos_feitos_hoje": pagamentos_feitos_hoje,
        "valor_pagamentos_feitos_hoje": valor_pagamentos_feitos_hoje,
        "pagamentos_feitos_total": pagamentos_feitos_total,
        "ftd_hoje": ftd_hoje,
        "depositos_hoje": depositos_hoje,
        "total_lucro": net_revenue,
    }


# ========== GGR REPORT ==========
@router.get("/ggr/report")
async def get_ggr_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Relatório de GGR (Gross Gaming Revenue)"""
    from datetime import datetime, date
    
    # Parse dates or use defaults
    if start_date:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    else:
        start = datetime.combine(date.today(), datetime.min.time())
    
    if end_date:
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    else:
        end = datetime.utcnow()
    
    # Total de depósitos aprovados no período
    total_deposits = db.query(Deposit).filter(
        Deposit.status == TransactionStatus.APPROVED,
        Deposit.created_at >= start,
        Deposit.created_at <= end
    ).with_entities(func.sum(Deposit.amount)).scalar() or 0.0
    
    # Total de saques aprovados no período
    total_withdrawals = db.query(Withdrawal).filter(
        Withdrawal.status == TransactionStatus.APPROVED,
        Withdrawal.created_at >= start,
        Withdrawal.created_at <= end
    ).with_entities(func.sum(Withdrawal.amount)).scalar() or 0.0
    
    # Total de apostas no período
    total_bets = db.query(Bet).filter(
        Bet.created_at >= start,
        Bet.created_at <= end
    ).with_entities(func.sum(Bet.amount)).scalar() or 0.0
    
    # Total ganho em apostas
    total_wins = db.query(Bet).filter(
        Bet.status == BetStatus.WON,
        Bet.created_at >= start,
        Bet.created_at <= end
    ).with_entities(func.sum(Bet.win_amount)).scalar() or 0.0
    
    # GGR = Total Apostado - Total Ganho
    ggr = total_bets - total_wins
    
    # NGR (Net Gaming Revenue) = GGR - Bonuses (simplificado, pode incluir bônus depois)
    ngr = ggr
    
    return {
        "period": {
            "start": start.isoformat(),
            "end": end.isoformat()
        },
        "deposits": {
            "total": total_deposits,
            "count": db.query(Deposit).filter(
                Deposit.status == TransactionStatus.APPROVED,
                Deposit.created_at >= start,
                Deposit.created_at <= end
            ).count()
        },
        "withdrawals": {
            "total": total_withdrawals,
            "count": db.query(Withdrawal).filter(
                Withdrawal.status == TransactionStatus.APPROVED,
                Withdrawal.created_at >= start,
                Withdrawal.created_at <= end
            ).count()
        },
        "bets": {
            "total_amount": total_bets,
            "total_wins": total_wins,
            "count": db.query(Bet).filter(
                Bet.created_at >= start,
                Bet.created_at <= end
            ).count()
        },
        "ggr": ggr,
        "ngr": ngr,
        "ggr_rate": (ggr / total_bets * 100) if total_bets > 0 else 0.0,
    }


# ========== BETS ==========
@router.get("/bets")
async def get_bets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = None,
    status: Optional[BetStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar apostas"""
    query = db.query(Bet)
    
    if user_id:
        query = query.filter(Bet.user_id == user_id)
    if status:
        query = query.filter(Bet.status == status)
    
    bets = query.order_by(desc(Bet.created_at)).offset(skip).limit(limit).all()
    
    return [
        {
            "id": bet.id,
            "user_id": bet.user_id,
            "username": bet.user.username if bet.user else None,
            "game_id": bet.game_id,
            "game_name": bet.game_name,
            "provider": bet.provider,
            "amount": bet.amount,
            "win_amount": bet.win_amount,
            "status": bet.status.value,
            "transaction_id": bet.transaction_id,
            "created_at": bet.created_at.isoformat(),
        }
        for bet in bets
    ]


@router.get("/bets/{bet_id}")
async def get_bet(
    bet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Obter aposta específica"""
    bet = db.query(Bet).filter(Bet.id == bet_id).first()
    if not bet:
        raise HTTPException(status_code=404, detail="Aposta não encontrada")
    
    return {
        "id": bet.id,
        "user_id": bet.user_id,
        "username": bet.user.username if bet.user else None,
        "game_id": bet.game_id,
        "game_name": bet.game_name,
        "provider": bet.provider,
        "amount": bet.amount,
        "win_amount": bet.win_amount,
        "status": bet.status.value,
        "transaction_id": bet.transaction_id,
        "external_id": bet.external_id,
        "metadata": json.loads(bet.metadata_json) if bet.metadata_json else None,
        "created_at": bet.created_at.isoformat(),
        "updated_at": bet.updated_at.isoformat(),
    }


# ========== NOTIFICATIONS ==========
@router.get("/notifications")
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = None,
    is_read: Optional[bool] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar notificações"""
    query = db.query(Notification)
    
    if user_id:
        query = query.filter(Notification.user_id == user_id)
    else:
        # Admin vê apenas notificações globais (user_id = null)
        query = query.filter(Notification.user_id == None)
    
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    if is_active is not None:
        query = query.filter(Notification.is_active == is_active)
    
    notifications = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()
    
    return [
        {
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "type": notif.type.value,
            "user_id": notif.user_id,
            "username": notif.user.username if notif.user else None,
            "is_read": notif.is_read,
            "is_active": notif.is_active,
            "link": notif.link,
            "created_at": notif.created_at.isoformat(),
        }
        for notif in notifications
    ]


@router.post("/notifications")
async def create_notification(
    title: str,
    message: str,
    type: NotificationType = NotificationType.INFO,
    user_id: Optional[int] = None,
    link: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Criar notificação"""
    notification = Notification(
        title=title,
        message=message,
        type=type,
        user_id=user_id,  # null = notificação global
        link=link,
        is_active=True,
        is_read=False
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "type": notification.type.value,
        "user_id": notification.user_id,
        "is_read": notification.is_read,
        "is_active": notification.is_active,
        "link": notification.link,
        "created_at": notification.created_at.isoformat(),
    }


@router.put("/notifications/{notification_id}")
async def update_notification(
    notification_id: int,
    title: Optional[str] = None,
    message: Optional[str] = None,
    type: Optional[NotificationType] = None,
    is_active: Optional[bool] = None,
    link: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualizar notificação"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    
    if title is not None:
        notification.title = title
    if message is not None:
        notification.message = message
    if type is not None:
        notification.type = type
    if is_active is not None:
        notification.is_active = is_active
    if link is not None:
        notification.link = link
    
    db.commit()
    db.refresh(notification)
    
    return {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "type": notification.type.value,
        "is_active": notification.is_active,
        "link": notification.link,
    }


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deletar notificação"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    
    db.delete(notification)
    db.commit()
    
    return {"success": True, "message": "Notificação deletada com sucesso"}


# ========== COUPONS ==========
@router.get("/coupons", response_model=List[schemas.CouponResponse])
async def get_coupons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar cupons"""
    query = db.query(Coupon)
    
    if is_active is not None:
        query = query.filter(Coupon.is_active == is_active)
    
    coupons = query.order_by(desc(Coupon.created_at)).offset(skip).limit(limit).all()
    return coupons


@router.post("/coupons", response_model=schemas.CouponResponse, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    coupon_data: schemas.CouponCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Criar cupom"""
    # Verificar se código já existe
    existing = db.query(Coupon).filter(Coupon.code == coupon_data.code.upper().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Código de cupom já existe")
    
    coupon = Coupon(
        code=coupon_data.code.upper().strip(),
        type=coupon_data.type,
        value=coupon_data.value,
        max_uses=coupon_data.max_uses,
        valid_from=coupon_data.valid_from,
        valid_until=coupon_data.valid_until,
        min_deposit_amount=coupon_data.min_deposit_amount,
        max_bonus_amount=coupon_data.max_bonus_amount,
        is_active=coupon_data.is_active
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    
    # Criar notificação global sobre o novo cupom
    notification = Notification(
        title="🎁 Novo Cupom Disponível!",
        message=f"Cupom {coupon.code}: {coupon.value}{'%' if coupon.type == 'percentage' else ' reais'} de bônus! Use no seu próximo depósito.",
        type=NotificationType.PROMOTION,
        user_id=None,  # Notificação global
        link="/depositar",
        is_active=True,
        is_read=False,
        metadata_json=json.dumps({"coupon_code": coupon.code})
    )
    db.add(notification)
    db.commit()
    
    return coupon


@router.put("/coupons/{coupon_id}", response_model=schemas.CouponResponse)
async def update_coupon(
    coupon_id: int,
    coupon_data: schemas.CouponUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualizar cupom"""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Cupom não encontrado")
    
    update_data = coupon_data.model_dump(exclude_unset=True)
    
    # Se código está sendo atualizado, verificar duplicidade
    if "code" in update_data:
        code_upper = update_data["code"].upper().strip()
        existing = db.query(Coupon).filter(
            Coupon.code == code_upper,
            Coupon.id != coupon_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Código de cupom já existe")
        update_data["code"] = code_upper
    
    for field, value in update_data.items():
        setattr(coupon, field, value)
    
    db.commit()
    db.refresh(coupon)
    return coupon


@router.delete("/coupons/{coupon_id}")
async def delete_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deletar cupom"""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Cupom não encontrado")
    
    db.delete(coupon)
    db.commit()
    
    return {"success": True, "message": "Cupom deletado com sucesso"}


# ========== PROMOTIONS ==========
@router.get("/promotions", response_model=List[schemas.PromotionResponse])
async def get_promotions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar promoções"""
    query = db.query(Promotion)
    
    if is_active is not None:
        query = query.filter(Promotion.is_active == is_active)
    
    promotions = query.order_by(desc(Promotion.created_at)).offset(skip).limit(limit).all()
    return promotions


@router.post("/promotions", response_model=schemas.PromotionResponse, status_code=status.HTTP_201_CREATED)
async def create_promotion(
    promotion_data: schemas.PromotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Criar promoção"""
    promotion = Promotion(
        title=promotion_data.title,
        description=promotion_data.description,
        type=PromotionType(promotion_data.type),
        bonus_value=promotion_data.bonus_value,
        bonus_type=promotion_data.bonus_type,
        min_deposit_amount=promotion_data.min_deposit_amount,
        max_bonus_amount=promotion_data.max_bonus_amount,
        banner_url=promotion_data.banner_url,
        is_first_deposit_only=promotion_data.is_first_deposit_only,
        is_active=promotion_data.is_active,
        start_date=promotion_data.start_date,
        end_date=promotion_data.end_date
    )
    db.add(promotion)
    db.commit()
    db.refresh(promotion)
    
    # Criar notificação global sobre a nova promoção
    notification = Notification(
        title=f"🎁 {promotion.title}",
        message=promotion.description or f"Nova promoção disponível! {promotion.bonus_value}{'%' if promotion.bonus_type == 'percentage' else ' reais'} de bônus.",
        type=NotificationType.PROMOTION,
        user_id=None,  # Notificação global
        link="/depositar",
        is_active=True,
        is_read=False,
        metadata_json=json.dumps({"promotion_id": promotion.id})
    )
    db.add(notification)
    db.commit()
    
    return promotion


@router.put("/promotions/{promotion_id}", response_model=schemas.PromotionResponse)
async def update_promotion(
    promotion_id: int,
    promotion_data: schemas.PromotionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualizar promoção"""
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promoção não encontrada")
    
    update_data = promotion_data.model_dump(exclude_unset=True)
    
    if "type" in update_data:
        update_data["type"] = PromotionType(update_data["type"])
    
    for field, value in update_data.items():
        setattr(promotion, field, value)
    
    db.commit()
    db.refresh(promotion)
    return promotion


@router.delete("/promotions/{promotion_id}")
async def delete_promotion(
    promotion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deletar promoção"""
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promoção não encontrada")
    
    db.delete(promotion)
    db.commit()
    
    return {"success": True, "message": "Promoção deletada com sucesso"}


@router.post("/promotions/{promotion_id}/upload-banner")
async def upload_promotion_banner(
    promotion_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Upload de banner para promoção"""
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promoção não encontrada")
    
    # Validar tipo de arquivo
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Apenas imagens são permitidas")
    
    # Salvar arquivo
    import os
    import uuid
    from pathlib import Path
    
    upload_dir = Path("uploads/promotions")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_ext = Path(file.filename).suffix if file.filename else '.jpg'
    filename = f"{promotion_id}-{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = upload_dir / filename
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Atualizar URL do banner
    banner_url = f"/api/public/media/uploads/promotions/{filename}"
    promotion.banner_url = banner_url
    db.commit()
    db.refresh(promotion)
    
    return {"banner_url": banner_url, "promotion": schemas.PromotionResponse.model_validate(promotion)}


# ========== PUBLIC PROMOTIONS ==========
@public_router.get("/promotions")
async def get_public_promotions(
    db: Session = Depends(get_db)
):
    """Listar promoções ativas (público)"""
    from datetime import datetime
    now = datetime.utcnow()
    
    promotions = db.query(Promotion).filter(
        Promotion.is_active == True,
        Promotion.start_date <= now,
        Promotion.end_date >= now
    ).order_by(desc(Promotion.created_at)).all()
    
    return [
        {
            "id": promo.id,
            "title": promo.title,
            "description": promo.description,
            "type": promo.type.value,
            "bonus_value": promo.bonus_value,
            "bonus_type": promo.bonus_type,
            "banner_url": promo.banner_url,
            "is_first_deposit_only": promo.is_first_deposit_only,
            "min_deposit_amount": promo.min_deposit_amount,
            "max_bonus_amount": promo.max_bonus_amount,
            "start_date": promo.start_date.isoformat(),
            "end_date": promo.end_date.isoformat(),
        }
        for promo in promotions
    ]


# ========== GAME LAYOUT ==========
@router.get("/game-layouts", response_model=List[GameLayoutResponse])
async def get_game_layouts(
    section: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar configurações de layout dos jogos"""
    query = db.query(GameLayout)
    if section:
        query = query.filter(GameLayout.section == section)
    return query.order_by(GameLayout.position).all()


@router.post("/game-layouts", response_model=GameLayoutResponse, status_code=status.HTTP_201_CREATED)
async def create_game_layout(
    layout_data: GameLayoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Criar configuração de layout para um jogo"""
    # Verificar se já existe
    existing = db.query(GameLayout).filter(
        GameLayout.game_code == layout_data.game_code,
        GameLayout.section == layout_data.section
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Layout já existe para este jogo nesta seção")
    
    layout = GameLayout(**layout_data.model_dump())
    db.add(layout)
    db.commit()
    db.refresh(layout)
    return layout


@router.put("/game-layouts/{layout_id}", response_model=GameLayoutResponse)
async def update_game_layout(
    layout_id: int,
    layout_data: GameLayoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualizar configuração de layout"""
    layout = db.query(GameLayout).filter(GameLayout.id == layout_id).first()
    if not layout:
        raise HTTPException(status_code=404, detail="Layout não encontrado")
    
    update_data = layout_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(layout, field, value)
    
    db.commit()
    db.refresh(layout)
    return layout


@router.post("/game-layouts/reorder")
async def reorder_game_layouts(
    layout_ids: List[int],
    section: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Reordenar layouts (array de IDs na ordem desejada)"""
    query = db.query(GameLayout)
    if section:
        query = query.filter(GameLayout.section == section)
    layouts = query.all()
    
    # Atualizar posições
    for idx, layout_id in enumerate(layout_ids):
        layout = next((l for l in layouts if l.id == layout_id), None)
        if layout:
            layout.position = idx
    
    db.commit()
    return {"success": True, "message": "Ordem atualizada"}


@router.delete("/game-layouts/{layout_id}")
async def delete_game_layout(
    layout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deletar configuração de layout"""
    layout = db.query(GameLayout).filter(GameLayout.id == layout_id).first()
    if not layout:
        raise HTTPException(status_code=404, detail="Layout não encontrado")
    
    db.delete(layout)
    db.commit()
    return {"success": True, "message": "Layout deletado com sucesso"}


# ========== PROVIDER LAYOUT ==========
@router.get("/provider-layouts", response_model=List[ProviderLayoutResponse])
async def get_provider_layouts(
    section: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar configurações de layout dos provedores"""
    query = db.query(ProviderLayout)
    if section:
        query = query.filter(ProviderLayout.section == section)
    return query.order_by(ProviderLayout.position).all()


@router.post("/provider-layouts", response_model=ProviderLayoutResponse, status_code=status.HTTP_201_CREATED)
async def create_provider_layout(
    layout_data: ProviderLayoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Criar configuração de layout para um provedor"""
    # Verificar se já existe
    existing = db.query(ProviderLayout).filter(
        ProviderLayout.provider_code == layout_data.provider_code,
        ProviderLayout.section == layout_data.section
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Layout já existe para este provedor nesta seção")
    
    layout = ProviderLayout(**layout_data.model_dump())
    db.add(layout)
    db.commit()
    db.refresh(layout)
    return layout


@router.put("/provider-layouts/{layout_id}", response_model=ProviderLayoutResponse)
async def update_provider_layout(
    layout_id: int,
    layout_data: ProviderLayoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualizar configuração de layout do provedor"""
    layout = db.query(ProviderLayout).filter(ProviderLayout.id == layout_id).first()
    if not layout:
        raise HTTPException(status_code=404, detail="Layout não encontrado")
    
    update_data = layout_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(layout, field, value)
    
    db.commit()
    db.refresh(layout)
    return layout


@router.post("/provider-layouts/reorder")
async def reorder_provider_layouts(
    layout_ids: List[int],
    section: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Reordenar layouts de provedores (array de IDs na ordem desejada)"""
    query = db.query(ProviderLayout)
    if section:
        query = query.filter(ProviderLayout.section == section)
    layouts = query.all()
    
    # Atualizar posições
    for idx, layout_id in enumerate(layout_ids):
        layout = next((l for l in layouts if l.id == layout_id), None)
        if layout:
            layout.position = idx
    
    db.commit()
    return {"success": True, "message": "Ordem dos provedores atualizada"}


@router.delete("/provider-layouts/{layout_id}")
async def delete_provider_layout(
    layout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deletar configuração de layout do provedor"""
    layout = db.query(ProviderLayout).filter(ProviderLayout.id == layout_id).first()
    if not layout:
        raise HTTPException(status_code=404, detail="Layout não encontrado")
    
    db.delete(layout)
    db.commit()
    return {"success": True, "message": "Layout do provedor deletado com sucesso"}


# ========== THEMES ==========
@router.get("/themes", response_model=List[ThemeResponse])
async def get_themes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar temas"""
    return db.query(Theme).order_by(Theme.is_default.desc(), Theme.created_at).all()


@router.get("/themes/active", response_model=ThemeResponse)
async def get_active_theme(
    db: Session = Depends(get_db)
):
    """Obter tema ativo (público, usado pelo frontend)"""
    theme = db.query(Theme).filter(Theme.is_active == True, Theme.is_default == True).first()
    if not theme:
        # Retornar tema padrão se nenhum estiver marcado como padrão
        theme = db.query(Theme).filter(Theme.is_active == True).first()
    if not theme:
        raise HTTPException(status_code=404, detail="Nenhum tema ativo encontrado")
    return theme


@router.post("/themes", response_model=ThemeResponse, status_code=status.HTTP_201_CREATED)
async def create_theme(
    theme_data: ThemeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Criar novo tema"""
    # Se é o padrão, remover padrão dos outros
    if theme_data.is_default:
        db.query(Theme).filter(Theme.is_default == True).update({"is_default": False})
    
    theme = Theme(**theme_data.model_dump())
    db.add(theme)
    db.commit()
    db.refresh(theme)
    return theme


@router.put("/themes/{theme_id}", response_model=ThemeResponse)
async def update_theme(
    theme_id: int,
    theme_data: ThemeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualizar tema"""
    theme = db.query(Theme).filter(Theme.id == theme_id).first()
    if not theme:
        raise HTTPException(status_code=404, detail="Tema não encontrado")
    
    update_data = theme_data.model_dump(exclude_unset=True)
    
    # Se está marcando como padrão, remover padrão dos outros
    if update_data.get("is_default") is True:
        db.query(Theme).filter(Theme.is_default == True, Theme.id != theme_id).update({"is_default": False})
    
    for field, value in update_data.items():
        setattr(theme, field, value)
    
    db.commit()
    db.refresh(theme)
    return theme


@router.delete("/themes/{theme_id}")
async def delete_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deletar tema"""
    theme = db.query(Theme).filter(Theme.id == theme_id).first()
    if not theme:
        raise HTTPException(status_code=404, detail="Tema não encontrado")
    
    db.delete(theme)
    db.commit()
    return {"success": True, "message": "Tema deletado com sucesso"}


# ========== AFFILIATES ==========
@router.get("/affiliates", response_model=List[AffiliateResponse])
async def get_affiliates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar afiliados"""
    affiliates = db.query(Affiliate).order_by(Affiliate.created_at.desc()).all()
    
    # Para cada afiliado, buscar o usuário vinculado e adicionar informações
    result = []
    for affiliate in affiliates:
        # Buscar usuário que tem este afiliado como affiliate_id
        user = db.query(User).filter(User.affiliate_id == affiliate.id).first()
        
        # Se não encontrou, tentar pelo metadata_json
        if not user and affiliate.metadata_json:
            try:
                metadata = json.loads(affiliate.metadata_json)
                user_id = metadata.get("user_id")
                if user_id:
                    user = db.query(User).filter(User.id == user_id).first()
                    # Se encontrou pelo metadata mas não está vinculado, vincular agora
                    if user and not user.affiliate_id:
                        user.affiliate_id = affiliate.id
                        db.commit()
            except:
                pass
        
        # Criar resposta com informações do usuário
        affiliate_dict = {
            "id": affiliate.id,
            "code": affiliate.code,
            "name": affiliate.name,
            "email": affiliate.email,
            "phone": affiliate.phone,
            "commission_rate": affiliate.commission_rate,
            "is_active": affiliate.is_active,
            "metadata_json": affiliate.metadata_json,
            "created_at": affiliate.created_at,
            "updated_at": affiliate.updated_at,
            "user_id": user.id if user else None,
            "user_name": user.username if user else None,
            "user_email": user.email if user else None
        }
        result.append(affiliate_dict)
    
    return result


@router.get("/affiliates/{affiliate_id}", response_model=AffiliateResponse)
async def get_affiliate(
    affiliate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Obter afiliado específico"""
    affiliate = db.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
    if not affiliate:
        raise HTTPException(status_code=404, detail="Afiliado não encontrado")
    return affiliate


@router.post("/affiliates", response_model=AffiliateResponse, status_code=status.HTTP_201_CREATED)
async def create_affiliate(
    affiliate_data: AffiliateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Criar novo afiliado"""
    # Verificar se código já existe
    existing = db.query(Affiliate).filter(Affiliate.code == affiliate_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Código de afiliado já existe")
    
    affiliate = Affiliate(**affiliate_data.model_dump())
    db.add(affiliate)
    db.commit()
    db.refresh(affiliate)
    
    # Vincular usuário ao afiliado se user_id estiver no metadata_json
    if affiliate.metadata_json:
        try:
            metadata = json.loads(affiliate.metadata_json)
            user_id = metadata.get("user_id")
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.affiliate_id = affiliate.id
                    db.commit()
                    print(f"[AFFILIATE] Usuário {user_id} vinculado ao afiliado {affiliate.id}")
        except Exception as e:
            print(f"[AFFILIATE] Erro ao vincular usuário: {str(e)}")
    
    return affiliate


@router.put("/affiliates/{affiliate_id}", response_model=AffiliateResponse)
async def update_affiliate(
    affiliate_id: int,
    affiliate_data: AffiliateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualizar afiliado"""
    affiliate = db.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
    if not affiliate:
        raise HTTPException(status_code=404, detail="Afiliado não encontrado")
    
    # Guardar user_id anterior do metadata
    old_user_id = None
    if affiliate.metadata_json:
        try:
            old_metadata = json.loads(affiliate.metadata_json)
            old_user_id = old_metadata.get("user_id")
        except:
            pass
    
    update_data = affiliate_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(affiliate, field, value)
    
    db.commit()
    db.refresh(affiliate)
    
    # Desvincular usuário anterior se houver
    if old_user_id:
        old_user = db.query(User).filter(User.id == old_user_id).first()
        if old_user and old_user.affiliate_id == affiliate_id:
            old_user.affiliate_id = None
            db.commit()
    
    # Vincular novo usuário ao afiliado se user_id estiver no metadata_json
    if affiliate.metadata_json:
        try:
            metadata = json.loads(affiliate.metadata_json)
            user_id = metadata.get("user_id")
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.affiliate_id = affiliate.id
                    db.commit()
                    print(f"[AFFILIATE] Usuário {user_id} vinculado ao afiliado {affiliate.id}")
        except Exception as e:
            print(f"[AFFILIATE] Erro ao vincular usuário: {str(e)}")
    
    return affiliate


@router.delete("/affiliates/{affiliate_id}")
async def delete_affiliate(
    affiliate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deletar afiliado"""
    affiliate = db.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
    if not affiliate:
        raise HTTPException(status_code=404, detail="Afiliado não encontrado")
    
    db.delete(affiliate)
    db.commit()
    return {"success": True, "message": "Afiliado deletado com sucesso"}


# ========== MANAGERS ==========
@router.get("/managers")
async def get_managers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar gerentes com suas configurações"""
    managers_settings = db.query(ManagerSettings).all()
    result = []
    
    for ms in managers_settings:
        manager_user = db.query(User).filter(User.id == ms.manager_id).first()
        if not manager_user:
            continue
        
        # Buscar sub-afiliados do gerente
        sub_affiliates = db.query(SubAffiliate).filter(SubAffiliate.manager_id == ms.manager_id).all()
        sub_affiliate_ids = [sub.affiliate_id for sub in sub_affiliates]
        
        # Buscar usuários vinculados aos sub-afiliados
        users_from_subs = db.query(User).filter(User.affiliate_id.in_(sub_affiliate_ids)).all()
        user_ids = [u.id for u in users_from_subs]
        
        # FTDs dos subordinados
        ftds = db.query(FTD).filter(FTD.user_id.in_(user_ids)).all()
        
        # Calcular CPA ganho
        cpa_earned = 0.0
        for ftd in ftds:
            user = next((u for u in users_from_subs if u.id == ftd.user_id), None)
            if user and user.affiliate_id:
                sub = next((s for s in sub_affiliates if s.affiliate_id == user.affiliate_id), None)
                if sub:
                    cpa_earned += sub.cpa_rate
        
        # Depósitos dos subordinados
        deposits = db.query(Deposit).filter(Deposit.user_id.in_(user_ids)).all()
        total_deposit_amount = sum(d.amount for d in deposits)
        
        # Revshare ganho
        revshare_earned = (total_deposit_amount * ms.revshare_rate) / 100 if ms.revshare_rate > 0 else 0.0
        total_earned = cpa_earned + revshare_earned
        
        result.append({
            "id": ms.id,
            "manager_id": ms.manager_id,
            "user_id": manager_user.id,
            "user_name": manager_user.username,
            "user_email": manager_user.email,
            "cpa_pool": ms.cpa_pool,
            "cpa_distributed": ms.cpa_distributed,
            "cpa_available": ms.cpa_pool - ms.cpa_distributed,
            "revshare_rate": ms.revshare_rate,
            "total_earned": total_earned,
            "is_active": manager_user.is_active,
            "created_at": ms.created_at,
            "updated_at": ms.updated_at
        })
    
    return result


@router.post("/managers", status_code=status.HTTP_201_CREATED)
async def create_manager(
    user_id: int = Query(...),
    cpa_pool: float = Query(...),
    revshare_rate: float = Query(0.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Criar novo gerente"""
    # Verificar se usuário existe
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Verificar se já é gerente
    existing = db.query(ManagerSettings).filter(ManagerSettings.manager_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuário já é gerente")
    
    # Criar configuração do gerente
    manager_settings = ManagerSettings(
        manager_id=user_id,
        cpa_pool=cpa_pool,
        cpa_distributed=0.0,
        revshare_rate=revshare_rate
    )
    db.add(manager_settings)
    
    # Atualizar role do usuário para manager se necessário
    if user.role not in [UserRole.AGENT, UserRole.MANAGER]:
        user.role = UserRole.MANAGER
    
    db.commit()
    db.refresh(manager_settings)
    
    return {
        "id": manager_settings.id,
        "manager_id": manager_settings.manager_id,
        "cpa_pool": manager_settings.cpa_pool,
        "revshare_rate": manager_settings.revshare_rate
    }


@router.put("/managers/{manager_id}")
async def update_manager(
    manager_id: int,
    cpa_pool: Optional[float] = None,
    revshare_rate: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualizar configurações do gerente"""
    manager_settings = db.query(ManagerSettings).filter(ManagerSettings.manager_id == manager_id).first()
    if not manager_settings:
        raise HTTPException(status_code=404, detail="Gerente não encontrado")
    
    if cpa_pool is not None:
        manager_settings.cpa_pool = cpa_pool
    if revshare_rate is not None:
        manager_settings.revshare_rate = revshare_rate
    
    db.commit()
    db.refresh(manager_settings)
    
    # Retornar no mesmo formato do GET
    manager_user = db.query(User).filter(User.id == manager_settings.manager_id).first()
    sub_affiliates = db.query(SubAffiliate).filter(SubAffiliate.manager_id == manager_settings.manager_id).all()
    sub_affiliate_ids = [sub.affiliate_id for sub in sub_affiliates]
    users_from_subs = db.query(User).filter(User.affiliate_id.in_(sub_affiliate_ids)).all()
    user_ids = [u.id for u in users_from_subs]
    
    ftds = db.query(FTD).filter(FTD.user_id.in_(user_ids)).all()
    cpa_earned = 0.0
    for ftd in ftds:
        user = next((u for u in users_from_subs if u.id == ftd.user_id), None)
        if user and user.affiliate_id:
            sub = next((s for s in sub_affiliates if s.affiliate_id == user.affiliate_id), None)
            if sub:
                cpa_earned += sub.cpa_rate
    
    deposits = db.query(Deposit).filter(Deposit.user_id.in_(user_ids)).all()
    total_deposit_amount = sum(d.amount for d in deposits)
    revshare_earned = (total_deposit_amount * manager_settings.revshare_rate) / 100 if manager_settings.revshare_rate > 0 else 0.0
    total_earned = cpa_earned + revshare_earned
    
    return {
        "id": manager_settings.id,
        "manager_id": manager_settings.manager_id,
        "user_id": manager_user.id if manager_user else None,
        "user_name": manager_user.username if manager_user else None,
        "user_email": manager_user.email if manager_user else None,
        "cpa_pool": manager_settings.cpa_pool,
        "cpa_distributed": manager_settings.cpa_distributed,
        "cpa_available": manager_settings.cpa_pool - manager_settings.cpa_distributed,
        "revshare_rate": manager_settings.revshare_rate,
        "total_earned": total_earned,
        "is_active": manager_user.is_active if manager_user else False,
        "created_at": manager_settings.created_at,
        "updated_at": manager_settings.updated_at
    }


@router.delete("/managers/{manager_id}")
async def delete_manager(
    manager_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deletar gerente"""
    manager_settings = db.query(ManagerSettings).filter(ManagerSettings.manager_id == manager_id).first()
    if not manager_settings:
        raise HTTPException(status_code=404, detail="Gerente não encontrado")
    
    db.delete(manager_settings)
    db.commit()
    return {"success": True, "message": "Gerente deletado com sucesso"}


# ========== IGAMEWIN PROVIDER CONFIG ==========
@router.get("/igamewin-provider-configs", response_model=List[IGameWinProviderConfigResponse])
async def get_igamewin_provider_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar configurações de provedores IGameWin (até 3)"""
    configs = db.query(IGameWinProviderConfig).order_by(IGameWinProviderConfig.position).all()
    return configs


@router.get("/igamewin-provider-configs/{config_id}", response_model=IGameWinProviderConfigResponse)
async def get_igamewin_provider_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Obter configuração específica"""
    config = db.query(IGameWinProviderConfig).filter(IGameWinProviderConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return config


@router.post("/igamewin-provider-configs", response_model=IGameWinProviderConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_igamewin_provider_config(
    config_data: IGameWinProviderConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Criar configuração de provedor IGameWin"""
    # Validar posição (1, 2 ou 3)
    if config_data.position not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Posição deve ser 1, 2 ou 3")
    
    # Verificar se já existe configuração com esse provider_code
    existing = db.query(IGameWinProviderConfig).filter(
        IGameWinProviderConfig.provider_code == config_data.provider_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Provedor já configurado")
    
    # Verificar se já existe configuração com essa posição
    existing_pos = db.query(IGameWinProviderConfig).filter(
        IGameWinProviderConfig.position == config_data.position
    ).first()
    if existing_pos:
        raise HTTPException(status_code=400, detail=f"Posição {config_data.position} já está em uso")
    
    # Limitar a 3 configurações
    count = db.query(IGameWinProviderConfig).count()
    if count >= 3:
        raise HTTPException(status_code=400, detail="Máximo de 3 provedores permitidos")
    
    config = IGameWinProviderConfig(**config_data.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.put("/igamewin-provider-configs/{config_id}", response_model=IGameWinProviderConfigResponse)
async def update_igamewin_provider_config(
    config_id: int,
    config_data: IGameWinProviderConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualizar configuração de provedor IGameWin"""
    config = db.query(IGameWinProviderConfig).filter(IGameWinProviderConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    update_data = config_data.model_dump(exclude_unset=True)
    
    # Validar posição se fornecida
    if "position" in update_data and update_data["position"] not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Posição deve ser 1, 2 ou 3")
    
    # Se mudando posição, verificar se não conflita
    if "position" in update_data and update_data["position"] != config.position:
        existing_pos = db.query(IGameWinProviderConfig).filter(
            IGameWinProviderConfig.position == update_data["position"],
            IGameWinProviderConfig.id != config_id
        ).first()
        if existing_pos:
            raise HTTPException(status_code=400, detail=f"Posição {update_data['position']} já está em uso")
    
    # Se mudando provider_code, verificar se não conflita
    if "provider_code" in update_data and update_data["provider_code"] != config.provider_code:
        existing = db.query(IGameWinProviderConfig).filter(
            IGameWinProviderConfig.provider_code == update_data["provider_code"],
            IGameWinProviderConfig.id != config_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Provedor já configurado")
    
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    return config


@router.delete("/igamewin-provider-configs/{config_id}")
async def delete_igamewin_provider_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deletar configuração de provedor IGameWin"""
    config = db.query(IGameWinProviderConfig).filter(IGameWinProviderConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    db.delete(config)
    db.commit()
    return {"success": True, "message": "Configuração deletada com sucesso"}


@router.post("/igamewin-provider-configs/reorder")
async def reorder_igamewin_provider_configs(
    config_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Reordenar configurações de provedores IGameWin"""
    if len(config_ids) > 3:
        raise HTTPException(status_code=400, detail="Máximo de 3 provedores permitidos")
    
    configs = db.query(IGameWinProviderConfig).filter(IGameWinProviderConfig.id.in_(config_ids)).all()
    if len(configs) != len(config_ids):
        raise HTTPException(status_code=400, detail="Uma ou mais configurações não encontradas")
    
    # Atualizar posições
    for idx, config_id in enumerate(config_ids, start=1):
        config = next(c for c in configs if c.id == config_id)
        config.position = idx
    
    db.commit()
    return {"success": True, "message": "Ordem atualizada com sucesso"}


# ========== TRACKING CONFIG ==========
@router.get("/tracking-configs", response_model=List[TrackingConfigResponse])
async def get_tracking_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar configurações de tracking"""
    configs = db.query(TrackingConfig).order_by(TrackingConfig.created_at.desc()).all()
    return configs


@router.get("/tracking-configs/{config_id}", response_model=TrackingConfigResponse)
async def get_tracking_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Obter configuração de tracking específica"""
    config = db.query(TrackingConfig).filter(TrackingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return config


@router.post("/tracking-configs", response_model=TrackingConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_tracking_config(
    config_data: TrackingConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Criar configuração de tracking"""
    # Validar tipo
    if config_data.type not in ["webhook", "pixel", "api"]:
        raise HTTPException(status_code=400, detail="Tipo deve ser: webhook, pixel ou api")
    
    # Validar campos obrigatórios por tipo
    if config_data.type == "webhook" and not config_data.url:
        raise HTTPException(status_code=400, detail="URL é obrigatória para webhook")
    if config_data.type == "pixel" and not config_data.pixel_id:
        raise HTTPException(status_code=400, detail="Pixel ID é obrigatório para pixel")
    if config_data.type == "api" and not config_data.access_token and not config_data.api_key:
        raise HTTPException(status_code=400, detail="Access Token ou API Key é obrigatório para API")
    
    config = TrackingConfig(**config_data.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.put("/tracking-configs/{config_id}", response_model=TrackingConfigResponse)
async def update_tracking_config(
    config_id: int,
    config_data: TrackingConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualizar configuração de tracking"""
    config = db.query(TrackingConfig).filter(TrackingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    update_data = config_data.model_dump(exclude_unset=True)
    
    # Validar tipo se fornecido
    if "type" in update_data and update_data["type"] not in ["webhook", "pixel", "api"]:
        raise HTTPException(status_code=400, detail="Tipo deve ser: webhook, pixel ou api")
    
    # Validar campos obrigatórios por tipo
    final_type = update_data.get("type", config.type)
    if final_type == "webhook" and not (update_data.get("url") or config.url):
        raise HTTPException(status_code=400, detail="URL é obrigatória para webhook")
    if final_type == "pixel" and not (update_data.get("pixel_id") or config.pixel_id):
        raise HTTPException(status_code=400, detail="Pixel ID é obrigatório para pixel")
    if final_type == "api" and not (update_data.get("access_token") or config.access_token or update_data.get("api_key") or config.api_key):
        raise HTTPException(status_code=400, detail="Access Token ou API Key é obrigatório para API")
    
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    return config


@router.delete("/tracking-configs/{config_id}")
async def delete_tracking_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deletar configuração de tracking"""
    config = db.query(TrackingConfig).filter(TrackingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    db.delete(config)
    db.commit()
    return {"success": True, "message": "Configuração deletada com sucesso"}


# ========== WEBHOOKS ==========

@router.get("/webhook-url")
async def get_webhook_url(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Retorna a URL do webhook que deve ser configurada no painel da Gatebox
    """
    import os
    webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "")
    
    # Se não tiver variável, usar a URL padrão do backend
    if not webhook_base_url:
        # URL padrão do backend em produção
        webhook_base_url = "https://api.fortunevegas.site"
    
    webhook_url = f"{webhook_base_url}/api/webhooks/gatebox"
    return {
        "webhook_url": webhook_url,
        "instructions": "Configure esta URL no painel da Gatebox para receber notificações de eventos"
    }


@router.get("/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar todos os webhooks externos configurados"""
    webhooks = db.query(Webhook).order_by(Webhook.created_at.desc()).all()
    return webhooks


@router.post("/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Criar novo webhook"""
    # Validar event_type
    try:
        event_type = WebhookEventType(webhook_data.event_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de evento inválido. Tipos válidos: {[e.value for e in WebhookEventType]}"
        )
    
    # Validar URL
    if not webhook_data.url or not webhook_data.url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="URL inválida. Deve começar com http:// ou https://")
    
    webhook = Webhook(
        url=webhook_data.url,
        username=webhook_data.username,
        password=webhook_data.password,
        event_type=event_type,
        is_active=webhook_data.is_active
    )
    
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.put("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualizar webhook"""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook não encontrado")
    
    update_data = webhook_data.model_dump(exclude_unset=True)
    
    # Validar event_type se fornecido
    if "event_type" in update_data:
        try:
            update_data["event_type"] = WebhookEventType(update_data["event_type"])
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de evento inválido. Tipos válidos: {[e.value for e in WebhookEventType]}"
            )
    
    # Validar URL se fornecida
    if "url" in update_data:
        if not update_data["url"] or not update_data["url"].startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL inválida. Deve começar com http:// ou https://")
    
    for field, value in update_data.items():
        setattr(webhook, field, value)
    
    db.commit()
    db.refresh(webhook)
    return webhook


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deletar webhook"""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook não encontrado")
    
    db.delete(webhook)
    db.commit()
    return {"success": True, "message": "Webhook deletado com sucesso"}
