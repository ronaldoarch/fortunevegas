from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    User, Deposit, Withdrawal, FTD, Gateway, IGameWinAgent, FTDSettings,
    TransactionStatus, UserRole, Bet, BetStatus, Notification, NotificationType,
    GameLayout, Theme, Affiliate
)
from schemas import (
    UserResponse, UserCreate, UserUpdate,
    DepositResponse, DepositCreate, DepositUpdate,
    WithdrawalResponse, WithdrawalCreate, WithdrawalUpdate,
    FTDResponse, FTDCreate, FTDUpdate,
    GatewayResponse, GatewayCreate, GatewayUpdate,
    IGameWinAgentResponse, IGameWinAgentCreate, IGameWinAgentUpdate,
    FTDSettingsResponse, FTDSettingsCreate, FTDSettingsUpdate,
    GameLayoutResponse, GameLayoutCreate, GameLayoutUpdate,
    ThemeResponse, ThemeCreate, ThemeUpdate,
    AffiliateResponse, AffiliateCreate, AffiliateUpdate
)
from auth import get_password_hash
from igamewin_api import get_igamewin_api

router = APIRouter(prefix="/api/admin", tags=["admin"])
public_router = APIRouter(prefix="/api/public", tags=["public"])


# ========== USERS ==========
@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    users = db.query(User).offset(skip).limit(limit).all()
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
        settings = FTDSettings(pass_rate=0.0, min_amount=0.0, is_active=True)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.put("/ftd-settings", response_model=FTDSettingsResponse)
async def update_ftd_settings(
    settings_data: FTDSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    settings = db.query(FTDSettings).filter(FTDSettings.is_active == True).first()
    if not settings:
        settings = FTDSettings(**settings_data.model_dump())
        db.add(settings)
    else:
        update_data = settings_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
    
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
    agents = db.query(IGameWinAgent).all()
    return agents


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
    
    update_data = agent_data.model_dump(exclude_unset=True)
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


@public_router.get("/games")
async def public_games(
    provider_code: Optional[str] = Query(None),
    section: Optional[str] = Query("home", description="Seção: home, featured"),
    db: Session = Depends(get_db)
):
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

    # Obter configurações de layout do admin
    layouts = db.query(GameLayout).filter(
        GameLayout.section == section,
        GameLayout.is_active == True
    ).order_by(GameLayout.position).all()
    
    # Criar mapa de layout por game_code
    layout_map = {layout.game_code: layout for layout in layouts}
    
    public_games = []
    for g in games:
        status_val = g.get("status")
        is_active = (status_val == 1) or (status_val is True) or (str(status_val).lower() == "active")
        if not is_active:
            continue
        
        game_code = g.get("game_code") or g.get("code") or g.get("game_id") or g.get("id") or g.get("slug")
        layout = layout_map.get(game_code)
        
        # Se há layout configurado, usar posição e destaque dele
        # Se não há layout, jogo aparece no final
        position = layout.position if layout else 999999
        is_featured = layout.is_featured if layout else False
        
        public_games.append({
            "name": g.get("game_name") or g.get("name") or g.get("title") or g.get("gameTitle"),
            "code": game_code,
            "provider": g.get("provider_code") or g.get("provider") or g.get("provider_name") or g.get("vendor") or g.get("vendor_name") or chosen_provider,
            "banner": g.get("banner") or g.get("image") or g.get("icon"),
            "status": "active",
            "position": position,
            "is_featured": is_featured
        })

    # Ordenar por posição
    public_games.sort(key=lambda x: x["position"])
    
    # Filtrar destaques se solicitado
    if section == "featured":
        public_games = [g for g in public_games if g["is_featured"]]

    return {
        "providers": providers,
        "provider_code": chosen_provider,
        "games": public_games
    }


@public_router.get("/games/{game_code}/launch")
async def launch_game(
    game_code: str,
    provider_code: Optional[str] = Query(None),
    lang: str = Query("pt", description="Language code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Launch a game - requires user authentication AND positive balance
    
    Follows IGameWin API documentation:
    - Uses user_code (username) to launch game
    - Returns launch_url from API response
    - If provider_code is not provided, searches for the game in the game list to find its provider
    - Requires user to have balance > 0
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
        "user_code": current_user.username
    }


# ========== SEAMLESS API (IGameWin) ==========
@public_router.post("/gold_api")
async def seamless_api(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    API Seamless para IGameWin - requerida para modo seamless
    Endpoints suportados:
    - user_balance: Retornar saldo do usuário
    - transaction: Processar transação (debit/credit/debit_credit)
    """
    from fastapi import Request
    import hashlib
    
    method = request.get("method")
    agent_code = request.get("agent_code")
    agent_secret = request.get("agent_secret")  # IGameWin usa agent_secret aqui
    user_code = request.get("user_code")
    
    if not method or not agent_code or not agent_secret or not user_code:
        return {"status": 0, "msg": "INVALID_PARAMETER"}
    
    # Verificar credenciais do agente
    agent = db.query(IGameWinAgent).filter(
        IGameWinAgent.agent_code == agent_code,
        IGameWinAgent.is_active == True
    ).first()
    
    if not agent:
        return {"status": 0, "msg": "INVALID_AGENT"}
    
    # Verificar agent_secret (na doc IGameWin, pode ser o agent_key ou outro campo)
    # Por padrão, vamos usar agent_key como secret
    if agent_secret != agent.agent_key:
        # Se tiver credentials JSON, pode ter agent_secret lá
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
        return {
            "status": 1,
            "user_balance": user.balance
        }
    
    # Método: transaction
    if method == "transaction":
        agent_balance = request.get("agent_balance", 0)  # Saldo do agente (IGameWin envia)
        user_balance_sent = request.get("user_balance", 0)  # Saldo que IGameWin acha que o user tem
        
        # Obter dados da transação baseado no tipo de jogo
        game_type = request.get("game_type")
        
        if game_type == "slot":
            slot_data = request.get("slot", {})
            provider_code = slot_data.get("provider_code")
            game_code = slot_data.get("game_code")
            txn_type = slot_data.get("txn_type")  # debit, credit, debit_credit
            bet_money = slot_data.get("bet_money", 0)
            win_money = slot_data.get("win_money", 0)
            txn_id = slot_data.get("txn_id")
            
            if not txn_id:
                return {"status": 0, "msg": "INVALID_PARAMETER"}
            
            # Verificar se transação já foi processada
            existing_bet = db.query(Bet).filter(Bet.transaction_id == txn_id).first()
            if existing_bet:
                # Retornar saldo atualizado
                return {
                    "status": 1,
                    "user_balance": user.balance
                }
            
            # Processar transação
            try:
                if txn_type == "debit":
                    # Apenas aposta (debit)
                    if user.balance < bet_money:
                        return {"status": 0, "user_balance": user.balance, "msg": "INSUFFICIENT_USER_FUNDS"}
                    
                    user.balance -= bet_money
                    win_amount = 0
                    
                elif txn_type == "credit":
                    # Apenas ganho (credit)
                    user.balance += win_money
                    bet_money = 0
                    win_amount = win_money
                    
                elif txn_type == "debit_credit":
                    # Aposta e ganho (debit_credit)
                    if user.balance < bet_money:
                        return {"status": 0, "user_balance": user.balance, "msg": "INSUFFICIENT_USER_FUNDS"}
                    
                    user.balance -= bet_money
                    user.balance += win_money
                    win_amount = win_money
                    
                else:
                    return {"status": 0, "msg": "INVALID_TXN_TYPE"}
                
                # Criar registro de aposta
                bet = Bet(
                    user_id=user.id,
                    game_id=game_code,
                    game_name=game_code,  # Pode ser melhorado com nome real
                    provider=provider_code or "IGameWin",
                    amount=bet_money,
                    win_amount=win_amount,
                    status=BetStatus.WON if win_amount > 0 else BetStatus.LOST,
                    transaction_id=txn_id,
                    external_id=txn_id,
                    metadata_json=json.dumps(slot_data)
                )
                db.add(bet)
                
                # Sincronizar com IGameWin se necessário
                api = get_igamewin_api(db)
                if api:
                    # Transferir saldo para IGameWin se necessário (seamless mode)
                    # A lógica aqui depende de como você quer gerenciar o saldo
                    # Por enquanto, apenas atualizamos nosso banco
                    pass
                
                db.commit()
                db.refresh(user)
                
                return {
                    "status": 1,
                    "user_balance": user.balance
                }
                
            except Exception as e:
                db.rollback()
                return {"status": 0, "msg": f"INTERNAL_ERROR: {str(e)}"}
        
        return {"status": 0, "msg": "UNSUPPORTED_GAME_TYPE"}
    
    return {"status": 0, "msg": "INVALID_METHOD"}


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
    return db.query(Affiliate).order_by(Affiliate.created_at.desc()).all()


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
    
    update_data = affiliate_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(affiliate, field, value)
    
    db.commit()
    db.refresh(affiliate)
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
