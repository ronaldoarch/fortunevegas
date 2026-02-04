from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import User, UserRole
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    # Tenta encontrar por username primeiro
    user = db.query(User).filter(User.username == username).first()
    # Se não encontrou, tenta por email
    if not user:
        user = db.query(User).filter(User.email == username).first()
    # Se não encontrou, tenta por telefone (limpar caracteres especiais)
    if not user:
        phone_clean = ''.join(filter(str.isdigit, username))
        if phone_clean:
            user = db.query(User).filter(User.phone == phone_clean).first()
            # Se não encontrou com telefone limpo, tentar buscar por username que pode ser o telefone
            if not user:
                user = db.query(User).filter(User.username == phone_clean).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def create_admin_user(db: Session):
    """Create default admin user if doesn't exist"""
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@fortunevegas.com",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            balance=0.0
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    return admin
