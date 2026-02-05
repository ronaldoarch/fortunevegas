#!/usr/bin/env python3
"""
Script para executar a migration que adiciona o campo RTP à tabela igamewin_agents
Execute este script no terminal do container do backend no Coolify
"""
import os
import sys
from sqlalchemy import create_engine, text

# Obter DATABASE_URL e normalizar postgres:// para postgresql://
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Erro: DATABASE_URL não encontrada nas variáveis de ambiente")
    sys.exit(1)

# SQLAlchemy 2.0 requer postgresql:// em vez de postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"🔌 Conectando ao banco de dados...")
print(f"   URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '***'}")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.begin() as conn:
        print("\n📝 Executando migration: Adicionar campo RTP à tabela igamewin_agents...")
        
        # Verificar se a coluna já existe
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'igamewin_agents' AND column_name = 'rtp'
        """))
        
        if result.fetchone():
            print("⚠️  A coluna 'rtp' já existe na tabela igamewin_agents")
        else:
            # Adicionar coluna RTP
            print("   → Adicionando coluna 'rtp'...")
            conn.execute(text("""
                ALTER TABLE igamewin_agents 
                ADD COLUMN rtp FLOAT DEFAULT 96.0 NOT NULL
            """))
            print("   ✓ Coluna 'rtp' adicionada com sucesso")
        
        # Atualizar registros existentes para ter o valor padrão
        print("   → Atualizando registros existentes...")
        result = conn.execute(text("""
            UPDATE igamewin_agents 
            SET rtp = 96.0 
            WHERE rtp IS NULL
        """))
        updated_count = result.rowcount
        print(f"   ✓ {updated_count} registro(s) atualizado(s)")
        
        # Verificar resultado final
        result = conn.execute(text("""
            SELECT COUNT(*) as total, 
                   COUNT(CASE WHEN rtp IS NOT NULL THEN 1 END) as com_rtp,
                   AVG(rtp) as rtp_medio
            FROM igamewin_agents
        """))
        stats = result.fetchone()
        
        print("\n✅ Migration executada com sucesso!")
        print(f"   Total de agentes: {stats[0]}")
        print(f"   Agentes com RTP: {stats[1]}")
        print(f"   RTP médio: {stats[2]:.2f}%")
        
except Exception as e:
    print(f"\n❌ Erro ao executar migration: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
