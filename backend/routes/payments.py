"""
Rotas públicas para pagamentos (depósitos e saques) usando SuitPay
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import User, Deposit, Withdrawal, Gateway, TransactionStatus
from suitpay_api import SuitPayAPI
from schemas import DepositResponse, WithdrawalResponse, DepositPixRequest
from dependencies import get_current_user
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


def get_suitpay_client(gateway: Gateway) -> SuitPayAPI:
    """Cria cliente SuitPay a partir das credenciais do gateway"""
    try:
        credentials = json.loads(gateway.credentials) if gateway.credentials else {}
        client_id = credentials.get("client_id") or credentials.get("ci")
        client_secret = credentials.get("client_secret") or credentials.get("cs")
        sandbox = credentials.get("sandbox", True)
        
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Credenciais do gateway não configuradas"
            )
        
        return SuitPayAPI(client_id, client_secret, sandbox=sandbox)
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
    Cria depósito via PIX usando SuitPay
    
    Args:
        deposit_data: Dados do depósito (amount, payer_name, payer_tax_id)
    """
    # Usar usuário autenticado
    user = current_user
    
    if deposit_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
    
    # Buscar gateway PIX ativo
    gateway = get_active_pix_gateway(db)
    
    # Criar cliente SuitPay
    suitpay = get_suitpay_client(gateway)
    
    # Gerar número único da requisição
    request_number = f"DEP_{user.id}_{int(datetime.utcnow().timestamp())}"
    
    # URL do webhook (usar variável de ambiente ou construir)
    webhook_url = os.getenv("WEBHOOK_BASE_URL", "https://api.agenciamidas.com")
    url_callback = f"{webhook_url}/api/webhooks/suitpay/pix-cashin"
    
    # Validar CPF antes de enviar
    if not deposit_data.payer_tax_id or len(deposit_data.payer_tax_id.replace('.', '').replace('-', '').replace(' ', '')) < 11:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF/CNPJ inválido"
        )
    
    # Gerar código PIX
    pix_response = await suitpay.generate_pix_payment(
        value=deposit_data.amount,
        payer_name=deposit_data.payer_name,
        payer_tax_id=deposit_data.payer_tax_id,
        payer_email=user.email or "",
        request_number=request_number,
        url_callback=url_callback,
        payer_phone=user.phone
    )
    
    if not pix_response:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erro ao gerar código PIX no gateway. Verifique as credenciais e tente novamente."
        )
    
    # Criar registro de depósito
    deposit = Deposit(
        user_id=user.id,
        gateway_id=gateway.id,
        amount=deposit_data.amount,
        status=TransactionStatus.PENDING,
        transaction_id=str(uuid.uuid4()),
        external_id=pix_response.get("idTransaction") or request_number,
        metadata_json=json.dumps({
            "pix_code": pix_response.get("paymentCode"),
            "pix_qr_code": pix_response.get("paymentCode"),  # paymentCode é o QR Code
            "pix_qr_code_base64": pix_response.get("paymentCodeBase64"),
            "request_number": request_number,
            "suitpay_response": pix_response
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
    Cria saque via PIX usando SuitPay
    
    Args:
        amount: Valor do saque
        pix_key: Chave PIX (CPF, CNPJ, telefone, email ou chave aleatória)
        type_key: Tipo da chave PIX: "document", "phoneNumber", "email", "randomKey", "paymentCode"
        document_validation: CPF/CNPJ para validar se pertence à chave PIX (opcional)
    """
    # Usar usuário autenticado
    user = current_user
    
    # Verificar saldo
    if user.balance < amount:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
    
    # Validar tipo de chave
    valid_types = ["document", "phoneNumber", "email", "randomKey", "paymentCode"]
    if type_key not in valid_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de chave inválido. Use: {', '.join(valid_types)}"
        )
    
    # Buscar gateway PIX ativo
    gateway = get_active_pix_gateway(db)
    
    # Criar cliente SuitPay
    suitpay = get_suitpay_client(gateway)
    
    # URL do webhook
    webhook_url = os.getenv("WEBHOOK_BASE_URL", "https://api.agenciamidas.com")
    url_callback = f"{webhook_url}/api/webhooks/suitpay/pix-cashout"
    
    # Gerar external_id único para controle de duplicidade
    external_id = f"WTH_{user.id}_{int(datetime.utcnow().timestamp())}"
    
    # Realizar transferência PIX
    transfer_response = await suitpay.transfer_pix(
        value=amount,
        pix_key=pix_key,
        type_key=type_key,
        url_callback=url_callback,
        document_validation=document_validation,
        external_id=external_id
    )
    
    if not transfer_response:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erro ao processar transferência PIX no gateway"
        )
    
    # Verificar resposta da SuitPay
    response_status = transfer_response.get("response", "").upper()
    if response_status != "OK":
        error_messages = {
            "ACCOUNT_DOCUMENTS_NOT_VALIDATED": "Conta não validada",
            "NO_FUNDS": "Saldo insuficiente no gateway",
            "PIX_KEY_NOT_FOUND": "Chave PIX não encontrada",
            "UNAUTHORIZED_IP": "IP não autorizado",
            "DOCUMENT_VALIDATE": "A chave PIX não pertence ao documento informado",
            "DUPLICATE_EXTERNAL_ID": "ID externo já foi utilizado",
            "ERROR": "Erro interno no gateway"
        }
        error_msg = error_messages.get(response_status, f"Erro: {response_status}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Criar registro de saque
    withdrawal = Withdrawal(
        user_id=user.id,
        gateway_id=gateway.id,
        amount=amount,
        status=TransactionStatus.PENDING,
        transaction_id=str(uuid.uuid4()),
        external_id=transfer_response.get("idTransaction") or external_id,
        metadata_json=json.dumps({
            "pix_key": pix_key,
            "type_key": type_key,
            "document_validation": document_validation,
            "external_id": external_id,
            "suitpay_response": transfer_response
        })
    )
    
    # Bloquear saldo do usuário
    user.balance -= amount
    
    db.add(withdrawal)
    db.commit()
    db.refresh(withdrawal)
    
    return withdrawal


# ========== WEBHOOKS ==========

@webhook_router.post("/suitpay/pix-cashin")
async def webhook_pix_cashin(request: Request, db: Session = Depends(get_db)):
    """
    Webhook para receber notificações de PIX Cash-in (depósitos) da SuitPay
    """
    try:
        data = await request.json()
        
        # Buscar gateway PIX ativo para validar hash
        gateway = get_active_pix_gateway(db)
        credentials = json.loads(gateway.credentials) if gateway.credentials else {}
        client_secret = credentials.get("client_secret") or credentials.get("cs")
        
        if not client_secret:
            raise HTTPException(status_code=500, detail="Credenciais do gateway não configuradas")
        
        # Validar hash
        if not SuitPayAPI.validate_webhook_hash(data.copy(), client_secret):
            raise HTTPException(status_code=401, detail="Hash inválido")
        
        # Processar webhook
        id_transaction = data.get("idTransaction")
        status_transaction = data.get("statusTransaction")
        value = data.get("value")
        request_number = data.get("requestNumber")
        
        # Buscar depósito pelo external_id ou request_number
        deposit = None
        if id_transaction:
            deposit = db.query(Deposit).filter(Deposit.external_id == id_transaction).first()
        
        if not deposit and request_number:
            # Tentar buscar pelo request_number no metadata
            deposits = db.query(Deposit).filter(
                Deposit.status == TransactionStatus.PENDING
            ).all()
            for d in deposits:
                metadata = json.loads(d.metadata_json) if d.metadata_json else {}
                if metadata.get("request_number") == request_number:
                    deposit = d
                    break
        
        if not deposit:
            return {"status": "ok", "message": "Depósito não encontrado"}
        
        # Atualizar status do depósito
        if status_transaction == "PAID_OUT":
            if deposit.status != TransactionStatus.APPROVED:
                deposit.status = TransactionStatus.APPROVED
                # Adicionar saldo ao usuário
                user = db.query(User).filter(User.id == deposit.user_id).first()
                if user:
                    user.balance += deposit.amount
        elif status_transaction == "CHARGEBACK":
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


@webhook_router.post("/suitpay/pix-cashout")
async def webhook_pix_cashout(request: Request, db: Session = Depends(get_db)):
    """
    Webhook para receber notificações de PIX Cash-out (saques) da SuitPay
    """
    try:
        data = await request.json()
        
        # Buscar gateway PIX ativo para validar hash
        gateway = get_active_pix_gateway(db)
        credentials = json.loads(gateway.credentials) if gateway.credentials else {}
        client_secret = credentials.get("client_secret") or credentials.get("cs")
        
        if not client_secret:
            raise HTTPException(status_code=500, detail="Credenciais do gateway não configuradas")
        
        # Validar hash
        if not SuitPayAPI.validate_webhook_hash(data.copy(), client_secret):
            raise HTTPException(status_code=401, detail="Hash inválido")
        
        # Processar webhook
        id_transaction = data.get("idTransaction")
        status_transaction = data.get("statusTransaction")
        
        # Buscar saque pelo external_id
        withdrawal = None
        if id_transaction:
            withdrawal = db.query(Withdrawal).filter(Withdrawal.external_id == id_transaction).first()
        
        if not withdrawal:
            return {"status": "ok", "message": "Saque não encontrado"}
        
        # Atualizar status do saque
        if status_transaction == "PAID_OUT":
            withdrawal.status = TransactionStatus.APPROVED
        elif status_transaction == "CANCELED":
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
        
        return {"status": "ok", "message": "Webhook processado com sucesso"}
    
    except Exception as e:
        print(f"Erro ao processar webhook PIX Cash-out: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar webhook: {str(e)}")
