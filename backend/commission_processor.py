"""
Processador de comissões (CPA e Revshare) para afiliados e gerentes
"""
from sqlalchemy.orm import Session
from models import User, Deposit, Withdrawal, FTD, Affiliate, SubAffiliate, ManagerSettings, AffiliateMetric, AffiliateMetricType
from datetime import datetime
import json


def process_cpa_on_ftd(user_id: int, deposit_id: int, db: Session):
    """
    Processa CPA quando um usuário faz seu primeiro depósito (FTD)
    
    Lógica:
    - Se usuário foi trazido por sub-afiliado:
      - Sub ganha proporcional ao CPA dele (ex: R$ 15)
      - Gerente ganha proporcional ao CPA total dele (ex: R$ 30)
    - Se usuário foi trazido por afiliado direto:
      - Afiliado ganha CPA configurado
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.affiliate_id:
        return
    
    deposit = db.query(Deposit).filter(Deposit.id == deposit_id).first()
    if not deposit:
        return
    
    affiliate = db.query(Affiliate).filter(Affiliate.id == user.affiliate_id).first()
    if not affiliate:
        return
    
    # Verificar se é sub-afiliado (tem gerente)
    sub_affiliate = db.query(SubAffiliate).filter(SubAffiliate.affiliate_id == affiliate.id).first()
    
    if sub_affiliate:
        # Usuário foi trazido por sub-afiliado
        manager_id = sub_affiliate.manager_id
        manager_settings = db.query(ManagerSettings).filter(ManagerSettings.manager_id == manager_id).first()
        
        if manager_settings:
            # Sub ganha proporcional ao CPA dele (ex: R$ 15)
            sub_cpa = sub_affiliate.cpa_rate
            # Gerente ganha proporcional ao CPA total dele (pool original, ex: R$ 30)
            # O gerente ganha o CPA total, não apenas o que sobrou
            manager_cpa = manager_settings.cpa_pool
            
            # Registrar métricas
            # Métrica para sub-afiliado
            sub_metric = AffiliateMetric(
                affiliate_id=affiliate.id,
                manager_id=manager_id,
                sub_affiliate_id=sub_affiliate.id,
                metric_type=AffiliateMetricType.FIRST_DEPOSIT,
                user_id=user_id,
                amount=sub_cpa,
                metadata_json=json.dumps({
                    "deposit_id": deposit_id,
                    "deposit_amount": deposit.amount,
                    "cpa_type": "sub_affiliate",
                    "cpa_amount": sub_cpa
                })
            )
            db.add(sub_metric)
            
            # Métrica para gerente
            manager_metric = AffiliateMetric(
                manager_id=manager_id,
                metric_type=AffiliateMetricType.FIRST_DEPOSIT,
                user_id=user_id,
                amount=manager_cpa,
                metadata_json=json.dumps({
                    "deposit_id": deposit_id,
                    "deposit_amount": deposit.amount,
                    "cpa_type": "manager",
                    "cpa_amount": manager_cpa,
                    "sub_affiliate_id": sub_affiliate.id
                })
            )
            db.add(manager_metric)
            
            print(f"[CPA] FTD processado - Usuário: {user_id}, Sub CPA: R$ {sub_cpa:.2f}, Gerente CPA: R$ {manager_cpa:.2f}")
    else:
        # Usuário foi trazido por afiliado direto
        # Buscar CPA do afiliado (pode estar no metadata_json ou usar padrão)
        cpa_rate = 2.0  # Padrão
        if affiliate.metadata_json:
            try:
                metadata = json.loads(affiliate.metadata_json)
                cpa_rate = metadata.get("cpa_rate", 2.0)
            except:
                pass
        
        # Registrar métrica
        metric = AffiliateMetric(
            affiliate_id=affiliate.id,
            metric_type=AffiliateMetricType.FIRST_DEPOSIT,
            user_id=user_id,
            amount=cpa_rate,
            metadata_json=json.dumps({
                "deposit_id": deposit_id,
                "deposit_amount": deposit.amount,
                "cpa_type": "direct_affiliate",
                "cpa_amount": cpa_rate
            })
        )
        db.add(metric)
        
        print(f"[CPA] FTD processado - Usuário: {user_id}, Afiliado direto CPA: R$ {cpa_rate:.2f}")


def calculate_user_loss(user_id: int, db: Session) -> float:
    """
    Calcula a perda do usuário (depósitos - saques - saldo atual)
    """
    # Total de depósitos aprovados
    deposits = db.query(Deposit).filter(
        Deposit.user_id == user_id,
        Deposit.status == "approved"
    ).all()
    total_deposits = sum(d.amount for d in deposits)
    
    # Total de saques aprovados
    withdrawals = db.query(Withdrawal).filter(
        Withdrawal.user_id == user_id,
        Withdrawal.status == "approved"
    ).all()
    total_withdrawals = sum(w.amount for w in withdrawals)
    
    # Saldo atual do usuário
    user = db.query(User).filter(User.id == user_id).first()
    current_balance = user.balance if user else 0.0
    
    # Perda = depósitos - saques - saldo atual
    loss = total_deposits - total_withdrawals - current_balance
    
    return max(0.0, loss)  # Não pode ser negativo


def process_revshare_on_bet(user_id: int, bet_amount: float, bet_result: float, db: Session):
    """
    Processa revshare baseado na perda do usuário após uma aposta
    
    Revshare é calculado sobre a perda total do usuário (não sobre depósitos)
    Perda = Depósitos - Saques - Saldo Atual
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.affiliate_id:
        return
    
    # Calcular perda atual do usuário
    loss = calculate_user_loss(user_id, db)
    
    affiliate = db.query(Affiliate).filter(Affiliate.id == user.affiliate_id).first()
    if not affiliate:
        return
    
    # Verificar se é sub-afiliado
    sub_affiliate = db.query(SubAffiliate).filter(SubAffiliate.affiliate_id == affiliate.id).first()
    
    if sub_affiliate:
        # Usuário foi trazido por sub-afiliado
        manager_id = sub_affiliate.manager_id
        manager_settings = db.query(ManagerSettings).filter(ManagerSettings.manager_id == manager_id).first()
        
        if manager_settings:
            # Sub ganha revshare proporcional à taxa dele
            sub_revshare_rate = sub_affiliate.revshare_rate
            sub_revshare = (loss * sub_revshare_rate) / 100
            
            # Gerente ganha revshare proporcional à taxa dele
            manager_revshare_rate = manager_settings.revshare_rate
            manager_revshare = (loss * manager_revshare_rate) / 100
            
            # Registrar métricas (atualizar ou criar)
            # Buscar métrica existente ou criar nova
            sub_metric = db.query(AffiliateMetric).filter(
                AffiliateMetric.affiliate_id == affiliate.id,
                AffiliateMetric.user_id == user_id,
                AffiliateMetric.metric_type == AffiliateMetricType.BET
            ).first()
            
            if sub_metric:
                # Atualizar métrica existente com nova perda
                sub_metric.amount = sub_revshare
                sub_metric.metadata_json = json.dumps({
                    "user_loss": loss,
                    "revshare_rate": sub_revshare_rate,
                    "revshare_amount": sub_revshare,
                    "last_updated": datetime.utcnow().isoformat()
                })
            else:
                sub_metric = AffiliateMetric(
                    affiliate_id=affiliate.id,
                    manager_id=manager_id,
                    sub_affiliate_id=sub_affiliate.id,
                    metric_type=AffiliateMetricType.BET,
                    user_id=user_id,
                    amount=sub_revshare,
                    metadata_json=json.dumps({
                        "user_loss": loss,
                        "revshare_rate": sub_revshare_rate,
                        "revshare_amount": sub_revshare
                    })
                )
                db.add(sub_metric)
            
            # Métrica para gerente
            manager_metric = db.query(AffiliateMetric).filter(
                AffiliateMetric.manager_id == manager_id,
                AffiliateMetric.user_id == user_id,
                AffiliateMetric.metric_type == AffiliateMetricType.BET
            ).first()
            
            if manager_metric:
                manager_metric.amount = manager_revshare
                manager_metric.metadata_json = json.dumps({
                    "user_loss": loss,
                    "revshare_rate": manager_revshare_rate,
                    "revshare_amount": manager_revshare,
                    "sub_affiliate_id": sub_affiliate.id,
                    "last_updated": datetime.utcnow().isoformat()
                })
            else:
                manager_metric = AffiliateMetric(
                    manager_id=manager_id,
                    metric_type=AffiliateMetricType.BET,
                    user_id=user_id,
                    amount=manager_revshare,
                    metadata_json=json.dumps({
                        "user_loss": loss,
                        "revshare_rate": manager_revshare_rate,
                        "revshare_amount": manager_revshare,
                        "sub_affiliate_id": sub_affiliate.id
                    })
                )
                db.add(manager_metric)
            
            print(f"[REVSHARE] Perda processada - Usuário: {user_id}, Perda: R$ {loss:.2f}, Sub Revshare: R$ {sub_revshare:.2f}, Gerente Revshare: R$ {manager_revshare:.2f}")
    else:
        # Usuário foi trazido por afiliado direto
        revshare_rate = affiliate.commission_rate if affiliate.commission_rate > 0 else 2.0
        revshare = (loss * revshare_rate) / 100
        
        # Buscar ou criar métrica
        metric = db.query(AffiliateMetric).filter(
            AffiliateMetric.affiliate_id == affiliate.id,
            AffiliateMetric.user_id == user_id,
            AffiliateMetric.metric_type == AffiliateMetricType.BET
        ).first()
        
        if metric:
            metric.amount = revshare
            metric.metadata_json = json.dumps({
                "user_loss": loss,
                "revshare_rate": revshare_rate,
                "revshare_amount": revshare,
                "last_updated": datetime.utcnow().isoformat()
            })
        else:
            metric = AffiliateMetric(
                affiliate_id=affiliate.id,
                metric_type=AffiliateMetricType.BET,
                user_id=user_id,
                amount=revshare,
                metadata_json=json.dumps({
                    "user_loss": loss,
                    "revshare_rate": revshare_rate,
                    "revshare_amount": revshare
                })
            )
            db.add(metric)
        
        print(f"[REVSHARE] Perda processada - Usuário: {user_id}, Perda: R$ {loss:.2f}, Afiliado direto Revshare: R$ {revshare:.2f}")
