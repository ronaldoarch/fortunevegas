from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from models import Base
import os

# Obter DATABASE_URL e normalizar postgres:// para postgresql://
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fortunevegas.db")
# SQLAlchemy 2.0 requer postgresql:// em vez de postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def run_migrations():
    """Executa migrações SQL para PostgreSQL"""
    # Apenas para PostgreSQL
    if "postgresql" not in DATABASE_URL.lower():
        return
    
    try:
        with engine.begin() as conn:  # begin() cria transação automaticamente
            # 1. Criar tabela affiliates primeiro
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS affiliates (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(100) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    phone VARCHAR(20),
                    commission_rate FLOAT NOT NULL DEFAULT 0.0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    metadata_json TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliates_code ON affiliates(code)"))
            
            # 2. Adicionar coluna affiliate_id em users (se não existir)
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'affiliate_id'
            """))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE users ADD COLUMN affiliate_id INTEGER"))
            
            # 3. Adicionar foreign key (se não existir)
            result = conn.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_users_affiliate'
            """))
            if result.fetchone() is None:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD CONSTRAINT fk_users_affiliate 
                    FOREIGN KEY (affiliate_id) REFERENCES affiliates(id)
                """))
            
            # 4. Criar tabela game_layouts
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS game_layouts (
                    id SERIAL PRIMARY KEY,
                    game_code VARCHAR(255) NOT NULL,
                    provider_code VARCHAR(100),
                    position INTEGER NOT NULL DEFAULT 0,
                    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
                    section VARCHAR(100) DEFAULT 'home',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_game_layouts_game_code ON game_layouts(game_code)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_game_layouts_position ON game_layouts(position)"))
            
            # 5. Criar tabela provider_layouts
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS provider_layouts (
                    id SERIAL PRIMARY KEY,
                    provider_code VARCHAR(100) UNIQUE NOT NULL,
                    provider_name VARCHAR(255) NOT NULL,
                    position INTEGER NOT NULL DEFAULT 0,
                    max_games INTEGER NOT NULL DEFAULT 30,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    section VARCHAR(100) DEFAULT 'home',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_provider_layouts_provider_code ON provider_layouts(provider_code)"))
            
            # 6. Criar tabela themes
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS themes (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    is_default BOOLEAN NOT NULL DEFAULT FALSE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    colors_json TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 7. Criar tabela igamewin_provider_configs
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS igamewin_provider_configs (
                    id SERIAL PRIMARY KEY,
                    provider_code VARCHAR(100) UNIQUE NOT NULL,
                    provider_name VARCHAR(255) NOT NULL,
                    position INTEGER NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_igamewin_provider_configs_provider_code ON igamewin_provider_configs(provider_code)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_igamewin_provider_configs_position ON igamewin_provider_configs(position)"))
            
            # 8. Criar tabela tracking_configs
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tracking_configs (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    url VARCHAR(500),
                    pixel_id VARCHAR(255),
                    access_token VARCHAR(500),
                    api_key VARCHAR(500),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    metadata_json TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tracking_configs_type ON tracking_configs(type)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tracking_configs_is_active ON tracking_configs(is_active)"))
            
            # 8. Criar tabela webhooks
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS webhooks (
                    id SERIAL PRIMARY KEY,
                    url VARCHAR(500) NOT NULL,
                    username VARCHAR(255),
                    password VARCHAR(500),
                    event_type VARCHAR(50) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_webhooks_event_type ON webhooks(event_type)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_webhooks_is_active ON webhooks(is_active)"))
            
            # 9. Adicionar coluna min_withdrawal em ftd_settings (se não existir)
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'ftd_settings' AND column_name = 'min_withdrawal'
            """))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE ftd_settings ADD COLUMN min_withdrawal FLOAT NOT NULL DEFAULT 0.0"))
                print("✓ Added min_withdrawal column to ftd_settings")
            
            print("✓ Migrations executed successfully")
    except Exception as e:
        # Ignora erros de "already exists" ou constraints duplicadas
        error_str = str(e).lower()
        if "already exists" in error_str or "duplicate" in error_str or "constraint" in error_str:
            print(f"⚠ Migration partially applied (some objects may already exist): {e}")
        else:
            print(f"❌ Error running migrations: {e}")
            raise


def init_db():
    """Initialize database tables"""
    # Executa migrações primeiro (para PostgreSQL)
    run_migrations()
    # Depois cria/atualiza tabelas com SQLAlchemy
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
