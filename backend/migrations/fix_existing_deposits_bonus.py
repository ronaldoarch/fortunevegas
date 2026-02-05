"""
Script para corrigir depósitos já aprovados que foram creditados antes da implementação
da separação de saldo real e bônus não sacável.

Este script deve ser executado manualmente após o deploy para corrigir depósitos existentes.
"""
import os
import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Obter DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fortunevegas.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def fix_deposits():
    """Corrige depósitos já aprovados movendo bônus não sacáveis para bonus_balance"""
    db = SessionLocal()
    
    try:
        # Buscar todos os depósitos aprovados que têm bônus
        result = db.execute(text("""
            SELECT d.id, d.user_id, d.amount, d.bonus_amount, d.coupon_code, d.metadata_json
            FROM deposits d
            WHERE d.status = 'approved' AND d.bonus_amount > 0
        """))
        
        deposits = result.fetchall()
        print(f"Encontrados {len(deposits)} depósitos aprovados com bônus")
        
        fixed_count = 0
        for deposit in deposits:
            deposit_id, user_id, amount, bonus_amount, coupon_code, metadata_json = deposit
            
            # Buscar cupom se houver
            coupon = None
            if coupon_code:
                coupon_result = db.execute(text("""
                    SELECT id, is_withdrawable FROM coupons WHERE code = :code
                """), {"code": coupon_code})
                coupon_row = coupon_result.fetchone()
                if coupon_row:
                    coupon = {"id": coupon_row[0], "is_withdrawable": coupon_row[1]}
            
            # Extrair informações do metadata
            metadata = json.loads(metadata_json) if metadata_json else {}
            promotion_id = metadata.get("promotion_id")
            promotion_bonus = metadata.get("promotion_bonus", 0)
            coupon_bonus = metadata.get("coupon_bonus", 0)
            
            # Verificar se precisa corrigir
            needs_fix = False
            withdrawable_bonus = 0.0
            non_withdrawable_bonus = 0.0
            
            if coupon_bonus > 0 and coupon:
                if coupon["is_withdrawable"]:
                    withdrawable_bonus += coupon_bonus
                else:
                    non_withdrawable_bonus += coupon_bonus
                    needs_fix = True
            
            if promotion_bonus > 0 and promotion_id:
                promotion_result = db.execute(text("""
                    SELECT is_withdrawable FROM promotions WHERE id = :id
                """), {"id": promotion_id})
                promotion_row = promotion_result.fetchone()
                if promotion_row:
                    if promotion_row[0]:
                        withdrawable_bonus += promotion_bonus
                    else:
                        non_withdrawable_bonus += promotion_bonus
                        needs_fix = True
            
            if needs_fix:
                # Buscar usuário
                user_result = db.execute(text("""
                    SELECT balance, bonus_balance FROM users WHERE id = :id
                """), {"id": user_id})
                user_row = user_result.fetchone()
                
                if user_row:
                    current_balance = user_row[0] or 0.0
                    current_bonus_balance = user_row[1] or 0.0
                    
                    # Se o bônus não sacável está no balance, mover para bonus_balance
                    # Assumindo que o bônus foi creditado incorretamente no balance
                    if current_balance >= amount + bonus_amount:
                        # Mover bônus não sacável do balance para bonus_balance
                        db.execute(text("""
                            UPDATE users 
                            SET balance = balance - :non_withdrawable,
                                bonus_balance = bonus_balance + :non_withdrawable
                            WHERE id = :user_id
                        """), {
                            "non_withdrawable": non_withdrawable_bonus,
                            "user_id": user_id
                        })
                        
                        print(f"Depósito {deposit_id}: Movido R$ {non_withdrawable_bonus:.2f} de balance para bonus_balance")
                        fixed_count += 1
        
        db.commit()
        print(f"\nCorreção concluída: {fixed_count} depósitos corrigidos")
        
    except Exception as e:
        db.rollback()
        print(f"Erro ao corrigir depósitos: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Iniciando correção de depósitos existentes...")
    fix_deposits()
    print("Correção finalizada!")
