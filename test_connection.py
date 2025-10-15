#!/usr/bin/env python3
"""
Script para testar a conexão com SQL Server no Linux
"""

import sys
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse

# Configurações de conexão
DB_CONFIG = {
    'server': 'rio01p-sql01',
    'database': 'ControleTI',
    'username': 'RM',
    'password': 'rm',
    'port': '1433'
}

def test_connection():
    """Testa diferentes métodos de conexão"""
    
    password_encoded = urllib.parse.quote_plus(DB_CONFIG['password'])
    username_encoded = urllib.parse.quote_plus(DB_CONFIG['username'])
    
    # Métodos de conexão para testar
    connection_methods = [
        {
            'name': 'pyodbc com FreeTDS',
            'string': f"mssql+pyodbc://{username_encoded}:{password_encoded}@{DB_CONFIG['server']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?driver=FreeTDS&TrustServerCertificate=yes"
        },
        {
            'name': 'pymssql',
            'string': f"mssql+pymssql://{username_encoded}:{password_encoded}@{DB_CONFIG['server']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        }
    ]
    
    for method in connection_methods:
        print(f"\n🔍 Testando: {method['name']}")
        print(f"Connection string: {method['string'].replace(DB_CONFIG['password'], '***')}")
        
        try:
            engine = create_engine(method['string'])
            
            # Testa a conexão
            with engine.connect() as connection:
                result = connection.execute(text("SELECT @@VERSION as version, GETDATE() as server_time"))
                row = result.fetchone()
                
                print(f"✅ Conexão bem-sucedida!")
                print(f"📊 Versão do SQL Server: {row[0][:100]}...")
                print(f"🕐 Hora do servidor: {row[1]}")
                
                # Testa uma query simples do seu banco
                try:
                    result = connection.execute(text("SELECT TOP 5 * FROM INFORMATION_SCHEMA.TABLES"))
                    tables = result.fetchall()
                    print(f"📋 Primeiras 5 tabelas encontradas:")
                    for table in tables:
                        print(f"   - {table[2]} (Schema: {table[1]})")
                except Exception as e:
                    print(f"⚠️  Erro ao listar tabelas: {e}")
                
                return engine, method['name']
                
        except Exception as e:
            print(f"❌ Falha: {e}")
            continue
    
    print("\n❌ Nenhum método de conexão funcionou!")
    return None, None

if __name__ == "__main__":
    print("🚀 Testando conexão com SQL Server no Linux...")
    print(f"🎯 Servidor: {DB_CONFIG['server']}:{DB_CONFIG['port']}")
    print(f"🗃️  Database: {DB_CONFIG['database']}")
    print(f"👤 Usuário: {DB_CONFIG['username']}")
    
    engine, method = test_connection()
    
    if engine:
        print(f"\n🎉 Sucesso! Use o método: {method}")
        print("✨ Sua aplicação deve funcionar agora!")
    else:
        print("\n💡 Sugestões:")
        print("1. Verifique se o servidor SQL Server está acessível:")
        print(f"   telnet {DB_CONFIG['server']} {DB_CONFIG['port']}")
        print("2. Confirme as credenciais de acesso")
        print("3. Verifique se o firewall permite conexões na porta 1433")
        print("4. Considere usar um banco de dados local (SQLite) para desenvolvimento")
