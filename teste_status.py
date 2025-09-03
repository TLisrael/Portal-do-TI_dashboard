import pandas as pd
import urllib.parse
from sqlalchemy import create_engine, text

# Configurações de conexão
DB_CONFIG = {
    'server': 'rio01p-sql01',
    'database': 'ControleTI',
    'username': 'RM',
    'password': 'rm',
    'driver': 'ODBC Driver 17 for SQL Server',
    'port': '1433'
}

def get_engine():
    """Cria engine SQLAlchemy para SQL Server"""
    try:
        password_encoded = urllib.parse.quote_plus(DB_CONFIG['password'])
        username_encoded = urllib.parse.quote_plus(DB_CONFIG['username'])
        driver_encoded = urllib.parse.quote_plus(DB_CONFIG['driver'])
        
        connection_string = f"""mssql+pyodbc://{username_encoded}:{password_encoded}@{DB_CONFIG['server']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?driver={driver_encoded}"""
        
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        print(f"Erro na criação da engine: {e}")
        return None

def execute_query(query):
    """Executa query e retorna DataFrame usando SQLAlchemy"""
    engine = get_engine()
    if engine:
        try:
            with engine.connect() as connection:
                df = pd.read_sql(text(query), connection)
            return df
        except Exception as e:
            print(f"Erro na query: {e}")
            print(f"Query executada: {query}")
            return pd.DataFrame()
    return pd.DataFrame()

# Query de teste de status
query_status = """
SELECT 
    c.Status as StatusNumerico,
    CASE 
        WHEN c.Status = 1 THEN 'Em Estoque'
        WHEN c.Status = 2 THEN 'Acesso Remoto'
        WHEN c.Status = 3 THEN 'Em Uso'
        WHEN c.Status = 4 THEN 'Extraviado'
        WHEN c.Status = 5 THEN 'Reparo'
        WHEN c.Status = 6 THEN 'Roubado'
        WHEN c.Status = 7 THEN 'Devolvido'
        WHEN c.Status = 8 THEN 'Descartado'
        WHEN c.Status = 9 THEN 'Danificado'
        ELSE 'Status Indefinido'
    END as Status,
    COUNT(*) as Quantidade,
    ROUND((COUNT(*) * 100.0) / (SELECT COUNT(*) FROM Computadores), 2) as Percentual
FROM Computadores c
WHERE c.Status IS NOT NULL
GROUP BY c.Status
ORDER BY c.Status
"""

# Query simples para ver todos os status
query_simples = """
SELECT Status, COUNT(*) as Quantidade
FROM Computadores
GROUP BY Status
ORDER BY Status
"""

print("=== TESTE DE CONEXÃO E QUERY ===")
print("\n1. Testando query simples de contagem por status:")
df_simples = execute_query(query_simples)
print(df_simples)

print("\n2. Testando query com mapeamento de status:")
df_status = execute_query(query_status)
print(df_status)

print("\n3. Testando query de amostra dos primeiros 10 registros:")
query_amostra = "SELECT TOP 10 Serial, Modelo, Status, Usuario, Matricula FROM Computadores"
df_amostra = execute_query(query_amostra)
print(df_amostra)
