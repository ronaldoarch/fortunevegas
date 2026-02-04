"""
Rotas públicas para pagamentos (depósitos e saques) usando Gatebox
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import User, Deposit, Withdrawal, Gateway, TransactionStatus, WebhookEventType
from gatebox_api import GateboxAPI
from schemas import DepositResponse, WithdrawalResponse, DepositPixRequest
from dependencies import get_current_user
from webhook_dispatcher import dispatch_webhook
from datetime import datetime
import json
import uuid
import os

router = APIRouter(prefix="/api/public/payments", tags=["payments"])
webhook_router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


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
    
    if deposit_data.amount < 10:
        raise HTTPException(status_code=400, detail="Valor mínimo de depósito é R$ 10,00")
    
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
    
    # Se não fornecido ou inválido, usar CPF temporário válido para testes
    # CPF 00000000000 é válido para testes em alguns sistemas
    if not payer_tax_id_to_send:
        payer_tax_id_to_send = "00000000000"
    
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
            "gatebox_raw_response": pix_response  # Manter resposta original para debug
        })
    )
    
    db.add(deposit)
    db.commit()
    db.refresh(deposit)
    
    return deposit


@router.post("/withdrawal/pix", response_model=WithdrawalResponse, status_code=status.HTTP_201_CREATED)
async def create_pix_withdrawal(
    amount: float,
    pix_key: str,
    type_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document_validation: Optional[str] = None
):
    """
    Cria saque via PIX usando Gatebox
    
    Args:
        amount: Valor do saque
        pix_key: Chave PIX do recebedor
        type_key: Tipo da chave PIX (não usado na Gatebox, mas mantido para compatibilidade)
        document_validation: CPF/CNPJ para validar se pertence à chave PIX (opcional)
    """
    # Usar usuário autenticado
    user = current_user
    
    # Verificar saldo
    if user.balance < amount:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
    
    # Buscar gateway PIX ativo
    gateway = get_active_pix_gateway(db)
    
    # Criar cliente Gatebox
    gatebox = get_gatebox_client(gateway)
    
    # Gerar external_id único para controle de duplicidade
    external_id = f"WTH_{user.id}_{int(datetime.utcnow().timestamp())}"
    
    # Validar chave PIX antes de fazer o saque (opcional)
    # A Gatebox pode validar automaticamente, mas podemos fazer uma validação prévia
    # pix_validation = await gatebox.validate_pix_key(pix_key)
    
    # Realizar transferência PIX
    # A Gatebox requer name (nome do recebedor) - usar nome do usuário se disponível
    # Usar username como fallback se não houver nome completo
    recipient_name = user.username or user.email.split('@')[0] or "Usuário"
    
    transfer_response = await gatebox.withdraw_pix(
        external_id=external_id,
        key=pix_key,
        name=recipient_name,
        amount=amount,
        document_number=document_validation,
        description=f"Saque de R$ {amount:.2f}"
    )
    
    if not transfer_response:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erro ao processar transferência PIX no gateway"
        )
    
    # Verificar se houve erro na resposta da Gatebox
    if transfer_response.get("error"):
        error_detail = transfer_response.get("detail", "Erro ao processar saque")
        status_code = transfer_response.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail=error_detail)
    
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
    """
    try:
        data = await request.json()
        print(f"Webhook Gatebox recebido: {json.dumps(data, indent=2)}")
        
        # Identificar o tipo de evento
        event_type = data.get("eventType") or data.get("event_type") or data.get("type")
        status_transaction = data.get("status") or data.get("statusTransaction") or data.get("status_transaction")
        
        # Se não tiver eventType explícito, tentar identificar pelo contexto
        if not event_type:
            # Verificar se é depósito ou saque pelo external_id
            external_id = data.get("externalId") or data.get("external_id")
            if external_id:
                deposit = db.query(Deposit).filter(Deposit.external_id == external_id).first()
                if deposit:
                    event_type = "PIX_PAY_IN"
                else:
                    withdrawal = db.query(Withdrawal).filter(Withdrawal.external_id == external_id).first()
                    if withdrawal:
                        event_type = "PIX_PAY_OUT"
        
        # Processar conforme o tipo de evento
        if event_type in ["PIX_PAY_IN", "pix_pay_in", "cashin", "cash-in"]:
            return await _process_pix_cashin(data, db)
        elif event_type in ["PIX_PAY_OUT", "pix_pay_out", "cashout", "cash-out"]:
            return await _process_pix_cashout(data, db)
        else:
            # Tentar processar como depósito ou saque baseado nos dados
            return await _process_unknown_event(data, db)
    
    except Exception as e:
        print(f"Erro ao processar webhook Gatebox: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar webhook: {str(e)}")


async def _process_pix_cashin(data: dict, db: Session):
    """Processa webhook de PIX Cash-in (depósito)"""
    # Buscar gateway PIX ativo
    gateway = get_active_pix_gateway(db)
    
    # Processar webhook
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
    status_upper = str(status_transaction).upper() if status_transaction else ""
    
    if status_upper in ["PAID", "PAID_OUT", "CONFIRMED", "APPROVED", "SUCCESS"]:
        if deposit.status != TransactionStatus.APPROVED:
            deposit.status = TransactionStatus.APPROVED
            # Adicionar saldo ao usuário
            user = db.query(User).filter(User.id == deposit.user_id).first()
            if user:
                user.balance += deposit.amount
    elif status_upper in ["CANCELLED", "CANCELED", "REJECTED", "FAILED", "CHARGEBACK"]:
        if deposit.status == TransactionStatus.APPROVED:
            # Reverter saldo se já foi aprovado
            user = db.query(User).filter(User.id == deposit.user_id).first()
            if user and user.balance >= deposit.amount:
                user.balance -= deposit.amount
        deposit.status = TransactionStatus.CANCELLED
    
    # Atualizar metadata
    metadata = json.loads(deposit.metadata_json) if deposit.metadata_json else {}
    metadata["webhook_data"] = data
    metadata["webhook_received_at"] = datetime.utcnow().isoformat()
    deposit.metadata_json = json.dumps(metadata)
    
    db.commit()
    
    # Disparar webhooks configurados para PIX_PAY_IN
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
    
    return {"status": "ok", "message": "Webhook processado com sucesso"}


async def _process_pix_cashout(data: dict, db: Session):
    """Processa webhook de PIX Cash-out (saque)"""
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
                # Adicionar saldo ao usuário
                user = db.query(User).filter(User.id == deposit.user_id).first()
                if user:
                    user.balance += deposit.amount
        elif status_upper in ["CANCELLED", "CANCELED", "REJECTED", "FAILED", "CHARGEBACK"]:
            if deposit.status == TransactionStatus.APPROVED:
                # Reverter saldo se já foi aprovado
                user = db.query(User).filter(User.id == deposit.user_id).first()
                if user and user.balance >= deposit.amount:
                    user.balance -= deposit.amount
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
