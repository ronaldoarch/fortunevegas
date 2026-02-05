"""
Rotas públicas para pagamentos (depósitos e saques) usando Gatebox
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from sqlalchemy import desc, or_
from database import get_db
from models import User, Deposit, Withdrawal, Gateway, TransactionStatus, FTDSettings, WebhookEventType, Bet, BetStatus, Notification, Coupon, CouponUse, Promotion, PromotionUse, PromotionType, FTD
from gatebox_api import GateboxAPI
from schemas import DepositResponse, WithdrawalResponse, DepositPixRequest, WithdrawalPixRequest, CouponValidateRequest, CouponResponse
from dependencies import get_current_user
from webhook_dispatcher import dispatch_webhook
from tracking_dispatcher import dispatch_tracking_event
from commission_processor import process_cpa_on_ftd, process_revshare_on_bet, calculate_user_loss
from datetime import datetime
import json
import uuid
import os
import re

router = APIRouter(prefix="/api/public/payments", tags=["payments"])
webhook_router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.get("/settings")
async def get_payment_settings(db: Session = Depends(get_db)):
    """
    Retorna configurações de pagamento (mínimos e máximos) para uso público
    """
    ftd_settings = db.query(FTDSettings).filter(FTDSettings.is_active == True).first()
    if not ftd_settings:
        return {
            "min_amount": 10.0,
            "max_amount": 0.0,
            "min_withdrawal": 10.0
        }
    return {
        "min_amount": ftd_settings.min_amount if ftd_settings.min_amount > 0 else 10.0,
        "max_amount": ftd_settings.max_amount,
        "min_withdrawal": ftd_settings.min_withdrawal if ftd_settings.min_withdrawal > 0 else 10.0
    }


def get_active_pix_gateway(db: Session) -> Gateway:
    """Busca gateway PIX ativo"""
    gateway = db.query(Gateway).filter(
        Gateway.type == "pix",
        Gateway.is_active == True
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gateway PIX não configurado ou inativo"
        )
    
    return gateway


def get_gatebox_client(gateway: Gateway) -> GateboxAPI:
    """Cria cliente Gatebox a partir das credenciais do gateway"""
    try:
        credentials = json.loads(gateway.credentials) if gateway.credentials else {}
        username = credentials.get("username")
        password = credentials.get("password")
        api_url = credentials.get("api_url", "https://api.gatebox.com.br")
        
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Credenciais do gateway não configuradas (username e password são obrigatórios)"
            )
        
        return GateboxAPI(username=username, password=password, api_url=api_url)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credenciais do gateway inválidas"
        )


@router.post("/deposit/pix", response_model=DepositResponse, status_code=status.HTTP_201_CREATED)
async def create_pix_deposit(
    deposit_data: DepositPixRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cria depósito via PIX usando Gatebox
    
    Args:
        deposit_data: Dados do depósito (amount, payer_name, payer_tax_id)
    """
    # Usar usuário autenticado
    user = current_user
    
    if deposit_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
    
    # Buscar configurações FTD para validar depósito mínimo e máximo
    ftd_settings = db.query(FTDSettings).filter(FTDSettings.is_active == True).first()
    min_deposit = 10.0  # Valor padrão
    max_deposit = 0.0  # 0 = sem limite
    if ftd_settings:
        if ftd_settings.min_amount > 0:
            min_deposit = ftd_settings.min_amount
        if ftd_settings.max_amount > 0:
            max_deposit = ftd_settings.max_amount
    
    if deposit_data.amount < min_deposit:
        raise HTTPException(status_code=400, detail=f"Valor mínimo de depósito é R$ {min_deposit:.2f}")
    
    if max_deposit > 0 and deposit_data.amount > max_deposit:
        raise HTTPException(status_code=400, detail=f"Valor máximo de depósito é R$ {max_deposit:.2f}")
    
    # Validar e calcular bônus do cupom se fornecido
    bonus_amount = 0.0
    coupon = None
    promotion_bonus = 0.0
    promotion = None
    
    if deposit_data.coupon_code:
        coupon, bonus_amount, coupon_error = validate_and_calculate_coupon_bonus(
            deposit_data.coupon_code, deposit_data.amount, user.id, db
        )
        if coupon_error:
            raise HTTPException(status_code=400, detail=coupon_error)
    
    # Verificar se é primeiro depósito e aplicar promoção automática
    existing_deposits = db.query(Deposit).filter(
        Deposit.user_id == user.id,
        Deposit.status == TransactionStatus.APPROVED
    ).count()
    
    is_first_deposit = existing_deposits == 0
    
    if is_first_deposit:
        # Buscar promoção ativa de primeiro depósito
        now = datetime.utcnow()
        active_promotion = db.query(Promotion).filter(
            Promotion.is_active == True,
            Promotion.is_first_deposit_only == True,
            Promotion.start_date <= now,
            Promotion.end_date >= now,
            Promotion.min_deposit_amount <= deposit_data.amount
        ).order_by(desc(Promotion.created_at)).first()
        
        if active_promotion:
            # Calcular bônus da promoção
            if active_promotion.bonus_type == "percentage":
                promotion_bonus = (deposit_data.amount * active_promotion.bonus_value) / 100
            else:  # fixed
                promotion_bonus = active_promotion.bonus_value
            
            # Aplicar limite máximo se existir
            if active_promotion.max_bonus_amount is not None and promotion_bonus > active_promotion.max_bonus_amount:
                promotion_bonus = active_promotion.max_bonus_amount
            
            promotion = active_promotion
    
    # Total de bônus (cupom + promoção)
    total_bonus = bonus_amount + promotion_bonus
    
    # Validar dados do usuário
    if not deposit_data.payer_name or len(deposit_data.payer_name.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome do pagador inválido"
        )
    
    # CPF/CNPJ é opcional - só usar se for válido (11 ou 14 dígitos)
    # Se não fornecido, usar CPF temporário válido para testes (Gatebox pode exigir document)
    payer_tax_id_to_send = None
    if deposit_data.payer_tax_id:
        tax_id_clean = deposit_data.payer_tax_id.replace('.', '').replace('-', '').replace(' ', '').replace('/', '')
        # Validar se é CPF (11 dígitos) ou CNPJ (14 dígitos)
        if len(tax_id_clean) == 11 or len(tax_id_clean) == 14:
            payer_tax_id_to_send = tax_id_clean
    
    # Se não fornecido ou inválido, usar CPF válido conhecido para testes
    # CPF 11144477735 é um CPF válido conhecido usado para testes
    if not payer_tax_id_to_send:
        payer_tax_id_to_send = "11144477735"
    
    # Buscar gateway PIX ativo
    gateway = get_active_pix_gateway(db)
    
    # Criar cliente Gatebox
    gatebox = get_gatebox_client(gateway)
    
    # Gerar external_id único para controle de duplicidade
    external_id = f"DEP_{user.id}_{int(datetime.utcnow().timestamp())}"
    
    # Preparar dados para a API Gatebox
    # Telefone é opcional - só enviar se existir e estiver em formato válido
    phone_to_send = None
    if user.phone:
        import re
        # Limpar telefone (remover caracteres não numéricos)
        phone_clean = re.sub(r'[^0-9]', '', user.phone)
        # Validar se tem pelo menos 10 dígitos (DDD + número)
        if len(phone_clean) >= 10:
            # Formatar como +55 (código do Brasil) + DDD + número
            if not phone_clean.startswith('55'):
                phone_to_send = f"+55{phone_clean}"
            else:
                phone_to_send = f"+{phone_clean}"
    
    # Email é opcional - usar temporário se não houver
    email_to_send = user.email if user.email and '@' in user.email else f"{user.username}@temp.com"
    
    # Gerar código PIX
    # document só será enviado se for CPF/CNPJ válido (11 ou 14 dígitos)
    pix_response = await gatebox.create_immediate_qrcode(
        external_id=external_id,
        amount=deposit_data.amount,
        name=deposit_data.payer_name,
        expire=3600,  # 1 hora de expiração
        document=payer_tax_id_to_send,  # Opcional - só enviado se for CPF/CNPJ válido
        email=email_to_send,
        phone=phone_to_send,  # Pode ser None se não houver telefone válido
        identification=f"Depósito - {deposit_data.payer_name}",
        description=f"Depósito de R$ {deposit_data.amount:.2f}"
    )
    
    # Verificar se houve erro na resposta da Gatebox
    if not pix_response:
        raise HTTPException(
            status_code=502,
            detail="Sem resposta do gateway PIX"
        )
    
    if pix_response.get("error"):
        # Extrair mensagem de erro específica da Gatebox
        if pix_response and pix_response.get("error"):
            error_detail = pix_response.get("detail", "Erro desconhecido")
            status_code = pix_response.get("status_code", 502)
            
            # Mensagens específicas da Gatebox
            if "UNAUTHORIZED" in str(error_detail) or "401" in str(status_code):
                error_detail = "Não autorizado. Verifique as credenciais do gateway."
            elif "INVALID" in str(error_detail) or "400" in str(status_code):
                error_detail = "Dados inválidos. Verifique os dados informados."
        else:
            error_detail = "Sem resposta do gateway"
            status_code = 502
        
        raise HTTPException(
            status_code=status_code,
            detail=error_detail
        )
    
    # Criar registro de depósito
    # A Gatebox pode retornar dados em diferentes estruturas
    # Verificar se há um campo "data" ou similar que contenha a resposta real
    actual_response = pix_response
    if isinstance(pix_response, dict):
        # Verificar se há um campo "data" que contenha a resposta real
        if "data" in pix_response and isinstance(pix_response["data"], dict):
            actual_response = pix_response["data"]
        # Verificar se há um campo "result" que contenha a resposta real
        elif "result" in pix_response and isinstance(pix_response["result"], dict):
            actual_response = pix_response["result"]
    
    # Log para debug
    print(f"Gatebox PIX Response (raw): {json.dumps(pix_response, indent=2)}")
    print(f"Gatebox PIX Response (actual): {json.dumps(actual_response, indent=2)}")
    
    # Extrair dados do PIX da resposta Gatebox
    # A Gatebox retorna o código PIX no campo "key"
    pix_code = (
        actual_response.get("key") or  # Campo principal da Gatebox
        actual_response.get("qrCode") or 
        actual_response.get("pixCode") or 
        actual_response.get("emv") or 
        actual_response.get("qr_code") or
        actual_response.get("pix_code") or
        actual_response.get("code") or
        actual_response.get("qrCodeString") or
        ""
    )
    
    # A Gatebox pode não retornar QR Code Base64 diretamente
    # Vamos tentar encontrar ou gerar depois se necessário
    pix_qr_code_base64 = (
        actual_response.get("qrCodeBase64") or 
        actual_response.get("base64") or 
        actual_response.get("qr_code_base64") or
        actual_response.get("qrCodeBase64Image") or
        actual_response.get("qrCodeImage") or
        actual_response.get("qrCodeImageBase64") or
        actual_response.get("qrCode") or  # Pode ser base64 também
        ""
    )
    
    transaction_id_gatebox = (
        actual_response.get("transactionId") or 
        actual_response.get("id") or 
        actual_response.get("transaction_id") or
        actual_response.get("externalId") or
        ""
    )
    
    print(f"Extracted PIX Code: {pix_code[:50] if pix_code else 'EMPTY'}...")
    print(f"Extracted QR Code Base64: {'Yes (' + str(len(pix_qr_code_base64)) + ' chars)' if pix_qr_code_base64 else 'No'}")
    print(f"Extracted Transaction ID: {transaction_id_gatebox}")
    
    # Validar se temos pelo menos o código PIX
    if not pix_code:
        print(f"WARNING: No PIX code found in response. Full response: {json.dumps(pix_response, indent=2)}")
    
    deposit = Deposit(
        user_id=user.id,
        gateway_id=gateway.id,
        amount=deposit_data.amount,
        bonus_amount=total_bonus,  # Total de bônus (cupom + promoção)
        coupon_code=deposit_data.coupon_code.upper().strip() if deposit_data.coupon_code else None,
        status=TransactionStatus.PENDING,
        transaction_id=transaction_id_gatebox or str(uuid.uuid4()),
        external_id=external_id,
        metadata_json=json.dumps({
            "pix_code": pix_code,
            "pix_qr_code": pix_code,
            "pix_qr_code_base64": pix_qr_code_base64,
            "transaction_id": transaction_id_gatebox,
            "end_to_end": actual_response.get("endToEnd") or actual_response.get("end_to_end"),
            "external_id": external_id,
            "gatebox_response": actual_response,
            "gatebox_raw_response": pix_response,  # Manter resposta original para debug
            "promotion_id": promotion.id if promotion else None,
            "promotion_bonus": promotion_bonus,
            "coupon_bonus": bonus_amount,
            "is_first_deposit": is_first_deposit
        })
    )
    
    db.add(deposit)
    db.commit()
    db.refresh(deposit)
    
    return deposit


@router.post("/deposit/{deposit_id}/check-status")
async def check_deposit_status(
    deposit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verifica o status de um depósito consultando a API da Gatebox
    Útil quando o webhook não foi recebido ou houve algum problema
    """
    deposit = db.query(Deposit).filter(
        Deposit.id == deposit_id,
        Deposit.user_id == current_user.id
    ).first()
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Depósito não encontrado")
    
    # Buscar gateway PIX ativo
    gateway = get_active_pix_gateway(db)
    
    # Obter credenciais do gateway
    credentials = json.loads(gateway.credentials) if gateway.credentials else {}
    username = credentials.get("username")
    password = credentials.get("password")
    api_url = credentials.get("api_url", "https://api.gatebox.com.br")
    
    if not username or not password:
        raise HTTPException(status_code=500, detail="Credenciais do gateway não configuradas")
    
    # Consultar status na Gatebox
    gatebox = GateboxAPI(username=username, password=password, api_url=api_url)
    
    # Tentar consultar pelo external_id primeiro
    status_response = await gatebox.get_pix_status(external_id=deposit.external_id)
    
    if status_response and status_response.get("error"):
        # Se falhar, tentar pelo transaction_id no metadata
        metadata = json.loads(deposit.metadata_json) if deposit.metadata_json else {}
        transaction_id = metadata.get("transaction_id") or metadata.get("uuid")
        if transaction_id:
            status_response = await gatebox.get_pix_status(transaction_id=transaction_id)
    
    if not status_response or status_response.get("error"):
        return {
            "deposit_id": deposit.id,
            "current_status": deposit.status.value,
            "gatebox_status": None,
            "error": status_response.get("detail") if status_response else "Erro ao consultar status"
        }
    
    # Extrair dados da resposta
    gatebox_data = status_response.get("data") or status_response
    gatebox_status = gatebox_data.get("status") or gatebox_data.get("statusTransaction")
    
    # Processar atualização de status
    status_upper = str(gatebox_status).upper() if gatebox_status else ""
    
    if status_upper in ["PAID", "PAID_OUT", "CONFIRMED", "APPROVED", "SUCCESS", "COMPLETED"]:
        if deposit.status != TransactionStatus.APPROVED:
            deposit.status = TransactionStatus.APPROVED
            # Adicionar saldo ao usuário separando real e bônus
            user = db.query(User).filter(User.id == deposit.user_id).first()
            if user:
                # Extrair informações do metadata
                metadata = json.loads(deposit.metadata_json) if deposit.metadata_json else {}
                promotion_id = metadata.get("promotion_id")
                promotion_bonus = metadata.get("promotion_bonus", 0)
                coupon_bonus = metadata.get("coupon_bonus", 0)
                
                # Valor real depositado (sempre sacável)
                real_amount = deposit.amount
                user.balance += real_amount
                
                # Bônus total (cupom + promoção)
                total_bonus = deposit.bonus_amount
                
                # Verificar se os bônus são sacáveis
                withdrawable_bonus = 0.0
                non_withdrawable_bonus = 0.0
                
                if coupon_bonus > 0 and deposit.coupon_code:
                    coupon = db.query(Coupon).filter(Coupon.code == deposit.coupon_code).first()
                    if coupon:
                        if coupon.is_withdrawable:
                            withdrawable_bonus += coupon_bonus
                        else:
                            non_withdrawable_bonus += coupon_bonus
                        coupon.uses += 1
                        coupon_use = CouponUse(
                            coupon_id=coupon.id,
                            user_id=user.id,
                            deposit_id=deposit.id,
                            bonus_amount=coupon_bonus
                        )
                        db.add(coupon_use)
                
                if promotion_bonus > 0 and promotion_id:
                    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
                    if promotion:
                        if promotion.is_withdrawable:
                            withdrawable_bonus += promotion_bonus
                        else:
                            non_withdrawable_bonus += promotion_bonus
                        promotion_use = PromotionUse(
                            promotion_id=promotion.id,
                            user_id=user.id,
                            deposit_id=deposit.id,
                            bonus_amount=promotion_bonus
                        )
                        db.add(promotion_use)
                
                # Adicionar bônus sacável ao saldo real
                user.balance += withdrawable_bonus
                
                # Adicionar bônus não sacável ao saldo de bônus
                user.bonus_balance += non_withdrawable_bonus
                
                # Verificar se é primeiro depósito (FTD) e criar registro
                is_first_deposit = metadata.get("is_first_deposit", False)
                existing_ftd = db.query(FTD).filter(FTD.user_id == user.id).first()
                
                if is_first_deposit and not existing_ftd:
                    # Criar FTD
                    ftd_settings = db.query(FTDSettings).filter(FTDSettings.is_active == True).first()
                    pass_rate = ftd_settings.pass_rate if ftd_settings else 0.0
                    
                    ftd = FTD(
                        user_id=user.id,
                        deposit_id=deposit.id,
                        amount=deposit.amount,
                        is_first_deposit=True,
                        pass_rate=pass_rate,
                        status=TransactionStatus.APPROVED
                    )
                    db.add(ftd)
                    db.flush()  # Flush para obter o ID do FTD
                    
                    # Processar CPA no primeiro depósito
                    try:
                        process_cpa_on_ftd(user.id, deposit.id, db)
                    except Exception as e:
                        print(f"[CPA] Erro ao processar CPA (não crítico): {str(e)}")
                
                db.commit()
                return {
                    "deposit_id": deposit.id,
                    "current_status": "APPROVED",
                    "gatebox_status": gatebox_status,
                    "balance_credited": True,
                    "new_balance": user.balance,
                    "bonus_applied": deposit.bonus_amount
                }
    elif status_upper in ["CANCELLED", "CANCELED", "REJECTED", "FAILED", "CHARGEBACK", "EXPIRED"]:
        if deposit.status == TransactionStatus.APPROVED:
            # Reverter saldo se já foi aprovado (mesma lógica dos webhooks)
            user = db.query(User).filter(User.id == deposit.user_id).first()
            if user:
                # Extrair informações do metadata
                metadata = json.loads(deposit.metadata_json) if deposit.metadata_json else {}
                promotion_id = metadata.get("promotion_id")
                promotion_bonus = metadata.get("promotion_bonus", 0)
                coupon_bonus = metadata.get("coupon_bonus", 0)
                
                # Reverter valor real depositado
                real_amount = deposit.amount
                if user.balance >= real_amount:
                    user.balance -= real_amount
                    
                    # Reverter bônus sacável e não sacável separadamente
                    if coupon_bonus > 0 and deposit.coupon_code:
                        coupon = db.query(Coupon).filter(Coupon.code == deposit.coupon_code).first()
                        if coupon:
                            if coupon.is_withdrawable:
                                if user.balance >= coupon_bonus:
                                    user.balance -= coupon_bonus
                            else:
                                if user.bonus_balance >= coupon_bonus:
                                    user.bonus_balance -= coupon_bonus
                            if coupon.uses > 0:
                                coupon.uses -= 1
                        # Remover registro de uso
                        coupon_use = db.query(CouponUse).filter(
                            CouponUse.deposit_id == deposit.id
                        ).first()
                        if coupon_use:
                            db.delete(coupon_use)
                    
                    # Reverter uso da promoção se houver
                    if promotion_bonus > 0 and promotion_id:
                        promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
                        if promotion:
                            if promotion.is_withdrawable:
                                if user.balance >= promotion_bonus:
                                    user.balance -= promotion_bonus
                            else:
                                if user.bonus_balance >= promotion_bonus:
                                    user.bonus_balance -= promotion_bonus
                        promotion_use = db.query(PromotionUse).filter(
                            PromotionUse.deposit_id == deposit.id
                        ).first()
                        if promotion_use:
                            db.delete(promotion_use)
        deposit.status = TransactionStatus.CANCELLED
        db.commit()
    
    return {
        "deposit_id": deposit.id,
        "current_status": deposit.status.value,
        "gatebox_status": gatebox_status,
        "balance_credited": deposit.status == TransactionStatus.APPROVED
    }


@router.post("/withdrawal/pix", response_model=WithdrawalResponse, status_code=status.HTTP_201_CREATED)
async def create_pix_withdrawal(
    withdrawal_data: WithdrawalPixRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cria saque via PIX usando Gatebox
    
    Args:
        withdrawal_data: Dados do saque (amount, pix_key, type_key, document_validation)
    """
    # Usar usuário autenticado
    user = current_user
    
    # Extrair dados do request
    amount = withdrawal_data.amount
    pix_key = withdrawal_data.pix_key
    type_key = withdrawal_data.type_key
    document_validation = withdrawal_data.document_validation
    
    # Verificar saldo sacável (apenas saldo real, não inclui bônus não sacável)
    # Saldo sacável = balance (que já inclui depósitos reais + bônus sacáveis + ganhos dos jogos)
    withdrawable_balance = user.balance  # balance já é o saldo sacável
    if withdrawable_balance < amount:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
    
    # Buscar configurações FTD para validar saque mínimo
    ftd_settings = db.query(FTDSettings).filter(FTDSettings.is_active == True).first()
    min_withdrawal = 10.0  # Valor padrão
    if ftd_settings and ftd_settings.min_withdrawal > 0:
        min_withdrawal = ftd_settings.min_withdrawal
    
    if amount < min_withdrawal:
        raise HTTPException(status_code=400, detail=f"Valor mínimo de saque é R$ {min_withdrawal:.2f}")
    
    # Validar chave PIX
    if not pix_key or not pix_key.strip():
        raise HTTPException(status_code=400, detail="Chave PIX é obrigatória")
    
    # Limpar chave PIX (remover espaços e caracteres especiais se necessário)
    pix_key_clean = pix_key.strip()
    
    # Se for telefone, garantir formato correto
    # A Gatebox espera formato: +55XXXXXXXXXXX (com + e código do país)
    if type_key == "TELEFONE":
        # Remover caracteres não numéricos
        pix_key_clean = ''.join(filter(str.isdigit, pix_key_clean))
        
        # Remover código do país se já estiver presente
        if pix_key_clean.startswith('55'):
            pix_key_clean = pix_key_clean[2:]
        
        # Validar tamanho do telefone (deve ter 10 ou 11 dígitos após remover código do país)
        if len(pix_key_clean) < 10 or len(pix_key_clean) > 11:
            raise HTTPException(
                status_code=400, 
                detail=f"Telefone inválido. Use o formato: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX"
            )
        
        # Formatar como +55XXXXXXXXXXX (com + e código do país)
        pix_key_clean = f"+55{pix_key_clean}"
        print(f"[WITHDRAWAL] Chave PIX (telefone) formatada: {pix_key_clean}")
    
    # Buscar gateway PIX ativo
    gateway = get_active_pix_gateway(db)
    
    # Criar cliente Gatebox
    gatebox = get_gatebox_client(gateway)
    
    # Gerar external_id único para controle de duplicidade
    external_id = f"WTH_{user.id}_{int(datetime.utcnow().timestamp())}"
    
    # Realizar transferência PIX
    # A Gatebox requer name (nome do recebedor) - usar nome completo se disponível
    # IMPORTANTE: Para chave PIX de telefone, o nome deve corresponder ao titular da conta bancária
    # Tentar usar um nome mais descritivo, mas se não houver, usar username
    # Se o username for um telefone, usar um nome genérico
    recipient_name = user.username or "Usuário"
    
    # Se o username for apenas números (telefone), usar um nome mais apropriado
    if recipient_name and re.match(r'^\d+$', recipient_name):
        # Username é apenas números, usar formato mais apropriado
        recipient_name = f"Cliente {user.id}" if user.id else "Usuário"
    
    # Se houver email, tentar extrair nome do email (se não for apenas números)
    if user.email and '@' in user.email:
        email_name = user.email.split('@')[0]
        if email_name and len(email_name) > 3 and not re.match(r'^\d+$', email_name):
            recipient_name = email_name
    
    # Log dos dados que serão enviados
    print(f"[WITHDRAWAL] Dados do saque:")
    print(f"  - External ID: {external_id}")
    print(f"  - Chave PIX: {pix_key_clean} (tipo: {type_key})")
    print(f"  - Nome: {recipient_name}")
    print(f"  - Valor: R$ {amount:.2f}")
    print(f"  - Documento (opcional): {document_validation or 'Não informado'}")
    
    try:
        transfer_response = await gatebox.withdraw_pix(
            external_id=external_id,
            key=pix_key_clean,
            name=recipient_name,
            amount=amount,
            document_number=document_validation,
            description=f"Saque de R$ {amount:.2f}"
        )
    except Exception as e:
        print(f"Erro ao chamar Gatebox withdraw_pix: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao processar transferência PIX: {str(e)}"
        )
    
    if not transfer_response:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erro ao processar transferência PIX no gateway"
        )
    
    # Verificar se houve erro na resposta da Gatebox
    if transfer_response.get("error"):
        error_detail = (
            transfer_response.get("detail") or 
            transfer_response.get("message") or 
            transfer_response.get("errorMessage") or
            "Erro ao processar saque"
        )
        status_code = transfer_response.get("status_code", 400)
        print(f"[WITHDRAWAL] ❌ Erro na resposta da Gatebox: {error_detail}")
        raise HTTPException(status_code=status_code, detail=error_detail)
    
    # Verificar se o status inicial indica problema
    actual_response = transfer_response
    if isinstance(transfer_response, dict):
        if "data" in transfer_response and isinstance(transfer_response["data"], dict):
            actual_response = transfer_response["data"]
        elif "result" in transfer_response and isinstance(transfer_response["result"], dict):
            actual_response = transfer_response["result"]
    
    # Verificar status inicial na resposta
    initial_status = actual_response.get("status", "").upper()
    if initial_status in ["FAILED", "REJECTED", "ERROR"]:
        error_msg = actual_response.get("message") or actual_response.get("error") or "Saque rejeitado pela Gatebox"
        print(f"[WITHDRAWAL] ⚠️ Status inicial indica falha: {initial_status} - {error_msg}")
        # Não bloquear aqui, pois o webhook pode atualizar depois, mas logar para investigação
    
    # A Gatebox pode retornar dados em diferentes estruturas
    # Verificar se há um campo "data" ou similar que contenha a resposta real
    actual_response = transfer_response
    if isinstance(transfer_response, dict):
        # Verificar se há um campo "data" que contenha a resposta real
        if "data" in transfer_response and isinstance(transfer_response["data"], dict):
            actual_response = transfer_response["data"]
        # Verificar se há um campo "result" que contenha a resposta real
        elif "result" in transfer_response and isinstance(transfer_response["result"], dict):
            actual_response = transfer_response["result"]
    
    # Log para debug
    print(f"Gatebox Withdrawal Response (raw): {json.dumps(transfer_response, indent=2)}")
    print(f"Gatebox Withdrawal Response (actual): {json.dumps(actual_response, indent=2)}")
    
    # Extrair transaction_id e end_to_end da resposta
    transaction_id_gatebox = (
        actual_response.get("transactionId") or 
        actual_response.get("id") or 
        actual_response.get("transaction_id") or
        actual_response.get("externalId") or
        ""
    )
    
    end_to_end = (
        actual_response.get("endToEnd") or 
        actual_response.get("end_to_end") or
        None
    )
    
    print(f"Extracted Transaction ID: {transaction_id_gatebox}")
    print(f"Extracted End-to-End: {end_to_end}")
    
    # Criar registro de saque
    withdrawal = Withdrawal(
        user_id=user.id,
        gateway_id=gateway.id,
        amount=amount,
        status=TransactionStatus.PENDING,
        transaction_id=transaction_id_gatebox or str(uuid.uuid4()),
        external_id=external_id,
        metadata_json=json.dumps({
            "pix_key": pix_key,
            "type_key": type_key,
            "document_validation": document_validation,
            "external_id": external_id,
            "transaction_id": transaction_id_gatebox,
            "end_to_end": end_to_end,
            "gatebox_response": actual_response,
            "gatebox_raw_response": transfer_response  # Manter resposta original para debug
        })
    )
    
    # Bloquear saldo do usuário
    user.balance -= amount
    
    db.add(withdrawal)
    db.commit()
    db.refresh(withdrawal)
    
    return withdrawal


# ========== WEBHOOKS ==========

@webhook_router.post("/gatebox")
async def webhook_gatebox(request: Request, db: Session = Depends(get_db)):
    """
    Webhook único para receber todas as notificações da Gatebox
    Esta é a URL que deve ser configurada no painel da Gatebox
    Todos os tipos de eventos (PIX_PAY_IN, PIX_PAY_OUT, etc.) apontam para esta mesma URL
    """
    try:
        # Tentar obter dados como JSON
        try:
            data = await request.json()
        except:
            # Se falhar, tentar como texto e fazer parse manual
            body = await request.body()
            try:
                data = json.loads(body.decode('utf-8'))
            except:
                data = {}
        
        # Log completo do webhook recebido
        print(f"[WEBHOOK] ========== WEBHOOK GATEBOX RECEBIDO ==========")
        print(f"[WEBHOOK] Headers: {dict(request.headers)}")
        print(f"[WEBHOOK] Raw data: {json.dumps(data, indent=2)}")
        
        # Verificar se os dados estão dentro de um campo "data" ou similar
        # A Gatebox pode enviar: {"statusCode": 200, "data": {...}} ou diretamente {...}
        original_data = data.copy()
        if "data" in data and isinstance(data["data"], dict):
            inner_data = data["data"]
            # Mesclar dados internos com dados externos (inner_data tem prioridade)
            data = {**data, **inner_data}
            print(f"[WEBHOOK] Dados extraídos do campo 'data': {json.dumps(inner_data, indent=2)}")
        
        # Identificar o tipo de evento - a Gatebox pode enviar o tipo de várias formas
        event_type = (
            data.get("eventType") or 
            data.get("event_type") or 
            data.get("type") or 
            data.get("event") or
            data.get("eventType") or  # Pode estar no nível superior
            original_data.get("eventType") or
            original_data.get("event_type") or
            request.headers.get("X-Event-Type") or  # Alguns sistemas enviam no header
            request.headers.get("X-Gatebox-Event-Type")
        )
        
        # Extrair status - pode estar no nível raiz ou dentro de transaction
        transaction_data = data.get("transaction") or {}
        status_transaction = (
            data.get("status") or 
            transaction_data.get("status") or
            data.get("statusTransaction") or 
            data.get("status_transaction") or
            original_data.get("status") or
            original_data.get("statusTransaction")
        )
        
        # Extrair external_id - pode estar no nível raiz ou dentro de transaction
        external_id = (
            data.get("externalId") or 
            data.get("external_id") or
            transaction_data.get("externalId") or
            transaction_data.get("external_id")
        )
        
        print(f"[WEBHOOK] Event type identificado: {event_type}")
        print(f"[WEBHOOK] Status: {status_transaction}")
        print(f"[WEBHOOK] External ID: {external_id}")
        print(f"[WEBHOOK] Dados finais processados: {json.dumps(data, indent=2)}")
        
        # Se não tiver eventType explícito, tentar identificar pelo contexto
        if not event_type:
            # Verificar se é depósito ou saque pelo external_id
            if external_id:
                deposit = db.query(Deposit).filter(Deposit.external_id == external_id).first()
                if deposit:
                    event_type = "PIX_PAY_IN"
                    print(f"[WEBHOOK] ✅ Identificado como PIX_PAY_IN pelo external_id: {external_id}")
                else:
                    withdrawal = db.query(Withdrawal).filter(Withdrawal.external_id == external_id).first()
                    if withdrawal:
                        event_type = "PIX_PAY_OUT"
                        print(f"[WEBHOOK] ✅ Identificado como PIX_PAY_OUT pelo external_id: {external_id}")
        
        # Processar conforme o tipo de evento
        result = None
        if event_type in ["PIX_PAY_IN", "pix_pay_in", "cashin", "cash-in", "PIX_CASH_IN"]:
            result = await _process_pix_cashin(data, db)
        elif event_type in ["PIX_PAY_OUT", "pix_pay_out", "cashout", "cash-out", "PIX_CASH_OUT"]:
            result = await _process_pix_cashout(data, db)
        elif event_type in ["PIX_REVERSAL", "pix_reversal"]:
            # Processar reversão de depósito
            print(f"[WEBHOOK] Processando PIX_REVERSAL")
            result = await _process_pix_cashin(data, db)  # Reversão pode ser tratada como cancelamento
        elif event_type in ["PIX_REVERSAL_OUT", "pix_reversal_out"]:
            # Processar reversão de saque
            print(f"[WEBHOOK] Processando PIX_REVERSAL_OUT")
            result = await _process_pix_cashout(data, db)
        elif event_type in ["PIX_REFUND", "pix_refund"]:
            # Processar estorno
            print(f"[WEBHOOK] Processando PIX_REFUND")
            result = await _process_pix_cashin(data, db)  # Estorno pode ser tratado como cancelamento
        else:
            # Tentar processar como depósito ou saque baseado nos dados
            print(f"[WEBHOOK] ⚠️ Tipo de evento não reconhecido ({event_type}), tentando processar como evento desconhecido")
            result = await _process_unknown_event(data, db)
        
        print(f"[WEBHOOK] ========== WEBHOOK PROCESSADO COM SUCESSO ==========")
        
        # Retornar sempre 200 OK para a Gatebox saber que recebemos o webhook
        return {"status": "ok", "message": "Webhook recebido e processado", "result": result}
    
    except Exception as e:
        import traceback
        print(f"[WEBHOOK] ❌ ERRO ao processar webhook Gatebox: {str(e)}")
        print(f"[WEBHOOK] Traceback: {traceback.format_exc()}")
        # Retornar 200 mesmo em caso de erro para evitar retentativas desnecessárias
        # Mas logar o erro para investigação
        return {"status": "error", "message": f"Erro ao processar webhook: {str(e)}"}


async def _process_pix_cashin(data: dict, db: Session):
    """Processa webhook de PIX Cash-in (depósito)"""
    # Buscar gateway PIX ativo
    gateway = get_active_pix_gateway(db)
    
    # Processar webhook
    external_id = data.get("externalId") or data.get("external_id")
    transaction_id = data.get("transactionId") or data.get("transaction_id") or data.get("id")
    uuid_gatebox = data.get("uuid")  # UUID retornado pela Gatebox
    status_transaction = data.get("status") or data.get("statusTransaction") or data.get("status_transaction")
    amount = data.get("amount") or data.get("value")
    end_to_end = data.get("endToEnd") or data.get("end_to_end")
    
    print(f"[WEBHOOK] Processando PIX Cash-in - external_id: {external_id}, uuid: {uuid_gatebox}, transaction_id: {transaction_id}, status: {status_transaction}")
    
    # Buscar depósito pelo external_id (mais confiável)
    deposit = None
    if external_id:
        deposit = db.query(Deposit).filter(Deposit.external_id == external_id).first()
        if deposit:
            print(f"[WEBHOOK] Depósito encontrado pelo external_id: {external_id}")
    
    # Se não encontrou pelo external_id, tentar pelo UUID no metadata
    if not deposit and uuid_gatebox:
        deposits = db.query(Deposit).filter(
            Deposit.status == TransactionStatus.PENDING
        ).all()
        for d in deposits:
            metadata = json.loads(d.metadata_json) if d.metadata_json else {}
            gatebox_response = metadata.get("gatebox_response") or {}
            if gatebox_response.get("uuid") == uuid_gatebox:
                deposit = d
                print(f"[WEBHOOK] Depósito encontrado pelo UUID: {uuid_gatebox}")
                break
    
    # Se ainda não encontrou, tentar pelo transaction_id no metadata
    if not deposit and transaction_id:
        deposits = db.query(Deposit).filter(
            Deposit.status == TransactionStatus.PENDING
        ).all()
        for d in deposits:
            metadata = json.loads(d.metadata_json) if d.metadata_json else {}
            if metadata.get("transaction_id") == transaction_id or metadata.get("end_to_end") == end_to_end:
                deposit = d
                print(f"[WEBHOOK] Depósito encontrado pelo transaction_id: {transaction_id}")
                break
    
    # Última tentativa: buscar todos os depósitos pendentes e verificar pelo identifier
    if not deposit:
        identifier = data.get("identifier")
        if identifier:
            deposits = db.query(Deposit).filter(
                Deposit.status == TransactionStatus.PENDING
            ).all()
            for d in deposits:
                metadata = json.loads(d.metadata_json) if d.metadata_json else {}
                gatebox_response = metadata.get("gatebox_response") or {}
                if gatebox_response.get("identifier") == identifier:
                    deposit = d
                    print(f"[WEBHOOK] Depósito encontrado pelo identifier: {identifier}")
                    break
    
    if not deposit:
        print(f"[WEBHOOK] Depósito não encontrado - external_id: {external_id}, transaction_id: {transaction_id}")
        return {"status": "ok", "message": "Depósito não encontrado"}
    
    print(f"[WEBHOOK] Depósito encontrado - ID: {deposit.id}, Status atual: {deposit.status.value}, Valor: {deposit.amount}")
    
    # Atualizar status do depósito
    status_upper = str(status_transaction).upper() if status_transaction else ""
    print(f"[WEBHOOK] Status recebido (uppercase): {status_upper}")
    
    # Aceitar mais variações de status de pagamento confirmado
    paid_statuses = ["PAID", "PAID_OUT", "CONFIRMED", "APPROVED", "SUCCESS", "COMPLETED", "SETTLED"]
    
    if status_upper in paid_statuses:
        if deposit.status != TransactionStatus.APPROVED:
            print(f"[WEBHOOK] Creditando saldo - Status mudando de {deposit.status.value} para APPROVED")
            deposit.status = TransactionStatus.APPROVED
            # Adicionar saldo ao usuário separando real e bônus
            user = db.query(User).filter(User.id == deposit.user_id).first()
            if user:
                old_balance = user.balance
                old_bonus_balance = user.bonus_balance
                
                # Extrair informações do metadata
                metadata = json.loads(deposit.metadata_json) if deposit.metadata_json else {}
                promotion_id = metadata.get("promotion_id")
                promotion_bonus = metadata.get("promotion_bonus", 0)
                coupon_bonus = metadata.get("coupon_bonus", 0)
                
                # Valor real depositado (sempre sacável)
                real_amount = deposit.amount
                user.balance += real_amount
                
                # Bônus total (cupom + promoção)
                total_bonus = deposit.bonus_amount
                
                # Verificar se os bônus são sacáveis
                withdrawable_bonus = 0.0
                non_withdrawable_bonus = 0.0
                
                if coupon_bonus > 0 and deposit.coupon_code:
                    coupon = db.query(Coupon).filter(Coupon.code == deposit.coupon_code).first()
                    if coupon:
                        if coupon.is_withdrawable:
                            withdrawable_bonus += coupon_bonus
                        else:
                            non_withdrawable_bonus += coupon_bonus
                        coupon.uses += 1
                        coupon_use = CouponUse(
                            coupon_id=coupon.id,
                            user_id=user.id,
                            deposit_id=deposit.id,
                            bonus_amount=coupon_bonus
                        )
                        db.add(coupon_use)
                        print(f"[WEBHOOK] Cupom aplicado - Código: {deposit.coupon_code}, Bônus: R$ {coupon_bonus:.2f}, Sacável: {coupon.is_withdrawable}")
                
                if promotion_bonus > 0 and promotion_id:
                    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
                    if promotion:
                        if promotion.is_withdrawable:
                            withdrawable_bonus += promotion_bonus
                        else:
                            non_withdrawable_bonus += promotion_bonus
                        promotion_use = PromotionUse(
                            promotion_id=promotion.id,
                            user_id=user.id,
                            deposit_id=deposit.id,
                            bonus_amount=promotion_bonus
                        )
                        db.add(promotion_use)
                        print(f"[WEBHOOK] Promoção aplicada - ID: {promotion.id}, Título: {promotion.title}, Bônus: R$ {promotion_bonus:.2f}, Sacável: {promotion.is_withdrawable}")
                
                # Adicionar bônus sacável ao saldo real
                user.balance += withdrawable_bonus
                
                # Adicionar bônus não sacável ao saldo de bônus
                user.bonus_balance += non_withdrawable_bonus
                
                # Verificar se é primeiro depósito (FTD) e criar registro
                is_first_deposit = metadata.get("is_first_deposit", False)
                existing_ftd = db.query(FTD).filter(FTD.user_id == user.id).first()
                
                if is_first_deposit and not existing_ftd:
                    # Criar FTD
                    ftd_settings = db.query(FTDSettings).filter(FTDSettings.is_active == True).first()
                    pass_rate = ftd_settings.pass_rate if ftd_settings else 0.0
                    
                    ftd = FTD(
                        user_id=user.id,
                        deposit_id=deposit.id,
                        amount=deposit.amount,
                        is_first_deposit=True,
                        pass_rate=pass_rate,
                        status=TransactionStatus.APPROVED
                    )
                    db.add(ftd)
                    db.flush()  # Flush para obter o ID do FTD
                    
                    # Processar CPA no primeiro depósito
                    try:
                        process_cpa_on_ftd(user.id, deposit.id, db)
                    except Exception as e:
                        print(f"[CPA] Erro ao processar CPA (não crítico): {str(e)}")
                
                # Processar revshare baseado em perdas (atualizar quando há mudança no saldo)
                try:
                    loss = calculate_user_loss(user.id, db)
                    if loss > 0:
                        # Simular aposta para atualizar revshare (valor da aposta não importa, só a perda)
                        process_revshare_on_bet(user.id, 0.0, 0.0, db)
                except Exception as e:
                    print(f"[REVSHARE] Erro ao processar revshare (não crítico): {str(e)}")
                
                print(f"[WEBHOOK] Saldo creditado - Usuário ID: {user.id}, Saldo anterior: {old_balance}, Saldo novo: {user.balance}, Bônus anterior: {old_bonus_balance}, Bônus novo: {user.bonus_balance}, Depósito: R$ {real_amount:.2f}, Bônus sacável: R$ {withdrawable_bonus:.2f}, Bônus não sacável: R$ {non_withdrawable_bonus:.2f}")
            else:
                print(f"[WEBHOOK] ERRO: Usuário não encontrado - user_id: {deposit.user_id}")
        else:
            print(f"[WEBHOOK] Depósito já estava aprovado, ignorando")
    elif status_upper in ["CANCELLED", "CANCELED", "REJECTED", "FAILED", "CHARGEBACK", "EXPIRED"]:
        print(f"[WEBHOOK] Cancelando depósito - Status: {status_upper}")
        if deposit.status == TransactionStatus.APPROVED:
            # Reverter saldo se já foi aprovado (depósito + bônus)
            user = db.query(User).filter(User.id == deposit.user_id).first()
            if user:
                # Extrair informações do metadata
                metadata = json.loads(deposit.metadata_json) if deposit.metadata_json else {}
                promotion_id = metadata.get("promotion_id")
                promotion_bonus = metadata.get("promotion_bonus", 0)
                coupon_bonus = metadata.get("coupon_bonus", 0)
                
                # Reverter valor real depositado
                real_amount = deposit.amount
                if user.balance >= real_amount:
                    old_balance = user.balance
                    user.balance -= real_amount
                    
                    # Reverter bônus sacável e não sacável separadamente
                    if coupon_bonus > 0 and deposit.coupon_code:
                        coupon = db.query(Coupon).filter(Coupon.code == deposit.coupon_code).first()
                        if coupon:
                            if coupon.is_withdrawable:
                                if user.balance >= coupon_bonus:
                                    user.balance -= coupon_bonus
                            else:
                                if user.bonus_balance >= coupon_bonus:
                                    user.bonus_balance -= coupon_bonus
                            if coupon.uses > 0:
                                coupon.uses -= 1
                        # Remover registro de uso
                        coupon_use = db.query(CouponUse).filter(
                            CouponUse.deposit_id == deposit.id
                        ).first()
                        if coupon_use:
                            db.delete(coupon_use)
                            print(f"[WEBHOOK] Uso de cupom revertido - Código: {deposit.coupon_code}")
                    
                    if promotion_bonus > 0 and promotion_id:
                        promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
                        if promotion:
                            if promotion.is_withdrawable:
                                if user.balance >= promotion_bonus:
                                    user.balance -= promotion_bonus
                            else:
                                if user.bonus_balance >= promotion_bonus:
                                    user.bonus_balance -= promotion_bonus
                        promotion_use = db.query(PromotionUse).filter(
                            PromotionUse.deposit_id == deposit.id
                        ).first()
                        if promotion_use:
                            db.delete(promotion_use)
                            print(f"[WEBHOOK] Uso de promoção revertido - ID: {promotion_id}")
                    
                    print(f"[WEBHOOK] Saldo revertido - Usuário ID: {user.id}, Saldo anterior: {old_balance}, Saldo novo: {user.balance}, Bônus novo: {user.bonus_balance}, Depósito revertido: R$ {real_amount:.2f}, Bônus revertido: R$ {deposit.bonus_amount:.2f}")
        deposit.status = TransactionStatus.CANCELLED
    else:
        print(f"[WEBHOOK] Status não reconhecido ou ainda pendente - Status: {status_upper}")
    
    # Atualizar metadata
    metadata = json.loads(deposit.metadata_json) if deposit.metadata_json else {}
    metadata["webhook_data"] = data
    metadata["webhook_received_at"] = datetime.utcnow().isoformat()
    metadata["webhook_status"] = status_transaction
    deposit.metadata_json = json.dumps(metadata)
    
    try:
        db.commit()
        print(f"[WEBHOOK] ✅ Depósito atualizado e commitado - ID: {deposit.id}, Novo status: {deposit.status.value}")
        
        # Disparar webhooks configurados para PIX_PAY_IN (não bloquear se falhar)
        try:
            await dispatch_webhook(
                db=db,
                event_type=WebhookEventType.PIX_PAY_IN,
                payload={
                    "event_type": "PIX_PAY_IN",
                    "deposit_id": deposit.id,
                    "user_id": deposit.user_id,
                    "amount": deposit.amount,
                    "status": deposit.status.value,
                    "transaction_id": deposit.transaction_id,
                    "external_id": deposit.external_id,
                    "end_to_end": end_to_end,
                    "gatebox_data": data
                }
            )
        except Exception as e:
            print(f"[WEBHOOK] ⚠️ Erro ao disparar webhook customizado (não crítico): {str(e)}")
        
        # Disparar eventos de tracking (primeiro depósito ou redepósito)
        if deposit.status == TransactionStatus.APPROVED:
            try:
                # Verificar se é primeiro depósito
                metadata = json.loads(deposit.metadata_json) if deposit.metadata_json else {}
                is_first_deposit = metadata.get("is_first_deposit", False)
                
                # Buscar dados do usuário
                user = db.query(User).filter(User.id == deposit.user_id).first()
                if user:
                    event_name = "first_deposit" if is_first_deposit else "redeposit"
                    await dispatch_tracking_event(
                        db=db,
                        event_name=event_name,
                        payload={
                            "user_id": user.id,
                            "email": user.email,
                            "phone": user.phone,
                            "amount": deposit.amount,
                            "deposit_id": deposit.id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "metadata": {
                                "transaction_id": deposit.transaction_id,
                                "external_id": deposit.external_id,
                                "bonus_amount": deposit.bonus_amount,
                                "coupon_code": deposit.coupon_code,
                                "is_first_deposit": is_first_deposit
                            }
                        }
                    )
            except Exception as e:
                print(f"[TRACKING] ⚠️ Erro ao disparar evento de tracking (não crítico): {str(e)}")
        
        return {
            "status": "ok", 
            "message": "Webhook processado com sucesso",
            "deposit_id": deposit.id,
            "deposit_status": deposit.status.value,
            "balance_credited": deposit.status == TransactionStatus.APPROVED
        }
    except Exception as e:
        db.rollback()
        print(f"[WEBHOOK] ❌ Erro ao commitar depósito: {str(e)}")
        raise


async def _process_pix_cashout(data: dict, db: Session):
    """Processa webhook de PIX Cash-out (saque)"""
    print(f"[WEBHOOK] ========== PROCESSANDO PIX CASHOUT ==========")
    print(f"[WEBHOOK] Data recebida: {json.dumps(data, indent=2)}")
    
    # Buscar gateway PIX ativo
    gateway = get_active_pix_gateway(db)
    
    # Processar webhook - verificar estrutura aninhada
    # A Gatebox pode enviar dados em data["transaction"] ou diretamente em data
    transaction_data = data.get("transaction") or data
    external_id = (
        transaction_data.get("externalId") or 
        transaction_data.get("external_id") or
        data.get("externalId") or 
        data.get("external_id")
    )
    transaction_id = (
        transaction_data.get("transactionId") or 
        transaction_data.get("transaction_id") or 
        transaction_data.get("id") or
        data.get("transactionId") or 
        data.get("transaction_id") or 
        data.get("id")
    )
    status_transaction = (
        data.get("status") or 
        transaction_data.get("status") or
        data.get("statusTransaction") or 
        data.get("status_transaction")
    )
    end_to_end = (
        data.get("endToEnd") or 
        data.get("end_to_end") or
        transaction_data.get("endToEnd") or 
        transaction_data.get("end_to_end")
    )
    
    # Extrair motivo da falha (se houver) - verificar em vários lugares
    failure_reason = (
        data.get("reason") or
        data.get("message") or
        data.get("error") or
        data.get("errorMessage") or
        data.get("failureReason") or
        data.get("detail") or
        data.get("description") or
        transaction_data.get("reason") or
        transaction_data.get("message") or
        transaction_data.get("error") or
        transaction_data.get("errorMessage")
    )
    
    # Verificar também em bankData e invoice
    bank_data = data.get("bankData") or {}
    invoice_data = data.get("invoice") or {}
    
    if not failure_reason:
        failure_reason = (
            bank_data.get("error") or
            bank_data.get("message") or
            bank_data.get("reason") or
            invoice_data.get("error") or
            invoice_data.get("message")
        )
    
    # Tentar extrair erro de campos aninhados
    if not failure_reason and isinstance(data, dict):
        # Procurar por campos de erro em qualquer nível
        for key, value in data.items():
            if isinstance(value, dict):
                error_msg = value.get("error") or value.get("message") or value.get("reason")
                if error_msg:
                    failure_reason = error_msg
                    break
    
    print(f"[WEBHOOK] External ID extraído: {external_id}")
    print(f"[WEBHOOK] Transaction ID extraído: {transaction_id}")
    print(f"[WEBHOOK] Status extraído: {status_transaction}")
    print(f"[WEBHOOK] Motivo da falha (se houver): {failure_reason}")
    
    # Se não encontrou motivo, tentar buscar na resposta completa
    if not failure_reason and status_transaction == "FAILED":
        print(f"[WEBHOOK] ⚠️ Status FAILED mas motivo não encontrado. Dados completos: {json.dumps(data, indent=2)}")
    
    # Buscar saque pelo external_id
    withdrawal = None
    if external_id:
        withdrawal = db.query(Withdrawal).filter(Withdrawal.external_id == external_id).first()
        if withdrawal:
            print(f"[WEBHOOK] Saque encontrado pelo external_id: {external_id}, ID: {withdrawal.id}")
    
    # Se não encontrou pelo external_id, tentar pelo transaction_id no metadata
    if not withdrawal and transaction_id:
        withdrawals = db.query(Withdrawal).filter(
            Withdrawal.status == TransactionStatus.PENDING
        ).all()
        for w in withdrawals:
            metadata = json.loads(w.metadata_json) if w.metadata_json else {}
            gatebox_response = metadata.get("gatebox_response") or {}
            if (metadata.get("transaction_id") == transaction_id or 
                gatebox_response.get("transactionId") == transaction_id or
                gatebox_response.get("uuid") == transaction_id or
                metadata.get("end_to_end") == end_to_end):
                withdrawal = w
                print(f"[WEBHOOK] Saque encontrado pelo transaction_id/uuid: {transaction_id}, ID: {withdrawal.id}")
                break
    
    if not withdrawal:
        print(f"[WEBHOOK] ❌ Saque não encontrado - external_id: {external_id}, transaction_id: {transaction_id}")
        return {"status": "ok", "message": "Saque não encontrado"}
    
    print(f"[WEBHOOK] Saque encontrado - ID: {withdrawal.id}, Status atual: {withdrawal.status.value}, Valor: {withdrawal.amount}")
    
    # Atualizar status do saque
    status_upper = str(status_transaction).upper() if status_transaction else ""
    print(f"[WEBHOOK] Status processado (uppercase): {status_upper}")
    
    # Status de sucesso
    success_statuses = ["PAID", "PAID_OUT", "CONFIRMED", "APPROVED", "SUCCESS", "COMPLETED", "SETTLED"]
    # Status de falha
    failed_statuses = ["CANCELLED", "CANCELED", "REJECTED", "FAILED", "CHARGEBACK", "EXPIRED"]
    
    if status_upper in success_statuses:
        print(f"[WEBHOOK] ✅ Saque aprovado - Status: {status_upper}")
        withdrawal.status = TransactionStatus.APPROVED
    elif status_upper in failed_statuses:
        print(f"[WEBHOOK] ❌ Saque falhou - Status: {status_upper}")
        if failure_reason:
            print(f"[WEBHOOK] Motivo da falha: {failure_reason}")
        print(f"[WEBHOOK] Revertendo saldo...")
        # Reverter saldo quando o saque falha (o saldo foi bloqueado na criação)
        user = db.query(User).filter(User.id == withdrawal.user_id).first()
        if user:
            old_balance = user.balance
            user.balance += withdrawal.amount
            print(f"[WEBHOOK] Saldo revertido - Usuário ID: {user.id}, Saldo anterior: {old_balance}, Saldo novo: {user.balance}, Valor revertido: {withdrawal.amount}")
        else:
            print(f"[WEBHOOK] ERRO: Usuário não encontrado - user_id: {withdrawal.user_id}")
        withdrawal.status = TransactionStatus.REJECTED
    else:
        print(f"[WEBHOOK] ⚠️ Status não reconhecido ou ainda pendente - Status: {status_upper}")
    
    # Atualizar metadata
    metadata = json.loads(withdrawal.metadata_json) if withdrawal.metadata_json else {}
    metadata["webhook_data"] = data
    metadata["webhook_received_at"] = datetime.utcnow().isoformat()
    metadata["webhook_status"] = status_transaction
    if failure_reason:
        metadata["failure_reason"] = failure_reason
    withdrawal.metadata_json = json.dumps(metadata)
    
    try:
        db.commit()
        print(f"[WEBHOOK] ✅ Saque atualizado e commitado - ID: {withdrawal.id}, Novo status: {withdrawal.status.value}")
        
        # Disparar webhooks configurados para PIX_PAY_OUT (não bloquear se falhar)
        try:
            await dispatch_webhook(
                db=db,
                event_type=WebhookEventType.PIX_PAY_OUT,
                payload={
                    "event_type": "PIX_PAY_OUT",
                    "withdrawal_id": withdrawal.id,
                    "user_id": withdrawal.user_id,
                    "amount": withdrawal.amount,
                    "status": withdrawal.status.value,
                    "transaction_id": withdrawal.transaction_id,
                    "external_id": withdrawal.external_id,
                    "end_to_end": end_to_end,
                    "gatebox_data": data
                }
            )
        except Exception as e:
            print(f"[WEBHOOK] ⚠️ Erro ao disparar webhook customizado (não crítico): {str(e)}")
        
        return {
            "status": "ok", 
            "message": "Webhook processado com sucesso",
            "withdrawal_id": withdrawal.id,
            "withdrawal_status": withdrawal.status.value,
            "balance_reverted": status_upper in failed_statuses
        }
    except Exception as e:
        db.rollback()
        print(f"[WEBHOOK] ❌ Erro ao commitar saque: {str(e)}")
        raise


async def _process_unknown_event(data: dict, db: Session):
    """Tenta processar evento desconhecido como depósito ou saque"""
    # Tentar como depósito primeiro
    result = await _process_pix_cashin(data, db)
    if "não encontrado" not in result.get("message", "").lower():
        return result
    
    # Se não encontrou depósito, tentar como saque
    return await _process_pix_cashout(data, db)


# Manter rotas antigas para compatibilidade (deprecated)
@webhook_router.post("/gatebox/pix-cashin")
async def webhook_pix_cashin(request: Request, db: Session = Depends(get_db)):
    """
    Webhook para receber notificações de PIX Cash-in (depósitos) da Gatebox
    Nota: A validação de webhook da Gatebox pode variar - ajustar conforme documentação oficial
    """
    try:
        data = await request.json()
        
        # Buscar gateway PIX ativo
        gateway = get_active_pix_gateway(db)
        
        # Processar webhook
        # A Gatebox pode usar diferentes campos - ajustar conforme resposta real
        external_id = data.get("externalId") or data.get("external_id")
        transaction_id = data.get("transactionId") or data.get("transaction_id") or data.get("id")
        status_transaction = data.get("status") or data.get("statusTransaction") or data.get("status_transaction")
        amount = data.get("amount") or data.get("value")
        end_to_end = data.get("endToEnd") or data.get("end_to_end")
        
        # Buscar depósito pelo external_id
        deposit = None
        if external_id:
            deposit = db.query(Deposit).filter(Deposit.external_id == external_id).first()
        
        # Se não encontrou pelo external_id, tentar pelo transaction_id no metadata
        if not deposit and transaction_id:
            deposits = db.query(Deposit).filter(
                Deposit.status == TransactionStatus.PENDING
            ).all()
            for d in deposits:
                metadata = json.loads(d.metadata_json) if d.metadata_json else {}
                if metadata.get("transaction_id") == transaction_id or metadata.get("end_to_end") == end_to_end:
                    deposit = d
                    break
        
        if not deposit:
            return {"status": "ok", "message": "Depósito não encontrado"}
        
        # Atualizar status do depósito
        # A Gatebox pode usar diferentes valores de status - ajustar conforme documentação
        status_upper = str(status_transaction).upper() if status_transaction else ""
        
        if status_upper in ["PAID", "PAID_OUT", "CONFIRMED", "APPROVED", "SUCCESS"]:
            if deposit.status != TransactionStatus.APPROVED:
                deposit.status = TransactionStatus.APPROVED
                # Adicionar saldo ao usuário separando real e bônus (mesma lógica do webhook principal)
                user = db.query(User).filter(User.id == deposit.user_id).first()
                if user:
                    # Extrair informações do metadata
                    metadata = json.loads(deposit.metadata_json) if deposit.metadata_json else {}
                    promotion_id = metadata.get("promotion_id")
                    promotion_bonus = metadata.get("promotion_bonus", 0)
                    coupon_bonus = metadata.get("coupon_bonus", 0)
                    
                    # Valor real depositado (sempre sacável)
                    real_amount = deposit.amount
                    user.balance += real_amount
                    
                    # Verificar se os bônus são sacáveis
                    withdrawable_bonus = 0.0
                    non_withdrawable_bonus = 0.0
                    
                    if coupon_bonus > 0 and deposit.coupon_code:
                        coupon = db.query(Coupon).filter(Coupon.code == deposit.coupon_code).first()
                        if coupon:
                            if coupon.is_withdrawable:
                                withdrawable_bonus += coupon_bonus
                            else:
                                non_withdrawable_bonus += coupon_bonus
                            coupon.uses += 1
                            coupon_use = CouponUse(
                                coupon_id=coupon.id,
                                user_id=user.id,
                                deposit_id=deposit.id,
                                bonus_amount=coupon_bonus
                            )
                            db.add(coupon_use)
                    
                    if promotion_bonus > 0 and promotion_id:
                        promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
                        if promotion:
                            if promotion.is_withdrawable:
                                withdrawable_bonus += promotion_bonus
                            else:
                                non_withdrawable_bonus += promotion_bonus
                            promotion_use = PromotionUse(
                                promotion_id=promotion.id,
                                user_id=user.id,
                                deposit_id=deposit.id,
                                bonus_amount=promotion_bonus
                            )
                            db.add(promotion_use)
                    
                    # Adicionar bônus sacável ao saldo real
                    user.balance += withdrawable_bonus
                    
                    # Adicionar bônus não sacável ao saldo de bônus
                    user.bonus_balance += non_withdrawable_bonus
        elif status_upper in ["CANCELLED", "CANCELED", "REJECTED", "FAILED", "CHARGEBACK"]:
            if deposit.status == TransactionStatus.APPROVED:
                # Reverter saldo se já foi aprovado (mesma lógica do webhook principal)
                user = db.query(User).filter(User.id == deposit.user_id).first()
                if user:
                    # Extrair informações do metadata
                    metadata = json.loads(deposit.metadata_json) if deposit.metadata_json else {}
                    promotion_id = metadata.get("promotion_id")
                    promotion_bonus = metadata.get("promotion_bonus", 0)
                    coupon_bonus = metadata.get("coupon_bonus", 0)
                    
                    # Reverter valor real depositado
                    real_amount = deposit.amount
                    if user.balance >= real_amount:
                        user.balance -= real_amount
                        
                        # Reverter bônus sacável e não sacável separadamente
                        if coupon_bonus > 0 and deposit.coupon_code:
                            coupon = db.query(Coupon).filter(Coupon.code == deposit.coupon_code).first()
                            if coupon:
                                if coupon.is_withdrawable:
                                    if user.balance >= coupon_bonus:
                                        user.balance -= coupon_bonus
                                else:
                                    if user.bonus_balance >= coupon_bonus:
                                        user.bonus_balance -= coupon_bonus
                                if coupon.uses > 0:
                                    coupon.uses -= 1
                            # Remover registro de uso
                            coupon_use = db.query(CouponUse).filter(
                                CouponUse.deposit_id == deposit.id
                            ).first()
                            if coupon_use:
                                db.delete(coupon_use)
                        
                        # Reverter uso da promoção se houver
                        if promotion_bonus > 0 and promotion_id:
                            promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
                            if promotion:
                                if promotion.is_withdrawable:
                                    if user.balance >= promotion_bonus:
                                        user.balance -= promotion_bonus
                                else:
                                    if user.bonus_balance >= promotion_bonus:
                                        user.bonus_balance -= promotion_bonus
                            promotion_use = db.query(PromotionUse).filter(
                                PromotionUse.deposit_id == deposit.id
                            ).first()
                            if promotion_use:
                                db.delete(promotion_use)
            deposit.status = TransactionStatus.CANCELLED
        
        # Atualizar metadata
        metadata = json.loads(deposit.metadata_json) if deposit.metadata_json else {}
        metadata["webhook_data"] = data
        metadata["webhook_received_at"] = datetime.utcnow().isoformat()
        deposit.metadata_json = json.dumps(metadata)
        
        db.commit()
        
        return {"status": "ok", "message": "Webhook processado com sucesso"}
    
    except Exception as e:
        print(f"Erro ao processar webhook PIX Cash-in: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar webhook: {str(e)}")


@webhook_router.post("/gatebox/pix-cashout")
async def webhook_pix_cashout(request: Request, db: Session = Depends(get_db)):
    """
    Webhook para receber notificações de PIX Cash-out (saques) da Gatebox
    Nota: A validação de webhook da Gatebox pode variar - ajustar conforme documentação oficial
    """
    try:
        data = await request.json()
        
        # Buscar gateway PIX ativo
        gateway = get_active_pix_gateway(db)
        
        # Processar webhook
        external_id = data.get("externalId") or data.get("external_id")
        transaction_id = data.get("transactionId") or data.get("transaction_id") or data.get("id")
        status_transaction = data.get("status") or data.get("statusTransaction") or data.get("status_transaction")
        end_to_end = data.get("endToEnd") or data.get("end_to_end")
        
        # Buscar saque pelo external_id
        withdrawal = None
        if external_id:
            withdrawal = db.query(Withdrawal).filter(Withdrawal.external_id == external_id).first()
        
        # Se não encontrou pelo external_id, tentar pelo transaction_id no metadata
        if not withdrawal and transaction_id:
            withdrawals = db.query(Withdrawal).filter(
                Withdrawal.status == TransactionStatus.PENDING
            ).all()
            for w in withdrawals:
                metadata = json.loads(w.metadata_json) if w.metadata_json else {}
                if metadata.get("transaction_id") == transaction_id or metadata.get("end_to_end") == end_to_end:
                    withdrawal = w
                    break
        
        if not withdrawal:
            return {"status": "ok", "message": "Saque não encontrado"}
        
        # Atualizar status do saque
        status_upper = str(status_transaction).upper() if status_transaction else ""
        
        if status_upper in ["PAID", "PAID_OUT", "CONFIRMED", "APPROVED", "SUCCESS"]:
            withdrawal.status = TransactionStatus.APPROVED
        elif status_upper in ["CANCELLED", "CANCELED", "REJECTED", "FAILED"]:
            # Reverter saldo se foi cancelado
            if withdrawal.status == TransactionStatus.PENDING:
                user = db.query(User).filter(User.id == withdrawal.user_id).first()
                if user:
                    user.balance += withdrawal.amount
            withdrawal.status = TransactionStatus.CANCELLED
        
        # Atualizar metadata
        metadata = json.loads(withdrawal.metadata_json) if withdrawal.metadata_json else {}
        metadata["webhook_data"] = data
        metadata["webhook_received_at"] = datetime.utcnow().isoformat()
        withdrawal.metadata_json = json.dumps(metadata)
        
        db.commit()
        
        # Disparar webhooks configurados para PIX_PAY_OUT
        await dispatch_webhook(
            db=db,
            event_type=WebhookEventType.PIX_PAY_OUT,
            payload={
                "event_type": "PIX_PAY_OUT",
                "withdrawal_id": withdrawal.id,
                "user_id": withdrawal.user_id,
                "amount": withdrawal.amount,
                "status": withdrawal.status.value,
                "transaction_id": withdrawal.transaction_id,
                "external_id": withdrawal.external_id,
                "end_to_end": end_to_end,
                "gatebox_data": data
            }
        )
        
        return {"status": "ok", "message": "Webhook processado com sucesso"}
    
    except Exception as e:
        print(f"Erro ao processar webhook PIX Cash-out: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar webhook: {str(e)}")


# ========== ENDPOINTS PÚBLICOS PARA HISTÓRICO DO USUÁRIO ==========

@router.get("/my-deposits", response_model=List[DepositResponse])
async def get_my_deposits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Buscar depósitos do usuário logado"""
    deposits = db.query(Deposit).filter(
        Deposit.user_id == current_user.id
    ).order_by(desc(Deposit.created_at)).all()
    return deposits


@router.get("/my-withdrawals", response_model=List[WithdrawalResponse])
async def get_my_withdrawals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Buscar saques do usuário logado"""
    withdrawals = db.query(Withdrawal).filter(
        Withdrawal.user_id == current_user.id
    ).order_by(desc(Withdrawal.created_at)).all()
    return withdrawals


@router.get("/my-bets")
async def get_my_bets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Buscar apostas do usuário logado"""
    bets = db.query(Bet).filter(
        Bet.user_id == current_user.id
    ).order_by(desc(Bet.created_at)).all()
    
    return [
        {
            "id": bet.id,
            "game_id": bet.game_id,
            "game_name": bet.game_name,
            "provider": bet.provider,
            "amount": bet.amount,
            "win_amount": bet.win_amount,
            "status": bet.status.value,
            "transaction_id": bet.transaction_id,
            "created_at": bet.created_at.isoformat(),
            "updated_at": bet.updated_at.isoformat(),
        }
        for bet in bets
    ]


@router.get("/my-notifications")
async def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Buscar notificações do usuário logado (globais + pessoais)"""
    notifications = db.query(Notification).filter(
        Notification.is_active == True,
        or_(
            Notification.user_id == current_user.id,  # Notificações pessoais
            Notification.user_id == None  # Notificações globais
        )
    ).order_by(desc(Notification.created_at)).limit(50).all()
    
    return [
        {
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "type": notif.type.value,
            "is_read": notif.is_read,
            "link": notif.link,
            "created_at": notif.created_at.isoformat(),
        }
        for notif in notifications
    ]


@router.put("/my-notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marcar notificação como lida"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.is_active == True,
        or_(
            Notification.user_id == current_user.id,
            Notification.user_id == None
        )
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    
    notification.is_read = True
    db.commit()
    
    return {"success": True, "message": "Notificação marcada como lida"}


@router.put("/my-notifications/read-all")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marcar todas as notificações do usuário como lidas"""
    notifications = db.query(Notification).filter(
        Notification.is_active == True,
        Notification.is_read == False,
        or_(
            Notification.user_id == current_user.id,
            Notification.user_id == None
        )
    ).all()
    
    for notif in notifications:
        notif.is_read = True
    
    db.commit()
    
    return {"success": True, "count": len(notifications)}


# ========== COUPON VALIDATION ==========
def validate_and_calculate_coupon_bonus(
    coupon_code: str,
    deposit_amount: float,
    user_id: int,
    db: Session
) -> tuple[Optional[Coupon], float, str]:
    """
    Valida cupom e calcula o valor do bônus
    
    Returns:
        (coupon, bonus_amount, error_message)
        Se cupom válido: (coupon, bonus_amount, "")
        Se inválido: (None, 0.0, error_message)
    """
    if not coupon_code or not coupon_code.strip():
        return None, 0.0, ""
    
    coupon_code = coupon_code.strip().upper()
    
    # Buscar cupom
    coupon = db.query(Coupon).filter(
        Coupon.code == coupon_code,
        Coupon.is_active == True
    ).first()
    
    if not coupon:
        return None, 0.0, "Cupom não encontrado ou inválido"
    
    # Verificar validade
    now = datetime.utcnow()
    if coupon.valid_from > now:
        return None, 0.0, f"Cupom ainda não está válido. Válido a partir de {coupon.valid_from.strftime('%d/%m/%Y')}"
    
    if coupon.valid_until < now:
        return None, 0.0, f"Cupom expirado. Válido até {coupon.valid_until.strftime('%d/%m/%Y')}"
    
    # Verificar depósito mínimo
    if deposit_amount < coupon.min_deposit_amount:
        return None, 0.0, f"Depósito mínimo de R$ {coupon.min_deposit_amount:.2f} para usar este cupom"
    
    # Verificar limite de usos
    if coupon.max_uses is not None and coupon.uses >= coupon.max_uses:
        return None, 0.0, "Cupom esgotado (limite de usos atingido)"
    
    # Verificar se usuário já usou este cupom
    existing_use = db.query(CouponUse).filter(
        CouponUse.coupon_id == coupon.id,
        CouponUse.user_id == user_id
    ).first()
    
    if existing_use:
        return None, 0.0, "Você já usou este cupom anteriormente"
    
    # Calcular bônus
    if coupon.type == "percentage":
        bonus_amount = (deposit_amount * coupon.value) / 100
    else:  # fixed
        bonus_amount = coupon.value
    
    # Aplicar limite máximo de bônus se existir
    if coupon.max_bonus_amount is not None and bonus_amount > coupon.max_bonus_amount:
        bonus_amount = coupon.max_bonus_amount
    
    return coupon, bonus_amount, ""


@router.post("/validate-coupon")
async def validate_coupon(
    request: CouponValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validar cupom e retornar valor do bônus"""
    coupon, bonus_amount, error = validate_and_calculate_coupon_bonus(
        request.code, request.deposit_amount, current_user.id, db
    )
    
    if error:
        return {
            "valid": False,
            "bonus_amount": 0.0,
            "message": error
        }
    
    return {
        "valid": True,
        "coupon": CouponResponse.model_validate(coupon),
        "bonus_amount": bonus_amount,
        "message": f"Cupom válido! Bônus de R$ {bonus_amount:.2f}"
    }
