from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from models import Base
import os
import json

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
            
            # 8. Criar tabela affiliate_metrics
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS affiliate_metrics (
                    id SERIAL PRIMARY KEY,
                    affiliate_id INTEGER,
                    manager_id INTEGER,
                    sub_affiliate_id INTEGER,
                    metric_type VARCHAR(50) NOT NULL,
                    user_id INTEGER,
                    amount FLOAT,
                    metadata_json TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_metrics_affiliate_id ON affiliate_metrics(affiliate_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_metrics_manager_id ON affiliate_metrics(manager_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_metrics_sub_affiliate_id ON affiliate_metrics(sub_affiliate_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_metrics_metric_type ON affiliate_metrics(metric_type)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_metrics_created_at ON affiliate_metrics(created_at)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_metrics_user_id ON affiliate_metrics(user_id)"))
            
            # Adicionar foreign keys
            result = conn.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_affiliate_metrics_affiliate'
            """))
            if result.fetchone() is None:
                conn.execute(text("""
                    ALTER TABLE affiliate_metrics 
                    ADD CONSTRAINT fk_affiliate_metrics_affiliate 
                    FOREIGN KEY (affiliate_id) REFERENCES affiliates(id) ON DELETE CASCADE
                """))
            
            result = conn.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_affiliate_metrics_manager'
            """))
            if result.fetchone() is None:
                conn.execute(text("""
                    ALTER TABLE affiliate_metrics 
                    ADD CONSTRAINT fk_affiliate_metrics_manager 
                    FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE CASCADE
                """))
            
            result = conn.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_affiliate_metrics_sub_affiliate'
            """))
            if result.fetchone() is None:
                conn.execute(text("""
                    ALTER TABLE affiliate_metrics 
                    ADD CONSTRAINT fk_affiliate_metrics_sub_affiliate 
                    FOREIGN KEY (sub_affiliate_id) REFERENCES sub_affiliates(id) ON DELETE CASCADE
                """))
            
            result = conn.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_affiliate_metrics_user'
            """))
            if result.fetchone() is None:
                conn.execute(text("""
                    ALTER TABLE affiliate_metrics 
                    ADD CONSTRAINT fk_affiliate_metrics_user 
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                """))
            
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
            
            # 10. Adicionar coluna max_amount em ftd_settings (se não existir)
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'ftd_settings' AND column_name = 'max_amount'
            """))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE ftd_settings ADD COLUMN max_amount FLOAT NOT NULL DEFAULT 0.0"))
                print("✓ Added max_amount column to ftd_settings")
            
            # 11. Criar tabela sub_affiliates (se não existir)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sub_affiliates (
                    id SERIAL PRIMARY KEY,
                    manager_id INTEGER NOT NULL REFERENCES users(id),
                    affiliate_id INTEGER NOT NULL REFERENCES affiliates(id),
                    user_id INTEGER REFERENCES users(id),
                    cpa_rate FLOAT NOT NULL DEFAULT 0.0,
                    revshare_rate FLOAT NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sub_affiliates_manager_id ON sub_affiliates(manager_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sub_affiliates_affiliate_id ON sub_affiliates(affiliate_id)"))
            
            # 12. Criar tabela manager_settings (se não existir)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS manager_settings (
                    id SERIAL PRIMARY KEY,
                    manager_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
                    cpa_pool FLOAT NOT NULL DEFAULT 0.0,
                    cpa_distributed FLOAT NOT NULL DEFAULT 0.0,
                    revshare_rate FLOAT NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_manager_settings_manager_id ON manager_settings(manager_id)"))
            
            # 13. Adicionar coluna bonus_balance em users (se não existir)
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'bonus_balance'
            """))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE users ADD COLUMN bonus_balance FLOAT NOT NULL DEFAULT 0.0"))
                print("✓ Added bonus_balance column to users")
            
            # 14. Criar tabela coupons (se não existir)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS coupons (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    type VARCHAR(20) NOT NULL,
                    value FLOAT NOT NULL,
                    max_uses INTEGER,
                    uses INTEGER NOT NULL DEFAULT 0,
                    valid_from TIMESTAMP NOT NULL,
                    valid_until TIMESTAMP NOT NULL,
                    min_deposit_amount FLOAT NOT NULL DEFAULT 0.0,
                    max_bonus_amount FLOAT,
                    is_withdrawable BOOLEAN NOT NULL DEFAULT FALSE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_coupons_code ON coupons(code)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_coupons_is_active ON coupons(is_active)"))
            
            # 14. Criar tabela coupon_uses (se não existir)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS coupon_uses (
                    id SERIAL PRIMARY KEY,
                    coupon_id INTEGER NOT NULL REFERENCES coupons(id),
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    deposit_id INTEGER REFERENCES deposits(id),
                    bonus_amount FLOAT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_coupon_uses_coupon_id ON coupon_uses(coupon_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_coupon_uses_user_id ON coupon_uses(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_coupon_uses_deposit_id ON coupon_uses(deposit_id)"))
            
            # 15. Adicionar colunas bonus_amount e coupon_code em deposits (se não existirem)
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'deposits' AND column_name = 'bonus_amount'
            """))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE deposits ADD COLUMN bonus_amount FLOAT DEFAULT 0.0 NOT NULL"))
                print("✓ Added bonus_amount column to deposits")
            
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'deposits' AND column_name = 'coupon_code'
            """))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE deposits ADD COLUMN coupon_code VARCHAR(50)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_deposits_coupon_code ON deposits(coupon_code)"))
                print("✓ Added coupon_code column to deposits")
            
            # 16. Criar tabela promotions (se não existir)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS promotions (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    type VARCHAR(50) NOT NULL,
                    bonus_value FLOAT NOT NULL DEFAULT 0.0,
                    bonus_type VARCHAR(20) NOT NULL DEFAULT 'percentage',
                    min_deposit_amount FLOAT NOT NULL DEFAULT 0.0,
                    max_bonus_amount FLOAT,
                    banner_url VARCHAR(500),
                    is_first_deposit_only BOOLEAN NOT NULL DEFAULT FALSE,
                    is_withdrawable BOOLEAN NOT NULL DEFAULT FALSE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Adicionar coluna is_withdrawable em coupons se não existir
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'coupons' AND column_name = 'is_withdrawable'
            """))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE coupons ADD COLUMN is_withdrawable BOOLEAN NOT NULL DEFAULT FALSE"))
                print("✓ Added is_withdrawable column to coupons")
            
            # Adicionar coluna is_withdrawable em promotions se não existir
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'promotions' AND column_name = 'is_withdrawable'
            """))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE promotions ADD COLUMN is_withdrawable BOOLEAN NOT NULL DEFAULT FALSE"))
                print("✓ Added is_withdrawable column to promotions")
            
            # Corrigir depósitos já aprovados que foram creditados antes da separação de saldo
            print("Corrigindo depósitos já aprovados...")
            deposits_result = conn.execute(text("""
                SELECT d.id, d.user_id, d.amount, d.bonus_amount, d.coupon_code, d.metadata_json
                FROM deposits d
                WHERE d.status = 'approved' AND d.bonus_amount > 0
            """))
            deposits = deposits_result.fetchall()
            
            fixed_count = 0
            for deposit in deposits:
                deposit_id, user_id, amount, bonus_amount, coupon_code, metadata_json = deposit
                
                # Buscar cupom se houver
                coupon_is_withdrawable = None
                if coupon_code:
                    coupon_result = conn.execute(text("""
                        SELECT is_withdrawable FROM coupons WHERE code = :code
                    """), {"code": coupon_code})
                    coupon_row = coupon_result.fetchone()
                    if coupon_row:
                        coupon_is_withdrawable = coupon_row[0]
                
                # Extrair informações do metadata
                metadata = json.loads(metadata_json) if metadata_json else {}
                promotion_id = metadata.get("promotion_id")
                promotion_bonus = metadata.get("promotion_bonus", 0)
                coupon_bonus = metadata.get("coupon_bonus", 0)
                
                # Calcular bônus não sacável
                non_withdrawable_bonus = 0.0
                
                if coupon_bonus > 0 and coupon_is_withdrawable is not None:
                    if not coupon_is_withdrawable:
                        non_withdrawable_bonus += coupon_bonus
                
                if promotion_bonus > 0 and promotion_id:
                    promotion_result = conn.execute(text("""
                        SELECT is_withdrawable FROM promotions WHERE id = :id
                    """), {"id": promotion_id})
                    promotion_row = promotion_result.fetchone()
                    if promotion_row and not promotion_row[0]:
                        non_withdrawable_bonus += promotion_bonus
                
                # Se há bônus não sacável, mover do balance para bonus_balance
                if non_withdrawable_bonus > 0:
                    # Verificar saldo atual do usuário
                    user_result = conn.execute(text("""
                        SELECT balance, COALESCE(bonus_balance, 0) as bonus_balance FROM users WHERE id = :id
                    """), {"id": user_id})
                    user_row = user_result.fetchone()
                    
                    if user_row:
                        current_balance = user_row[0] or 0.0
                        current_bonus_balance = user_row[1] or 0.0
                        
                        # Só mover o que ainda está disponível (pode ter sido usado em apostas)
                        # Se o usuário tem menos que o depósito + bônus, significa que já usou parte
                        # Nesse caso, mover apenas o que ainda está no balance
                        amount_to_move = min(non_withdrawable_bonus, max(0, current_balance - amount))
                        
                        if amount_to_move > 0:
                            conn.execute(text("""
                                UPDATE users 
                                SET balance = balance - :amount_to_move,
                                    bonus_balance = COALESCE(bonus_balance, 0) + :amount_to_move
                                WHERE id = :user_id
                            """), {
                                "amount_to_move": amount_to_move,
                                "user_id": user_id
                            })
                            fixed_count += 1
            
            if fixed_count > 0:
                print(f"✓ Corrigidos {fixed_count} depósitos - bônus não sacáveis movidos para bonus_balance")
            else:
                print("✓ Nenhum depósito precisa de correção")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_promotions_is_active ON promotions(is_active)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_promotions_is_first_deposit_only ON promotions(is_first_deposit_only)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_promotions_start_date ON promotions(start_date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_promotions_end_date ON promotions(end_date)"))
            
            # 17. Criar tabela promotion_uses (se não existir)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS promotion_uses (
                    id SERIAL PRIMARY KEY,
                    promotion_id INTEGER NOT NULL REFERENCES promotions(id),
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    deposit_id INTEGER REFERENCES deposits(id),
                    bonus_amount FLOAT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_promotion_uses_promotion_id ON promotion_uses(promotion_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_promotion_uses_user_id ON promotion_uses(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_promotion_uses_deposit_id ON promotion_uses(deposit_id)"))
            
            # 18. Adicionar coluna rtp em igamewin_agents (se não existir)
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'igamewin_agents' AND column_name = 'rtp'
            """))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE igamewin_agents ADD COLUMN rtp FLOAT DEFAULT 96.0 NOT NULL"))
                conn.execute(text("UPDATE igamewin_agents SET rtp = 96.0 WHERE rtp IS NULL"))
                print("✓ Added rtp column to igamewin_agents")
            
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
