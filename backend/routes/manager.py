"""
Rotas públicas para gerentes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timedelta
from database import get_db
from models import User, Deposit, Withdrawal, Affiliate, FTD, SubAffiliate, ManagerSettings
from dependencies import get_current_user
from schemas import SubAffiliateCreate, SubAffiliateResponse, ManagerSettingsResponse
from auth import get_password_hash
import json

router = APIRouter(prefix="/api/public/manager", tags=["manager"])


def get_manager_settings(db: Session, manager_id: int) -> ManagerSettings:
    """Busca ou cria configurações do gerente"""
    settings = db.query(ManagerSettings).filter(ManagerSettings.manager_id == manager_id).first()
    if not settings:
        settings = ManagerSettings(manager_id=manager_id, cpa_pool=0.0, cpa_distributed=0.0, revshare_rate=0.0)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/settings", response_model=ManagerSettingsResponse)
async def get_my_manager_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna configurações do gerente (CPA Pool, etc)
    """
    if current_user.role not in ['agent', 'manager']:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Apenas gerentes podem acessar este painel."
        )
    
    settings = get_manager_settings(db, current_user.id)
    
    # Calcular CPA disponível
    cpa_available = settings.cpa_pool - settings.cpa_distributed
    
    return {
        "id": settings.id,
        "manager_id": settings.manager_id,
        "cpa_pool": settings.cpa_pool,
        "cpa_distributed": settings.cpa_distributed,
        "cpa_available": cpa_available,
        "revshare_rate": settings.revshare_rate,
        "created_at": settings.created_at,
        "updated_at": settings.updated_at
    }


@router.get("/sub-affiliates", response_model=List[SubAffiliateResponse])
async def get_my_sub_affiliates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna lista de sub-afiliados do gerente
    """
    if current_user.role not in ['agent', 'manager']:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Apenas gerentes podem acessar este painel."
        )
    
    sub_affiliates = db.query(SubAffiliate).filter(SubAffiliate.manager_id == current_user.id).all()
    
    result = []
    for sub in sub_affiliates:
        affiliate = db.query(Affiliate).filter(Affiliate.id == sub.affiliate_id).first()
        result.append({
            "id": sub.id,
            "manager_id": sub.manager_id,
            "affiliate_id": sub.affiliate_id,
            "user_id": sub.user_id,
            "cpa_rate": sub.cpa_rate,
            "revshare_rate": sub.revshare_rate,
            "affiliate_code": affiliate.code if affiliate else None,
            "affiliate_name": affiliate.name if affiliate else None,
            "created_at": sub.created_at
        })
    
    return result


@router.post("/sub-affiliates", response_model=SubAffiliateResponse, status_code=status.HTTP_201_CREATED)
async def create_sub_affiliate(
    sub_data: SubAffiliateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cria um novo sub-afiliado
    """
    if current_user.role not in ['agent', 'manager']:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Apenas gerentes podem criar sub-afiliados."
        )
    
    # Verificar se há CPA disponível
    settings = get_manager_settings(db, current_user.id)
    cpa_available = settings.cpa_pool - settings.cpa_distributed
    
    if sub_data.cpa_rate > cpa_available:
        raise HTTPException(
            status_code=400,
            detail=f"CPA insuficiente. Disponível: R$ {cpa_available:.2f}, Solicitado: R$ {sub_data.cpa_rate:.2f}"
        )
    
    # Verificar se código já existe
    existing_affiliate = db.query(Affiliate).filter(Affiliate.code == sub_data.code).first()
    if existing_affiliate:
        raise HTTPException(
            status_code=400,
            detail="Código de afiliado já existe"
        )
    
    # Verificar se username já existe
    existing_user = db.query(User).filter(User.username == sub_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username já existe"
        )
    
    # Criar afiliado
    affiliate = Affiliate(
        code=sub_data.code,
        name=sub_data.username,
        email=sub_data.email,
        commission_rate=sub_data.revshare_rate,
        is_active=True
    )
    db.add(affiliate)
    db.flush()
    
    # Criar usuário para o sub-afiliado
    user = User(
        username=sub_data.username,
        email=sub_data.email,
        password_hash=get_password_hash(sub_data.password),
        role="user",
        affiliate_id=affiliate.id,
        is_active=True,
        is_verified=False
    )
    db.add(user)
    db.flush()
    
    # Criar sub-afiliado
    sub_affiliate = SubAffiliate(
        manager_id=current_user.id,
        affiliate_id=affiliate.id,
        user_id=user.id,
        cpa_rate=sub_data.cpa_rate,
        revshare_rate=sub_data.revshare_rate
    )
    db.add(sub_affiliate)
    
    # Atualizar CPA distribuído
    settings.cpa_distributed += sub_data.cpa_rate
    
    db.commit()
    db.refresh(sub_affiliate)
    db.refresh(affiliate)
    
    return {
        "id": sub_affiliate.id,
        "manager_id": sub_affiliate.manager_id,
        "affiliate_id": sub_affiliate.affiliate_id,
        "user_id": sub_affiliate.user_id,
        "cpa_rate": sub_affiliate.cpa_rate,
        "revshare_rate": sub_affiliate.revshare_rate,
        "affiliate_code": affiliate.code,
        "affiliate_name": affiliate.name,
        "created_at": sub_affiliate.created_at
    }


@router.get("/performance")
async def get_manager_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna métricas de desempenho do gerente
    """
    if current_user.role not in ['agent', 'manager']:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Apenas gerentes podem acessar este painel."
        )
    
    settings = get_manager_settings(db, current_user.id)
    
    # Buscar sub-afiliados
    sub_affiliates = db.query(SubAffiliate).filter(SubAffiliate.manager_id == current_user.id).all()
    sub_affiliate_ids = [sub.affiliate_id for sub in sub_affiliates]
    
    # Buscar usuários vinculados aos sub-afiliados
    users_from_subs = db.query(User).filter(User.affiliate_id.in_(sub_affiliate_ids)).all()
    user_ids = [u.id for u in users_from_subs]
    
    # FTDs dos subordinados dos sub-afiliados
    ftds = db.query(FTD).filter(FTD.user_id.in_(user_ids)).all()
    
    # Calcular CPA ganho (mesmo valor que distribuiu)
    cpa_earned = 0.0
    for ftd in ftds:
        # Encontrar qual sub-afiliado trouxe este usuário
        user = next((u for u in users_from_subs if u.id == ftd.user_id), None)
        if user and user.affiliate_id:
            sub = next((s for s in sub_affiliates if s.affiliate_id == user.affiliate_id), None)
            if sub:
                cpa_earned += sub.cpa_rate
    
    # Depósitos dos subordinados dos sub-afiliados
    deposits = db.query(Deposit).filter(Deposit.user_id.in_(user_ids)).all()
    total_deposit_amount = sum(d.amount for d in deposits)
    
    # Revshare ganho
    revshare_earned = (total_deposit_amount * settings.revshare_rate) / 100 if settings.revshare_rate > 0 else 0.0
    
    return {
        "sub_affiliates": len(sub_affiliates),
        "cpa_pool": settings.cpa_pool,
        "cpa_earned": cpa_earned,
        "revshare_earned": revshare_earned
    }


@router.get("/commission")
async def get_manager_commission(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna informações de comissão do gerente
    """
    if current_user.role not in ['agent', 'manager']:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Apenas gerentes podem acessar este painel."
        )
    
    settings = get_manager_settings(db, current_user.id)
    
    # Buscar sub-afiliados
    sub_affiliates = db.query(SubAffiliate).filter(SubAffiliate.manager_id == current_user.id).all()
    sub_affiliate_ids = [sub.affiliate_id for sub in sub_affiliates]
    
    # Buscar usuários vinculados aos sub-afiliados
    users_from_subs = db.query(User).filter(User.affiliate_id.in_(sub_affiliate_ids)).all()
    user_ids = [u.id for u in users_from_subs]
    
    # FTDs dos subordinados dos sub-afiliados
    ftds = db.query(FTD).filter(FTD.user_id.in_(user_ids)).all()
    
    # Calcular CPA ganho (mesmo valor que distribuiu)
    cpa_earned = 0.0
    for ftd in ftds:
        user = next((u for u in users_from_subs if u.id == ftd.user_id), None)
        if user and user.affiliate_id:
            sub = next((s for s in sub_affiliates if s.affiliate_id == user.affiliate_id), None)
            if sub:
                cpa_earned += sub.cpa_rate
    
    # Depósitos dos subordinados dos sub-afiliados
    deposits = db.query(Deposit).filter(Deposit.user_id.in_(user_ids)).all()
    total_deposit_amount = sum(d.amount for d in deposits)
    
    # Revshare ganho
    revshare_earned = (total_deposit_amount * settings.revshare_rate) / 100 if settings.revshare_rate > 0 else 0.0
    
    total_earned = cpa_earned + revshare_earned
    
    return {
        "total_earned": total_earned,
        "cpa_earned": cpa_earned,
        "revshare_earned": revshare_earned,
        "revshare_rate": settings.revshare_rate
    }
