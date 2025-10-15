#!/usr/bin/env python3
"""
Script para verificar os dados de estoque e confirmar se as exclusões estão funcionando
"""
import pandas as pd
from app import get_engine, QUERIES
from sqlalchemy import text

def verificar_estoque():
    engine = get_engine()
    if not engine:
        print("❌ Erro ao conectar com o banco de dados")
        return
    
    print("=== VERIFICAÇÃO DE ESTOQUE ===\n")
    
    try:
        with engine.connect() as connection:
            # 1. Total geral de computadores (sem filtros)
            result = connection.execute(text("SELECT COUNT(*) FROM Computadores WHERE Usuario LIKE '%estoque%'"))
            total_geral = result.fetchone()[0]
            print(f"📊 Total geral em estoque (sem filtros): {total_geral}")
            
            # 2. Total por status
            result = connection.execute(text("""
                SELECT Status, COUNT(*) as Quantidade 
                FROM Computadores 
                WHERE Usuario LIKE '%estoque%'
                GROUP BY Status 
                ORDER BY Status
            """))
            print("\n📋 Distribuição por Status:")
            total_excluidos = 0
            for row in result.fetchall():
                status, quantidade = row
                status_nome = {
                    1: "Ativo",
                    2: "Inativo", 
                    3: "Manutenção",
                    4: "Extraviado",
                    5: "Reparo",
                    6: "Roubado",
                    7: "Emprestado",
                    8: "Descartado",
                    9: "Danificado"
                }.get(status, f"Status {status}")
                
                if status in [4, 8, 9]:  # Status excluídos
                    print(f"   ❌ Status {status} ({status_nome}): {quantidade} (EXCLUÍDO)")
                    total_excluidos += quantidade
                else:
                    print(f"   ✅ Status {status} ({status_nome}): {quantidade}")
            
            # 3. Total após exclusões
            result = connection.execute(text(QUERIES['total_equipamentos_estoque']))
            total_filtrado_resultado = result.fetchone()
            total_filtrado = total_filtrado_resultado[0] if total_filtrado_resultado and total_filtrado_resultado[0] else 0
            print(f"\n🎯 Total em estoque APÓS exclusões: {total_filtrado}")
            
            print(f"🚫 Total excluído (descarte, danificado, extraviado): {total_excluidos}")
            
            print(f"\n✅ Verificação: {total_geral} - {total_excluidos} = {total_geral - total_excluidos}")
            print(f"   Resultado da query: {total_filtrado}")
            
            if total_geral - total_excluidos == total_filtrado:
                print("✅ As exclusões estão funcionando corretamente!")
            else:
                print("❌ Há algum problema com as exclusões!")
    
    except Exception as e:
        print(f"❌ Erro durante a verificação: {e}")

if __name__ == "__main__":
    verificar_estoque()
