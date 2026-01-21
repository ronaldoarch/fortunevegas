-- Migração para adicionar novas funcionalidades: GameLayout, Theme, Affiliate
-- Execute este script no PostgreSQL antes de iniciar o backend
-- IMPORTANTE: Execute na ordem correta!

-- 1. Criar tabela affiliates PRIMEIRO (antes de adicionar foreign key em users)
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
);

CREATE INDEX IF NOT EXISTS idx_affiliates_code ON affiliates(code);

-- 2. Adicionar coluna affiliate_id na tabela users (se não existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'affiliate_id'
    ) THEN
        ALTER TABLE users ADD COLUMN affiliate_id INTEGER;
    END IF;
END $$;

-- 3. Adicionar foreign key de users.affiliate_id para affiliates.id (se não existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_users_affiliate'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT fk_users_affiliate 
            FOREIGN KEY (affiliate_id) REFERENCES affiliates(id);
    END IF;
END $$;

-- 4. Criar tabela game_layouts (se não existir)
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
);

CREATE INDEX IF NOT EXISTS idx_game_layouts_game_code ON game_layouts(game_code);
CREATE INDEX IF NOT EXISTS idx_game_layouts_position ON game_layouts(position);

-- 5. Criar tabela themes (se não existir)
CREATE TABLE IF NOT EXISTS themes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    colors_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
