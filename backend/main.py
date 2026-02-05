from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, get_db
from auth import create_admin_user
from sqlalchemy.orm import Session
import os

# Import routes
from routes import auth, admin, media, payments, affiliate

app = FastAPI(title="Fortune Vegas API", version="1.0.0")

# Configurar CORS - permite variáveis de ambiente para produção
cors_origins_env = os.getenv("CORS_ORIGINS", "").strip()
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()] if cors_origins_env else []

# Se não houver variável, usa defaults de desenvolvimento
if not cors_origins:
    cors_origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        # Domínios de produção
        "https://fortunevegas.site",
        "http://fortunevegas.site",
        "https://www.fortunevegas.site",
        "http://www.fortunevegas.site",
        "https://*.agenciamidas.com",
        "http://*.agenciamidas.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https?://(.*\.)?(fortunevegas\.site|agenciamidas\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(admin.public_router)
app.include_router(media.router)
app.include_router(media.public_router)
app.include_router(payments.router)
app.include_router(payments.webhook_router)
app.include_router(affiliate.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and create admin user on startup"""
    init_db()
    # Create admin user
    db = next(get_db())
    try:
        create_admin_user(db)
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "Fortune Vegas API", "status": "ok", "version": "1.0.0"}


@app.get("/api/health")
async def health():
    return {"status": "healthy"}
