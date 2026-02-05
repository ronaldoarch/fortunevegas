"""
Rotas públicas para afiliados
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import datetime, timedelta
from database import get_db
from models import User, Deposit, Withdrawal, Affiliate, FTD
from dependencies import get_current_user
from schemas import AffiliateResponse

router = APIRouter(prefix="/api/public/affiliate", tags=["affiliate"])


@router.get("/me")
async def get_my_affiliate_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna dados do afiliado do usuário logado
    """
    if not current_user.affiliate_id:
        raise HTTPException(
            status_code=404,
            detail="Usuário não está vinculado a um afiliado"
        )
    
    affiliate = db.query(Affiliate).filter(Affiliate.id == current_user.affiliate_id).first()
    if not affiliate:
        raise HTTPException(
            status_code=404,
            detail="Afiliado não encontrado"
        )
    
    return affiliate


@router.get("/link")
async def get_affiliate_link(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna o link de afiliado do usuário
    """
    if not current_user.affiliate_id:
        raise HTTPException(
            status_code=404,
            detail="Usuário não está vinculado a um afiliado"
        )
    
    affiliate = db.query(Affiliate).filter(Affiliate.id == current_user.affiliate_id).first()
    if not affiliate:
        raise HTTPException(
            status_code=404,
            detail="Afiliado não encontrado"
        )
    
    # Construir URL base (usar variável de ambiente ou padrão)
    import os
    frontend_url = os.getenv("FRONTEND_URL", "https://fortunevegas.site")
    affiliate_link = f"{frontend_url}?ref={affiliate.code}"
    
    return {
        "code": affiliate.code,
        "link": affiliate_link,
        "affiliate_id": affiliate.id
    }


@router.get("/stats")
async def get_affiliate_stats(
    period: Optional[str] = "month",  # week, month, all
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna estatísticas do afiliado (subordinados, depósitos, comissões)
    """
    if not current_user.affiliate_id:
        raise HTTPException(
            status_code=404,
            detail="Usuário não está vinculado a um afiliado"
        )
    
    affiliate = db.query(Affiliate).filter(Affiliate.id == current_user.affiliate_id).first()
    if not affiliate:
        raise HTTPException(
            status_code=404,
            detail="Afiliado não encontrado"
        )
    
    # Calcular período
    now = datetime.utcnow()
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "last_week":
        start_date = now - timedelta(days=14)
        end_date = now - timedelta(days=7)
    elif period == "last_month":
        start_date = now - timedelta(days=60)
        end_date = now - timedelta(days=30)
    else:  # month ou all
        start_date = now - timedelta(days=30)
        end_date = None
    
    # Buscar subordinados (usuários com affiliate_id = current_user.affiliate_id)
    subordinates_query = db.query(User).filter(User.affiliate_id == affiliate.id)
    
    if period == "last_week" or period == "last_month":
        subordinates_query = subordinates_query.filter(
            User.created_at >= start_date,
            User.created_at < end_date
        )
    elif period != "all":
        subordinates_query = subordinates_query.filter(User.created_at >= start_date)
    
    subordinates = subordinates_query.all()
    subordinate_ids = [u.id for u in subordinates]
    
    # Novos subordinados
    new_subordinates = len(subordinates)
    
    # Depósitos dos subordinados
    deposits_query = db.query(Deposit).filter(Deposit.user_id.in_(subordinate_ids))
    if period == "last_week" or period == "last_month":
        deposits_query = deposits_query.filter(
            Deposit.created_at >= start_date,
            Deposit.created_at < end_date
        )
    elif period != "all":
        deposits_query = deposits_query.filter(Deposit.created_at >= start_date)
    
    deposits = deposits_query.all()
    total_deposits = len(deposits)
    total_deposit_amount = sum(d.amount for d in deposits)
    
    # Primeiros depósitos (FTDs)
    ftds_query = db.query(FTD).filter(FTD.user_id.in_(subordinate_ids))
    if period == "last_week" or period == "last_month":
        ftds_query = ftds_query.filter(
            FTD.created_at >= start_date,
            FTD.created_at < end_date
        )
    elif period != "all":
        ftds_query = ftds_query.filter(FTD.created_at >= start_date)
    
    ftds = ftds_query.all()
    total_ftds = len(ftds)
    total_ftd_amount = sum(f.amount for f in ftds)
    
    # Usuários com primeiro depósito
    users_with_ftd = len(set(f.user_id for f in ftds))
    
    # Saques
    withdrawals_query = db.query(Withdrawal).filter(Withdrawal.user_id.in_(subordinate_ids))
    if period == "last_week" or period == "last_month":
        withdrawals_query = withdrawals_query.filter(
            Withdrawal.created_at >= start_date,
            Withdrawal.created_at < end_date
        )
    elif period != "all":
        withdrawals_query = withdrawals_query.filter(Withdrawal.created_at >= start_date)
    
    withdrawals = withdrawals_query.all()
    total_withdrawals = len(withdrawals)
    total_withdrawal_amount = sum(w.amount for w in withdrawals)
    
    # Calcular comissões (CPA e Revshare)
    # CPA: valor fixo por primeiro depósito (assumindo R$ 2,00 por padrão)
    cpa_rate = 2.0  # Pode vir do affiliate.metadata_json ou configuração
    cpa_earned = total_ftds * cpa_rate
    
    # Revshare: porcentagem sobre depósitos (assumindo 2% por padrão)
    revshare_rate = affiliate.commission_rate if affiliate.commission_rate > 0 else 2.0
    revshare_earned = (total_deposit_amount * revshare_rate) / 100
    
    total_earned = cpa_earned + revshare_earned
    
    return {
        "new_subordinates": new_subordinates,
        "total_deposits": total_deposits,
        "total_ftds": total_ftds,
        "users_with_ftd": users_with_ftd,
        "total_deposit_amount": total_deposit_amount,
        "total_ftd_amount": total_ftd_amount,
        "total_withdrawals": total_withdrawals,
        "total_withdrawal_amount": total_withdrawal_amount,
        "cpa_earned": cpa_earned,
        "revshare_earned": revshare_earned,
        "total_earned": total_earned,
        "cpa_rate": cpa_rate,
        "revshare_rate": revshare_rate,
        "status": "Ativo" if affiliate.is_active else "Inativo"
    }


@router.get("/performance")
async def get_affiliate_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna métricas de desempenho do afiliado
    """
    if not current_user.affiliate_id:
        raise HTTPException(
            status_code=404,
            detail="Usuário não está vinculado a um afiliado"
        )
    
    affiliate = db.query(Affiliate).filter(Affiliate.id == current_user.affiliate_id).first()
    if not affiliate:
        raise HTTPException(
            status_code=404,
            detail="Afiliado não encontrado"
        )
    
    # Buscar todos os subordinados
    subordinates = db.query(User).filter(User.affiliate_id == affiliate.id).all()
    subordinate_ids = [u.id for u in subordinates]
    
    # Total de indicações
    total_referrals = len(subordinates)
    
    # Depósitos dos indicados
    deposits = db.query(Deposit).filter(Deposit.user_id.in_(subordinate_ids)).all()
    total_deposit_amount = sum(d.amount for d in deposits)
    
    # CPA ganho
    ftds = db.query(FTD).filter(FTD.user_id.in_(subordinate_ids)).all()
    cpa_rate = 2.0  # Pode vir de configuração
    cpa_earned = len(ftds) * cpa_rate
    
    # Revshare ganho
    revshare_rate = affiliate.commission_rate if affiliate.commission_rate > 0 else 2.0
    revshare_earned = (total_deposit_amount * revshare_rate) / 100
    
    return {
        "referrals": total_referrals,
        "deposits_from_referrals": total_deposit_amount,
        "cpa_earned": cpa_earned,
        "revshare_earned": revshare_earned
    }
