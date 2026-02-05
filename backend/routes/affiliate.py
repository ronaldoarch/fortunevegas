"""
Rotas públicas para afiliados
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import datetime, timedelta
from database import get_db
from models import User, Deposit, Withdrawal, Affiliate, FTD, AffiliateMetric, AffiliateMetricType
from dependencies import get_current_user
from schemas import AffiliateResponse
from fastapi import Query

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
    
    # Calcular comissões (CPA e Revshare) a partir das métricas não convertidas
    import json
    # Buscar todas as métricas do afiliado (sem filtro de período para conversão)
    all_cpa_metrics = db.query(AffiliateMetric).filter(
        AffiliateMetric.affiliate_id == affiliate.id,
        AffiliateMetric.metric_type == AffiliateMetricType.FIRST_DEPOSIT
    ).all()
    
    all_revshare_metrics = db.query(AffiliateMetric).filter(
        AffiliateMetric.affiliate_id == affiliate.id,
        AffiliateMetric.metric_type == AffiliateMetricType.BET
    ).all()
    
    # Filtrar métricas não convertidas
    cpa_earned = 0.0
    for metric in all_cpa_metrics:
        metadata = {}
        if metric.metadata_json:
            try:
                metadata = json.loads(metric.metadata_json)
            except:
                pass
        if not metadata.get("converted", False) and metric.amount:
            cpa_earned += metric.amount
    
    revshare_earned = 0.0
    for metric in all_revshare_metrics:
        metadata = {}
        if metric.metadata_json:
            try:
                metadata = json.loads(metric.metadata_json)
            except:
                pass
        if not metadata.get("converted", False) and metric.amount:
            revshare_earned += metric.amount
    
    # Calcular também valores totais (incluindo convertidos) para histórico do período
    cpa_rate = 2.0  # Pode vir do affiliate.metadata_json ou configuração
    total_cpa_earned = total_ftds * cpa_rate
    
    revshare_rate = affiliate.commission_rate if affiliate.commission_rate > 0 else 2.0
    total_revshare_earned = (total_deposit_amount * revshare_rate) / 100
    
    total_earned = cpa_earned + revshare_earned  # Apenas não convertidas (todas, não apenas do período)
    
    return {
        "new_subordinates": new_subordinates,
        "total_deposits": total_deposits,
        "total_ftds": total_ftds,
        "users_with_ftd": users_with_ftd,
        "total_deposit_amount": total_deposit_amount,
        "total_ftd_amount": total_ftd_amount,
        "total_withdrawals": total_withdrawals,
        "total_withdrawal_amount": total_withdrawal_amount,
        "cpa_earned": cpa_earned,  # Não convertido
        "revshare_earned": revshare_earned,  # Não convertido
        "total_earned": total_earned,  # Total não convertido (disponível para conversão)
        "total_cpa_earned": total_cpa_earned,  # Total histórico (incluindo convertido)
        "total_revshare_earned": total_revshare_earned,  # Total histórico (incluindo convertido)
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


@router.get("/metrics")
async def get_affiliate_metrics(
    period: Optional[str] = Query("month", description="week, month, all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna métricas detalhadas de rastreamento do afiliado
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
    from datetime import timedelta
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
    
    # Buscar métricas
    metrics_query = db.query(AffiliateMetric).filter(
        AffiliateMetric.affiliate_id == affiliate.id
    )
    
    if period == "last_week" or period == "last_month":
        metrics_query = metrics_query.filter(
            AffiliateMetric.created_at >= start_date,
            AffiliateMetric.created_at < end_date
        )
    elif period != "all":
        metrics_query = metrics_query.filter(AffiliateMetric.created_at >= start_date)
    
    metrics = metrics_query.order_by(AffiliateMetric.created_at.desc()).all()
    
    # Agrupar por tipo
    clicks = [m for m in metrics if m.metric_type == AffiliateMetricType.CLICK]
    registrations = [m for m in metrics if m.metric_type == AffiliateMetricType.REGISTRATION]
    first_deposits = [m for m in metrics if m.metric_type == AffiliateMetricType.FIRST_DEPOSIT]
    deposits = [m for m in metrics if m.metric_type == AffiliateMetricType.DEPOSIT]
    withdrawals = [m for m in metrics if m.metric_type == AffiliateMetricType.WITHDRAWAL]
    
    # Calcular totais
    total_clicks = len(clicks)
    total_registrations = len(registrations)
    total_first_deposits = len(first_deposits)
    total_deposits = len(deposits)
    total_deposit_amount = sum(d.amount or 0 for d in deposits)
    total_withdrawals = len(withdrawals)
    total_withdrawal_amount = sum(w.amount or 0 for w in withdrawals)
    
    # Taxa de conversão
    conversion_rate = (total_registrations / total_clicks * 100) if total_clicks > 0 else 0
    registration_to_deposit_rate = (total_first_deposits / total_registrations * 100) if total_registrations > 0 else 0
    
    return {
        "period": period,
        "total_clicks": total_clicks,
        "total_registrations": total_registrations,
        "total_first_deposits": total_first_deposits,
        "total_deposits": total_deposits,
        "total_deposit_amount": total_deposit_amount,
        "total_withdrawals": total_withdrawals,
        "total_withdrawal_amount": total_withdrawal_amount,
        "conversion_rate": round(conversion_rate, 2),
        "registration_to_deposit_rate": round(registration_to_deposit_rate, 2),
        "metrics_by_date": [
            {
                "date": m.created_at.strftime("%Y-%m-%d"),
                "type": m.metric_type.value,
                "amount": m.amount,
                "count": 1
            }
            for m in metrics
        ]
    }


@router.post("/convert-rewards")
async def convert_rewards_to_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Converte recompensas de afiliado (CPA + Revshare) em saldo real sacável
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
    
    # Buscar todas as métricas não convertidas do afiliado
    # Métricas que geram recompensa: FIRST_DEPOSIT (CPA) e BET (Revshare)
    import json
    metrics = db.query(AffiliateMetric).filter(
        AffiliateMetric.affiliate_id == affiliate.id,
        AffiliateMetric.metric_type.in_([AffiliateMetricType.FIRST_DEPOSIT, AffiliateMetricType.BET])
    ).all()
    
    # Filtrar métricas não convertidas (verificar metadata_json)
    unconverted_metrics = []
    total_rewards = 0.0
    
    for metric in metrics:
        metadata = {}
        if metric.metadata_json:
            try:
                metadata = json.loads(metric.metadata_json)
            except:
                pass
        
        # Verificar se já foi convertido
        if not metadata.get("converted", False):
            unconverted_metrics.append(metric)
            if metric.amount:
                total_rewards += metric.amount
    
    if total_rewards <= 0:
        raise HTTPException(
            status_code=400,
            detail="Não há recompensas disponíveis para conversão"
        )
    
    # Adicionar saldo ao usuário afiliado
    current_user.balance += total_rewards
    
    # Marcar métricas como convertidas
    for metric in unconverted_metrics:
        metadata = {}
        if metric.metadata_json:
            try:
                metadata = json.loads(metric.metadata_json)
            except:
                pass
        
        metadata["converted"] = True
        metadata["converted_at"] = datetime.utcnow().isoformat()
        metadata["converted_by_user_id"] = current_user.id
        metric.metadata_json = json.dumps(metadata)
    
    db.commit()
    db.refresh(current_user)
    
    print(f"[AFFILIATE] Recompensas convertidas - Usuário: {current_user.id}, Valor: R$ {total_rewards:.2f}")
    
    return {
        "success": True,
        "amount_converted": total_rewards,
        "new_balance": current_user.balance,
        "message": f"R$ {total_rewards:.2f} convertidos para saldo real com sucesso"
    }
