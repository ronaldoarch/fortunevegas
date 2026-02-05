from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from database import get_db
from schemas import LoginRequest, Token, UserResponse, UserCreate
from auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash, get_user_by_username
from dependencies import get_current_user
from models import User, UserRole, Affiliate
from tracking_dispatcher import dispatch_tracking_event

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Verificar se username já existe
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Verificar se email já existe (apenas se fornecido)
    if user_data.email:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Verificar se telefone já existe (se fornecido)
    if user_data.phone:
        phone_clean = ''.join(filter(str.isdigit, user_data.phone))
        existing_phone = db.query(User).filter(User.phone == phone_clean).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone already registered"
            )
        # Usar telefone limpo
        phone_to_save = phone_clean
    else:
        phone_to_save = None
    
    # Criar email temporário se não fornecido
    email_to_save = user_data.email if user_data.email else f"{user_data.username}@temp.com"
    
    # Processar código de afiliado se fornecido
    affiliate_id = None
    if user_data.affiliate_code:
        affiliate = db.query(Affiliate).filter(
            Affiliate.code == user_data.affiliate_code,
            Affiliate.is_active == True
        ).first()
        if affiliate:
            affiliate_id = affiliate.id
            print(f"[AFFILIATE] Usuário sendo registrado com código de afiliado: {user_data.affiliate_code} (ID: {affiliate_id})")
        else:
            print(f"[AFFILIATE] Código de afiliado inválido ou inativo: {user_data.affiliate_code}")
    
    # Criar novo usuário
    new_user = User(
        username=user_data.username,
        email=email_to_save,
        cpf=user_data.cpf,
        phone=phone_to_save,
        password_hash=get_password_hash(user_data.password),
        role=UserRole.USER,
        balance=0.0,
        is_active=True,
        is_verified=False,
        affiliate_id=affiliate_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Disparar evento de tracking para cadastro
    try:
        await dispatch_tracking_event(
            db=db,
            event_name="registration",
            payload={
                "user_id": new_user.id,
                "email": new_user.email,
                "phone": new_user.phone,
                "username": new_user.username,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "cpf": new_user.cpf,
                    "affiliate_id": new_user.affiliate_id
                }
            }
        )
    except Exception as e:
        print(f"[TRACKING] Erro ao disparar evento de cadastro (não crítico): {str(e)}")
    
    return new_user


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    # authenticate_user já tenta por username e email
    user = authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
