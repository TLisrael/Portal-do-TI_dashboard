import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import os
import numpy as np
import urllib.parse

# ==================== CONFIGURAÇÕES DE CONEXÃO ====================
DB_CONFIG = {
    'server': 'rio01p-sql01',
    'database': 'ControleTI',
    'username': 'RM',
    'password': 'rm',
    'port': '1433'
}

# ===================================================================


def get_engine():
    """Cria engine SQLAlchemy para SQL Server - Compatível com Linux"""
    try:
        password_encoded = urllib.parse.quote_plus(DB_CONFIG['password'])
        username_encoded = urllib.parse.quote_plus(DB_CONFIG['username'])
        
        connection_attempts = [
            {
                'driver': 'ODBC Driver 18 for SQL Server',
                'method': 'pyodbc'
            },
            {
                'driver': 'ODBC Driver 17 for SQL Server', 
                'method': 'pyodbc'
            },
            {
                'driver': 'FreeTDS',
                'method': 'pyodbc'
            },
            # Método 2: pymssql (não precisa de ODBC)
            {
                'method': 'pymssql'
            }
        ]
        
        for attempt in connection_attempts:
            try:
                if attempt['method'] == 'pyodbc':
                    driver_encoded = urllib.parse.quote_plus(attempt['driver'])
                    connection_string = f"""mssql+pyodbc://{username_encoded}:{password_encoded}@{DB_CONFIG['server']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?driver={driver_encoded}&TrustServerCertificate=yes"""
                elif attempt['method'] == 'pymssql':
                    connection_string = f"""mssql+pymssql://{username_encoded}:{password_encoded}@{DB_CONFIG['server']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"""
                
                print(f"Tentando conexão com: {attempt}")
                engine = create_engine(connection_string)
                
                # Testa a conexão
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                
                print(f"Conexão bem-sucedida com: {attempt}")
                return engine
                
            except Exception as e:
                print(f"Falha com {attempt}: {e}")
                continue
        
        raise Exception("Nenhum método de conexão funcionou")
        
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

QUERIES = {
    # Terceirizados inativos com equipamentos
    'terceirizados_inativos_com_equipamentos': """
        SELECT 
            C.Serial, 
            C.Modelo, 
            C.Matricula AS Matricula_Comp,        
            T.Nome, 
            T.Matricula AS Matricula_Terc, 
            T.Chefia 
        FROM Computadores C 
        JOIN Terceirizados T ON C.Matricula = T.Matricula 
        WHERE T.Situacao = 0
    """,
    
    # Terceirizados ativos com equipamentos
    'terceirizados_ativos_com_equipamentos': """
        SELECT 
            C.Serial, 
            C.Modelo, 
            C.Matricula AS Matricula_Comp,        
            T.Nome, 
            T.Matricula AS Matricula_Terc, 
            T.Chefia 
        FROM Computadores C 
        JOIN Terceirizados T ON C.Matricula = T.Matricula 
        WHERE T.Situacao = 1
    """,
    
    # Colaboradores demitidos
    'colaboradores_demitidos': """
        SELECT Colaboradores.Nome 
        FROM Colaboradores  
        WHERE Colaboradores.Situacao = 'Demitido'
    """,
    
    # Colaboradores aviso prévio
    'colaboradores_aviso_previo': """
        SELECT Colaboradores.Nome 
        FROM Colaboradores  
        WHERE Colaboradores.Situacao = 'Aviso Prévio'
    """,
    
    # Colaboradores demitidos com equipamentos
    'colaboradores_demitidos_com_equipamentos': """
        SELECT     
            c.Nome AS Colaborador,     
            c.CCusto,     
            c.Chefia,     
            comp.Modelo AS ModeloComputador,     
            p.Modelo AS ModeloPeriferico 
        FROM Colaboradores c 
        LEFT JOIN Computadores comp ON comp.Matricula = c.Matricula 
        LEFT JOIN Perifericos p ON p.Matricula = c.Matricula 
        WHERE c.Situacao = 'Demitido'     
            AND c.Nome IS NOT NULL     
            AND comp.Modelo IS NOT NULL     
            AND (comp.ID IS NOT NULL OR p.ID IS NOT NULL)
    """,
    
    # Total em estoque
    'total_equipamentos_estoque': """
        SELECT SUM(Quantidade) AS TotalEmEstoque 
        FROM (     
            SELECT Modelo, COUNT(*) AS Quantidade     
            FROM Computadores     
            WHERE Usuario LIKE '%estoque%'     
              AND Status NOT IN (4, 6, 8, 9, 5)  -- Excluir: Extraviado, Roubado, Descartado, Danificado, Reparo
            GROUP BY Modelo 
        ) AS Subconsulta
    """,
    
    # Modelos em estoque
    'modelos_em_estoque': """
        SELECT 
            Modelo, 
            COUNT(*) AS Quantidade
        FROM Computadores
        WHERE Usuario LIKE '%estoque%'
          AND Status NOT IN (4, 6, 8, 9, 5)  -- Excluir: Extraviado, Roubado, Descartado, Danificado, Reparo
        GROUP BY Modelo
        ORDER BY Quantidade DESC
    """,
    
    # Colaboradores ativos com equipamentos
    'colaboradores_ativos_com_equipamentos': """
        SELECT 
            Computadores.Serial, 
            Computadores.Modelo, 
            Computadores.Matricula, 
            Colaboradores.Nome 
        FROM Computadores 
        LEFT JOIN Colaboradores ON Computadores.Matricula = Colaboradores.Matricula
        WHERE Computadores.Matricula IS NOT NULL
            AND Colaboradores.Nome IS NOT NULL
    """,
    
    # KPIs de contagem
    'kpi_terceirizados_inativos': """
        SELECT COUNT(*) as total_terceirizados_inativos
        FROM Computadores C 
        JOIN Terceirizados T ON C.Matricula = T.Matricula 
        WHERE T.Situacao = 0
    """,
    
    'kpi_terceirizados_ativos': """
        SELECT COUNT(*) as total_terceirizados_ativos
        FROM Computadores C 
        JOIN Terceirizados T ON C.Matricula = T.Matricula 
        WHERE T.Situacao = 1
    """,
    
    'kpi_colaboradores_demitidos': """
        SELECT COUNT(*) as total_colaboradores_demitidos
        FROM Colaboradores  
        WHERE Situacao = 'Demitido'
    """,
    
    'kpi_colaboradores_aviso_previo': """
        SELECT COUNT(*) as total_colaboradores_aviso_previo
        FROM Colaboradores  
        WHERE Situacao = 'Aviso Prévio'
    """,
    
    'kpi_colaboradores_ativos': """
        SELECT COUNT(*) as total_colaboradores_ativos
        FROM Colaboradores  
        WHERE Situacao = 'Ativo'
    """,
    
    'lista_computadores': """
        SELECT Serial
        FROM Computadores
        WHERE Serial IS NOT NULL
          AND Status NOT IN (4, 6, 8, 9, 5)  -- Excluir: Extraviado, Roubado, Descartado, Danificado, Reparo
    """,
    
    # Equipamentos alocados (não estoque, com matrícula)
    'kpi_equipamentos_alocados': """
        SELECT COUNT(*) as total_equipamentos_alocados
        FROM Computadores
        WHERE Matricula IS NOT NULL
          AND (Usuario IS NULL OR Usuario NOT LIKE '%estoque%')
          AND Status NOT IN (4, 6, 8, 9, 5)  -- Excluir: Extraviado, Roubado, Descartado, Danificado, Reparo
    """,
    
    'kpi_equipamentos_sem_dono': """
        SELECT COUNT(*) as total_equipamentos_descartados
        FROM Computadores
        WHERE Status IN (4, 6, 8, 9)  -- Extraviado, Roubado, Descartado, Danificado
    """,
    
    'kpi_colaboradores_ativos_sem_computador': """
        SELECT COUNT(*) as total_colaboradores_ativos_sem_computador
        FROM Colaboradores c
        LEFT JOIN Computadores comp ON comp.Matricula = c.Matricula
        WHERE c.Situacao = 'Ativo'
          AND comp.Matricula IS NULL
    """,
    
    'kpi_demitidos_com_equipamentos': """
        SELECT COUNT(DISTINCT c.Matricula) as total_demitidos_com_equipamentos
        FROM Colaboradores c 
        LEFT JOIN Computadores comp ON comp.Matricula = c.Matricula 
        LEFT JOIN Perifericos p ON p.Matricula = c.Matricula 
        WHERE c.Situacao = 'Demitido'     
            AND c.Nome IS NOT NULL     
            AND comp.Modelo IS NOT NULL     
            AND (comp.ID IS NOT NULL OR p.ID IS NOT NULL)
    """,
    
    'kpi_colaboradores_ativos_com_equipamentos': """
        SELECT COUNT(*) as total_colaboradores_ativos_com_equipamentos
        FROM Computadores 
        LEFT JOIN Colaboradores ON Computadores.Matricula = Colaboradores.Matricula
        WHERE Computadores.Matricula IS NOT NULL
            AND Colaboradores.Nome IS NOT NULL
    """,
    
    # Consultas adicionais básicas
    'total_computadores': """
        SELECT COUNT(*) as total_computadores
        FROM Computadores
        WHERE Status NOT IN (4, 6, 8, 9, 5)  -- Excluir: Extraviado, Roubado, Descartado, Danificado, Reparo
    """,
    
    'kpi_equipamentos_alugados': """
        SELECT COUNT(*) as total_equipamentos_alugados
        FROM Computadores
        WHERE Modelo LIKE '%Samsung%' OR Modelo LIKE '%SAMSUNG%' OR Modelo LIKE '%samsung%'
        AND Status NOT IN (4, 6, 8, 9, 5)  -- Excluir: Extraviado, Roubado, Descartado, Danificado, Reparo
    """,
    
    'computadores_por_modelo': """
        SELECT 
            Modelo,
            COUNT(*) as quantidade
        FROM Computadores
        WHERE Modelo IS NOT NULL
          AND Status NOT IN (4, 6, 8, 9, 5)  -- Excluir: Extraviado, Roubado, Descartado, Danificado, Reparo
        GROUP BY Modelo
        ORDER BY quantidade DESC
    """,
    
    'usuarios_por_setor': """
        SELECT 
            COALESCE(c.CCusto, 'Sem Setor') as Setor,
            COUNT(*) as quantidade
        FROM Colaboradores c
        WHERE c.Situacao NOT IN ('Demitido', 'Aviso Prévio')
        GROUP BY c.CCusto
        ORDER BY quantidade DESC
    """,
    
    'ocupacao_por_setor': """
        SELECT 
            COALESCE(c.CCusto, 'Sem Setor') as Setor,
            COUNT(DISTINCT c.Matricula) as TotalColaboradores,
            COUNT(DISTINCT CASE WHEN comp.Matricula IS NOT NULL THEN c.Matricula END) as ComEquipamento,
            CASE 
                WHEN COUNT(DISTINCT c.Matricula) > 0 
                THEN ROUND(
                    (COUNT(DISTINCT CASE WHEN comp.Matricula IS NOT NULL THEN c.Matricula END) * 100.0) / 
                    COUNT(DISTINCT c.Matricula), 1
                )
                ELSE 0 
            END as TaxaOcupacao
        FROM Colaboradores c
        LEFT JOIN Computadores comp ON comp.Matricula = c.Matricula
        WHERE c.Situacao = 'Ativo'
        GROUP BY c.CCusto
        HAVING COUNT(DISTINCT c.Matricula) > 0
        ORDER BY TaxaOcupacao DESC
    """,
    
    'colaboradores_por_chefia': """
        SELECT 
            COALESCE(c.Chefia, 'Sem Chefia') as Chefia,
            COUNT(*) as quantidade
        FROM Colaboradores c
        WHERE c.Situacao = 'Ativo'
        GROUP BY c.Chefia
        ORDER BY quantidade DESC
    """,
    
    'colaboradores_detalhado': """
        SELECT 
            c.Nome,
            c.Matricula,
            COALESCE(c.CCusto, 'Sem Setor') as Setor,
            COALESCE(c.Chefia, 'Sem Chefia') as Chefia,
            c.Situacao,
            CASE 
                WHEN comp.Serial IS NOT NULL THEN 'Com Equipamento'
                ELSE 'Sem Equipamento'
            END as StatusEquipamento,
            comp.Modelo as ModeloComputador
        FROM Colaboradores c
        LEFT JOIN Computadores comp ON comp.Matricula = c.Matricula
        WHERE c.Situacao = 'Ativo'
        ORDER BY c.Nome
    """,
    
    'equipamentos_detalhado': """
        SELECT 
            c.Serial,
            c.Modelo,
            COALESCE(c.Usuario, 'Sem Usuário') as Usuario,
            COALESCE(c.Matricula, 'Sem Matrícula') as Matricula,
            COALESCE(col.Nome, 'Não Alocado') as NomeColaborador,
            CASE 
                WHEN c.Usuario LIKE '%estoque%' THEN 'Estoque'
                WHEN c.Matricula IS NOT NULL THEN 'Em Uso'
                ELSE 'Descartado'
            END as Status
        FROM Computadores c
        LEFT JOIN Colaboradores col ON col.Matricula = c.Matricula
        ORDER BY c.Modelo, c.Serial
    """,
    
    'equipamentos_por_status': """
        SELECT 
            CASE 
                WHEN c.Usuario LIKE '%estoque%' THEN 'Estoque'
                WHEN c.Matricula IS NOT NULL THEN 'Em Uso'
                ELSE 'Sem Dono'
            END as Status,
            COUNT(*) as quantidade
        FROM Computadores c
        GROUP BY 
            CASE 
                WHEN c.Usuario LIKE '%estoque%' THEN 'Estoque'
                WHEN c.Matricula IS NOT NULL THEN 'Em Uso'
                ELSE 'Sem Dono'
            END
        ORDER BY quantidade DESC
    """,
    
    'equipamentos_por_status': """
        SELECT 
            CASE 
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'EM ESTOQUE' THEN 'Em Estoque'
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'ACESSO REMOTO' THEN 'Acesso Remoto' 
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'DESCARTADO' THEN 'Descartado'
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'DEVOLVIDO' THEN 'Devolvido'
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'DANIFICADO' THEN 'Danificado'
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'EXTRAVIADO' THEN 'Extraviado'
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'ROUBADO' THEN 'Roubado'
                WHEN c.Matricula IS NOT NULL THEN 'Em Uso'
                ELSE 'Sem Status'
            END as Status,
            COUNT(*) as quantidade
        FROM Computadores c
        GROUP BY 
            CASE 
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'EM ESTOQUE' THEN 'Em Estoque'
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'ACESSO REMOTO' THEN 'Acesso Remoto'
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'DESCARTADO' THEN 'Descartado'
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'DEVOLVIDO' THEN 'Devolvido'
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'DANIFICADO' THEN 'Danificado'
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'EXTRAVIADO' THEN 'Extraviado'
                WHEN UPPER(COALESCE(c.Usuario, 'SEM STATUS')) = 'ROUBADO' THEN 'Roubado'
                WHEN c.Matricula IS NOT NULL THEN 'Em Uso'
                ELSE 'Sem Status'
            END
        ORDER BY quantidade DESC
    """,
    
    'equipamentos_criticidade': """
        SELECT 
            c.Serial,
            c.Modelo,
            COALESCE(c.Usuario, 'Sem Usuário') as Usuario,
            COALESCE(c.Matricula, 'Sem Matrícula') as Matricula,
            COALESCE(col.Nome, 'Não Alocado') as NomeColaborador,
            CASE 
                WHEN c.Usuario LIKE '%estoque%' THEN 'Estoque'
                WHEN c.Matricula IS NOT NULL THEN 'Em Uso'
                ELSE 'Descartado'
            END as Status
        FROM Computadores c
        LEFT JOIN Colaboradores col ON col.Matricula = c.Matricula
        WHERE c.Serial IS NOT NULL
        ORDER BY c.Modelo, c.Serial
    """,
    
    # Novas queries para análises mais avançadas
    'custos_por_setor': """
        SELECT 
            COALESCE(col.CCusto, 'Sem Setor') as Setor,
            COUNT(DISTINCT c.Serial) as QuantidadeEquipamentos,
            COUNT(DISTINCT col.Matricula) as QuantidadeColaboradores,
            CASE 
                WHEN COUNT(DISTINCT col.Matricula) > 0 
                THEN ROUND(CAST(COUNT(DISTINCT c.Serial) AS FLOAT) / COUNT(DISTINCT col.Matricula), 2)
                ELSE 0 
            END as EquipamentoPorColaborador
        FROM Colaboradores col
        LEFT JOIN Computadores c ON c.Matricula = col.Matricula
        WHERE col.Situacao = 'Ativo'
        GROUP BY col.CCusto
        ORDER BY QuantidadeEquipamentos DESC
    """,
    
    'rotatividade_analise': """
        SELECT 
            YEAR(GETDATE()) as Ano,
            COUNT(CASE WHEN Situacao = 'Demitido' THEN 1 END) as Demitidos,
            COUNT(CASE WHEN Situacao = 'Aviso Prévio' THEN 1 END) as AvisoPrevio,
            COUNT(CASE WHEN Situacao = 'Ativo' THEN 1 END) as Ativos,
            ROUND(
                (COUNT(CASE WHEN Situacao IN ('Demitido', 'Aviso Prévio') THEN 1 END) * 100.0) / 
                NULLIF(COUNT(*), 0), 2
            ) as TaxaRotatividade
        FROM Colaboradores
    """,
    
    'equipamentos_idade_critica': """
        SELECT 
            c.Serial,
            c.Modelo,
            COALESCE(col.Nome, 'Não Alocado') as Usuario,
            COALESCE(col.CCusto, 'Sem Setor') as Setor,
            NULL as IdadeAnos,
            'Sem Data de Compra' as StatusIdade
        FROM Computadores c
        LEFT JOIN Colaboradores col ON col.Matricula = c.Matricula
        WHERE c.Serial IS NOT NULL
        ORDER BY c.Modelo, c.Serial
    """,
    
    'performance_mensal': """
        SELECT 
            FORMAT(GETDATE(), 'yyyy-MM') as MesAtual,
            COUNT(CASE WHEN c.Situacao = 'Ativo' THEN 1 END) as ColaboradoresAtivos,
            COUNT(DISTINCT comp.Serial) as EquipamentosAlocados,
            COUNT(CASE WHEN comp.Usuario LIKE '%estoque%' THEN 1 END) as EquipamentosEstoque,
            COUNT(CASE WHEN comp.Matricula IS NULL AND (comp.Usuario IS NULL OR comp.Usuario NOT LIKE '%estoque%') THEN 1 END) as EquipamentosSemDono
        FROM Colaboradores c
        FULL OUTER JOIN Computadores comp ON comp.Matricula = c.Matricula
    """,
    
    'alertas_sistema': """
        SELECT 
            'Colaboradores Demitidos com Equipamentos' as TipoAlerta,
            COUNT(DISTINCT c.Matricula) as Quantidade,
            'Alto' as Prioridade
        FROM Colaboradores c 
        LEFT JOIN Computadores comp ON comp.Matricula = c.Matricula 
        WHERE c.Situacao = 'Demitido' AND comp.ID IS NOT NULL
        
        UNION ALL
        
        SELECT 
            'Equipamentos Descartados/Danificados' as TipoAlerta,
            COUNT(*) as Quantidade,
            'Médio' as Prioridade
        FROM Computadores 
        WHERE Status IN (4, 6, 8, 9)  -- Extraviado, Roubado, Descartado, Danificado
        
        UNION ALL
        
        SELECT 
            'Colaboradores Ativos Sem Equipamento' as TipoAlerta,
            COUNT(*) as Quantidade,
            'Baixo' as Prioridade
        FROM Colaboradores c
        LEFT JOIN Computadores comp ON comp.Matricula = c.Matricula
        WHERE c.Situacao = 'Ativo' AND comp.Matricula IS NULL
    """,
    
    'equipamentos_por_status_real': """
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
    """,
    
    'equipamentos_detalhado_status': """
        SELECT 
            c.Serial,
            c.Modelo,
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
            END as StatusRealizado,
            COALESCE(c.Usuario, 'Sem Usuário') as Usuario,
            COALESCE(c.Matricula, 'Sem Matrícula') as Matricula,
            COALESCE(col.Nome, 'Não Alocado') as NomeColaborador,
            COALESCE(col.CCusto, 'Sem Setor') as Setor
        FROM Computadores c
        LEFT JOIN Colaboradores col ON col.Matricula = c.Matricula
        WHERE c.Serial IS NOT NULL
        ORDER BY c.Status, c.Modelo, c.Serial
    """,
    
    'equipamentos_criticos_por_status': """
        SELECT 
            CASE 
                WHEN c.Status = 8 THEN 'Descartado'
                WHEN c.Status = 9 THEN 'Danificado'
                WHEN c.Status = 4 THEN 'Extraviado'
                WHEN c.Status = 6 THEN 'Roubado'
                ELSE 'Outros'
            END as StatusCritico,
            COUNT(*) as Quantidade,
            NULL as IdadeMedia
        FROM Computadores c
        WHERE c.Status IN (4, 6, 8, 9)  -- Extraviado, Roubado, Descartado, Danificado
        GROUP BY 
            CASE 
                WHEN c.Status = 8 THEN 'Descartado'
                WHEN c.Status = 9 THEN 'Danificado'
                WHEN c.Status = 4 THEN 'Extraviado'
                WHEN c.Status = 6 THEN 'Roubado'
                ELSE 'Outros'
            END
        ORDER BY Quantidade DESC
    """,
    
    'diagnostico_status_simples': """
        SELECT 
            Status,
            COUNT(*) as Quantidade
        FROM Computadores
        GROUP BY Status
        ORDER BY Status
    """
}

# ==================== FUNÇÕES DE REDUÇÃO DE CUSTOS ====================
def load_desligamento_data():
    """Carrega e processa os dados do Excel para redução de custos"""
    try:
        df = pd.read_excel('desligamento.xlsx')
        
        df = df.dropna(subset=['CT'])
        df = df[~df['CT'].astype(str).str.contains('Total', na=False)]
        df = df[df['CT'] != 'CT']  # Remove cabeçalhos duplicados
        
        df['CT'] = pd.to_numeric(df['CT'], errors='coerce')
        df = df.dropna(subset=['CT'])
        
        for col in ['Valor Economizado/mês', 'Valor Economizado/ano']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if 'Valor Economizado/ano' not in df.columns or df['Valor Economizado/ano'].sum() == 0:
            df['Valor Economizado/ano'] = df['Valor Economizado/mês'] * 12
        
        return df
        
    except FileNotFoundError:
        print("Arquivo 'desligamento.xlsx' não encontrado na raiz do projeto!")
        # Retorna dados fictícios para teste
        return pd.DataFrame({
            'CT': [1, 2, 3, 4, 5],
            'Devolução': ['Notebook', 'Monitor', 'Impressora', 'Notebook', 'Monitor'],
            'Valor Economizado/mês': [1000, 500, 300, 1200, 450],
            'Valor Economizado/ano': [12000, 6000, 3600, 14400, 5400],
            'Situação': ['Devolvido em 01/01/2024', 'Aguardando', 'Devolvido em 15/01/2024', 'Aguardando', 'Aguardando']
        })
    except Exception as e:
        print(f"Erro ao carregar dados: {str(e)}")
        return None

def extract_date_from_situation(situation):
    """Extrai data da coluna situação"""
    if pd.isna(situation) or 'Aguardando' in str(situation):
        return None
    
    try:
        # Procura por data no formato dd/mm/yyyy
        import re
        date_pattern = r'(\d{2}/\d{2}/\d{4})'
        match = re.search(date_pattern, str(situation))
        if match:
            return pd.to_datetime(match.group(1), format='%d/%m/%Y')
    except:
        pass
    return None

def format_currency(value):
    """Formata valor como moeda brasileira"""
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def create_alert_card(title, count, priority, icon):
    """Cria card de alerta"""
    color_map = {
        'Alto': '#dc3545',
        'Médio': '#ffc107', 
        'Baixo': '#28a745'
    }
    
    return html.Div([
        html.Div([
            html.I(className=f"{icon} alert-icon"),
            html.Div([
                html.H4(str(count), className="alert-count"),
                html.P(title, className="alert-title"),
                html.Span(f"Prioridade {priority}", className="alert-priority")
            ], className="alert-content")
        ], className="alert-inner")
    ], className="alert-card", style={
        'border-left': f'4px solid {color_map.get(priority, "#6c757d")}'
    })

# Valor fixo atual
VALOR_FIXO_MENSAL = 102359.03
VALOR_FIXO_ANUAL = VALOR_FIXO_MENSAL * 12

# ==================== INICIALIZAÇÃO DA APP ====================
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {
              margin: 0;
              padding: 0;
              box-sizing: border-box;
            }
            
            body {
              font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
              background: #f8f9fa;
              color: #1e1e1e;
              line-height: 1.6;
              overflow-x: hidden;
              font-weight: 400;
            }
            
            .dashboard-container {
              display: flex;
              min-height: 100vh;
            }
            
            .sidebar {
              width: 260px;
              background: linear-gradient(180deg, #1e1e1e 0%, #0f0f0f 100%);
              color: white;
              position: fixed;
              height: 100vh;
              left: 0;
              top: 0;
              z-index: 1000;
              box-shadow: 4px 0 20px rgba(0,0,0,0.2);
              border-right: 2px solid #333;
            }
            
            .sidebar-header {
              padding: 2.5rem 1.5rem 1.5rem 1.5rem;
              border-bottom: 2px solid #333;
              text-align: center;
              background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%);
              -webkit-background-clip: text;
              background-clip: text;
            }
            
            .sidebar-header h1 {
              font-size: 1.75rem;
              font-weight: 900;
              margin-bottom: 0.5rem;
              color: white;
              text-shadow: 0 2px 4px rgba(0,0,0,0.3);
              letter-spacing: -0.5px;
            }
            
            .sidebar-header p {
              color: #ccc;
              font-size: 0.9rem;
              font-weight: 400;
            }
            
            .sidebar-nav {
              padding: 2rem 0;
            }
            
            .nav-item {
              display: flex;
              align-items: center;
              padding: 1.25rem 1.5rem;
              color: #bbb;
              transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
              border-left: 4px solid transparent;
              cursor: pointer;
              position: relative;
            }
            
            .nav-item:hover, .nav-item.active {
              background: linear-gradient(90deg, rgba(255,255,255,0.1) 0%, transparent 100%);
              color: white;
              border-left-color: #FFFFFF;
              transform: translateX(5px);
            }
            
            .nav-item:hover {
              cursor: pointer;
            }
            
            .nav-item i {
              margin-right: 1rem;
              width: 20px;
              text-align: center;
              font-size: 1.1rem;
            }
            
            #nav-reducao-custos.active {
              color: white !important;
            }
            
            .alert-card {
              background: white;
              border-radius: 8px;
              padding: 1rem;
              margin: 0.5rem;
              box-shadow: 0 2px 8px rgba(0,0,0,0.1);
              border: 1px solid #e9ecef;
              transition: transform 0.2s;
            }
            
            .alert-card:hover {
              transform: translateY(-2px);
              box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .alert-inner {
              display: flex;
              align-items: center;
            }
            
            .alert-icon {
              font-size: 2rem;
              margin-right: 1rem;
              color: #6c757d;
            }
            
            .alert-count {
              font-size: 1.5rem;
              font-weight: 700;
              margin: 0;
              color: #1e1e1e;
            }
            
            .alert-title {
              font-size: 0.9rem;
              margin: 0;
              color: #6c757d;
            }
            
            .alert-priority {
              font-size: 0.8rem;
              padding: 0.2rem 0.5rem;
              border-radius: 4px;
              background: #f8f9fa;
              color: #495057;
            }
            
            .alerts-grid {
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
              gap: 1rem;
              margin: 2rem 0;
            }
            
            .main-content {
              margin-left: 260px;
              padding: 2.5rem;
              width: calc(100% - 260px);
              min-height: 100vh;
              background: #f8f9fa;
            }
            
            .kpi-grid {
              display: grid !important;
              grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)) !important;
              gap: 2rem !important;
              margin-bottom: 3rem !important;
              width: 100% !important;
              padding: 0 1rem !important;
            }
            
            .kpi-card {
              background: white;
              border-radius: 12px;
              padding: 2rem;
              box-shadow: 0 8px 25px rgba(0,0,0,0.08);
              border: 1px solid #e9ecef;
              background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
              position: relative;
              transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
              overflow: hidden;
            }
            
            .kpi-card::before {
              content: '';
              position: absolute;
              top: 0;
              left: 0;
              right: 0;
              height: 4px;
              background: linear-gradient(90deg, #000000 0%, #333333 25%, #666666 50%, #999999 75%, #cccccc 100%);
              z-index: 1;
            }
            
            .kpi-card:hover {
              transform: translateY(-3px);
              box-shadow: 0 15px 40px rgba(0,0,0,0.15);
            }
            
            .kpi-card::after {
              content: '';
              position: absolute;
              top: -50%;
              right: -50%;
              width: 100px;
              height: 100px;
              background: linear-gradient(45deg, rgba(255,107,107,0.1) 0%, rgba(78,205,196,0.1) 100%);
              border-radius: 50%;
              z-index: 0;
            }
            
            .kpi-value {
              font-size: 2.4rem;
              font-weight: 600;
              color: #1e1e1e;
              margin-bottom: 0.5rem;
              position: relative;
              z-index: 2;
              letter-spacing: -0.5px;
              line-height: 1.1;
              font-family: 'Inter', sans-serif;
            }
            
            .kpi-label {
              color: #6c757d;
              font-size: 0.9rem;
              font-weight: 500;
              position: relative;
              z-index: 2;
              text-transform: none;
              letter-spacing: 0.2px;
              line-height: 1.3;
              font-family: 'Inter', sans-serif;
            }
            
            .chart-card {
              background: white;
              border-radius: 16px;
              padding: 2.5rem;
              box-shadow: 0 8px 25px rgba(0,0,0,0.08);
              border: 1px solid #e9ecef;
              margin-bottom: 2.5rem;
              transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            .chart-card:hover {
              box-shadow: 0 12px 35px rgba(0,0,0,0.12);
            }
            
            .chart-card-black {
              background: linear-gradient(145deg, #1e1e1e 0%, #0f0f0f 100%);
              border-radius: 16px;
              padding: 2.5rem;
              box-shadow: 0 8px 25px rgba(0,0,0,0.3);
              border: 1px solid #333;
              margin-bottom: 2.5rem;
              transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
              color: white;
            }
            
            .chart-card-black:hover {
              box-shadow: 0 12px 35px rgba(0,0,0,0.5);
              transform: translateY(-2px);
            }
            
            .chart-card-black h4,
            .chart-card-black h5 {
              color: white !important;
            }
            
            .chart-card-black .plotly {
              background: transparent !important;
            }
            
            .status-card-white {
              background: white !important;
              border: 2px solid #000000 !important;
              border-radius: 8px !important;
              box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
            }
            
            .header {
              background: white;
              border-radius: 16px;
              padding: 2rem 2.5rem;
              margin-bottom: 2.5rem;
              box-shadow: 0 8px 25px rgba(0,0,0,0.08);
              border: 1px solid #e9ecef;
              position: relative;
              overflow: hidden;
            }
            
            .header::before {
              content: '';
              position: absolute;
              top: 0;
              left: 0;
              right: 0;
              bottom: 0;
              background: linear-gradient(135deg, rgba(255,107,107,0.02) 0%, rgba(78,205,196,0.02) 100%);
              z-index: 0;
            }
            
            .header-content {
              display: flex;
              justify-content: space-between;
              align-items: center;
              position: relative;
              z-index: 1;
            }
            
            .header-title h1 {
              font-size: 2.25rem;
              font-weight: 900;
              color: #1e1e1e;
              margin-bottom: 0.5rem;
              letter-spacing: -0.5px;
            }
            
            .header-title p {
              color: #6c757d;
              font-size: 1.1rem;
              font-weight: 500;
            }
            
            .header-actions {
              display: flex;
              gap: 1.5rem;
              align-items: center;
            }
            
            .time-badge {
              background: linear-gradient(135deg, #1e1e1e 0%, #333 100%);
              color: white;
              padding: 0.75rem 1.5rem;
              border-radius: 8px;
              font-weight: 600;
              font-size: 0.9rem;
              box-shadow: 0 4px 15px rgba(0,0,0,0.2);
              letter-spacing: 0.5px;
            }
            
            .refresh-btn {
              background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
              color: white;
              border: none;
              padding: 0.75rem 1.5rem;
              border-radius: 8px;
              cursor: pointer;
              transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
              font-weight: 600;
              box-shadow: 0 4px 15px rgba(0,0,0,0.2);
              letter-spacing: 0.5px;
            }
            
            .refresh-btn:hover {
              background: linear-gradient(135deg, #1e1e1e 0%, #000 100%);
              transform: translateY(-2px);
              box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            }
            
            .refresh-btn i {
              margin-right: 0.5rem;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ==================== LAYOUT FUNCTIONS ====================
def create_sidebar():
    return html.Div([
        html.Div([
            html.H1("Portal TI", className="mb-3"),
            html.P("Dashboard Analytics", style={'opacity': '0.8', 'font-size': '0.9rem'})
        ], className="sidebar-header"),
        
        html.Div([
            html.Div([
                html.I(className="fas fa-chart-line"),
                "Analytics Dashboard"
            ], className="nav-item", id="nav-dashboard"),
            
            html.Div([
                html.I(className="fas fa-desktop"),
                "Equipamentos"
            ], className="nav-item", id="nav-equipamentos"),
            
            html.Div([
                html.I(className="fas fa-users"),
                "Colaboradores"
            ], className="nav-item", id="nav-colaboradores"),
            
            html.Div([
                html.I(className="fas fa-dollar-sign"),
                "Redução de Custos"
            ], className="nav-item", id="nav-reducao-custos"),
            
            html.Div([
                html.I(className="fas fa-mobile-alt"),
                "Linhas Móveis"
            ], className="nav-item", id="nav-linhas-moveis"),
            
            html.Div([
                html.I(className="fas fa-cog"),
                "Configurações"
            ], className="nav-item", id="nav-config")
        ], className="sidebar-nav", id="sidebar-nav-container")
    ], className="sidebar")

def create_kpi_card(title, value, icon_class, subtitle=None):
    return html.Div([
        html.Div([
            html.Div([
                html.I(className=icon_class, style={
                    'fontSize': '2rem',
                    'color': '#6c757d',
                    'marginBottom': '1rem'
                })
            ], style={'textAlign': 'right'}),
        ], className="kpi-header"),
        html.Div(str(value), className="kpi-value"),
        html.Div(title, className="kpi-label"),
        html.Div(subtitle if subtitle else "", style={
            'color': '#adb5bd', 
            'font-size': '0.85rem', 
            'margin-top': '0.75rem',
            'font-weight': '500'
        })
    ], className="kpi-card")

def create_colaboradores_content():
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.H1("Gestão de Colaboradores"),
                    html.P("Análise detalhada da equipe e distribuição organizacional")
                ], className="header-title"),
                html.Div([
                    html.Span(id="current-time-colab", className="time-badge"),
                    html.Button([
                        html.I(className="fas fa-sync-alt mr-2"),
                        "Atualizar Dados"
                    ], className="refresh-btn", id="refresh-btn-colab")
                ], className="header-actions")
            ], className="header-content")
        ], className="header"),
        
        html.Div([
            html.Div([
                dcc.Graph(id="colaboradores-por-setor")
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            html.Div([
                dcc.Graph(id="colaboradores-por-chefia")
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'})
        ], style={'marginBottom': '2rem'}),
        
        html.Div([
            html.Div([
                html.H4("👥 Lista Completa de Colaboradores Ativos", style={
                    'margin-bottom': '1.5rem',
                    'color': '#1e1e1e',
                    'fontWeight': '600',
                    'fontSize': '1.1rem'
                }),
                html.Div(id="colaboradores-detalhado-table", style={
                    'maxHeight': '600px', 
                    'overflowY': 'auto',
                    'border': '1px solid #e9ecef',
                    'borderRadius': '8px'
                })
            ], className="chart-card")
        ]),
        
        dcc.Interval(
            id='interval-colaboradores',
            interval=300*1000,
            n_intervals=0
        )
    ])

def create_equipamentos_content():
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.H1("Gestão de Equipamentos"),
                    html.P("Controle completo do inventário de TI")
                ], className="header-title"),
                html.Div([
                    html.Span(id="current-time-equip", className="time-badge"),
                    html.Button([
                        html.I(className="fas fa-sync-alt mr-2"),
                        "Atualizar Dados"
                    ], className="refresh-btn", id="refresh-btn-equip")
                ], className="header-actions")
            ], className="header-content")
        ], className="header"),
        
        html.Div([
            html.Div([
                dcc.Graph(id="equipamentos-por-status")
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            html.Div([
                dcc.Graph(id="equipamentos-criticidade")
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'})
        ], style={'marginBottom': '2rem'}),
        
        html.Div([
            html.Div([
                dcc.Graph(id="equipamentos-por-modelo-full")
            ], className="chart-card", style={'width': '100%'})
        ], style={'marginBottom': '2rem'}),
        
        html.Div([
            html.Div([
                dcc.Graph(id="custos-por-setor")
            ], className="chart-card", style={'width': '100%'})
        ], style={'marginBottom': '2rem'}),
        
        html.Div([
            html.H3("📋 Análise Detalhada", style={
                'color': '#1e1e1e', 
                'marginBottom': '1rem', 
                'fontWeight': '800',
                'fontSize': '1.5rem'
            })
        ]),
        
        html.Div([
            html.Div([
                html.H4("🚨 Equipamentos Críticos por Idade", style={
                    'margin-bottom': '1.5rem',
                    'color': '#1e1e1e',
                    'fontWeight': '600',
                    'fontSize': '1.1rem'
                }),
                html.Div(id="equipamentos-criticos-table", style={
                    'maxHeight': '400px', 
                    'overflowY': 'auto',
                    'border': '1px solid #e9ecef',
                    'borderRadius': '8px'
                })
            ], className="chart-card", style={'width': '100%', 'marginBottom': '2rem'})
        ]),
        
        # Nova seção para análise de equipamentos por status
        html.Div([
            html.Div([
                html.H4("� Análise de Equipamentos por Status", style={
                    'margin-bottom': '1.5rem',
                    'color': '#1e1e1e',
                    'fontWeight': '600',
                    'fontSize': '1.1rem'
                }),
                html.Div([
                    html.Div([
                        dcc.Graph(id="equipamentos-status-chart")
                    ], style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                    
                    html.Div([
                        html.H5("Resumo por Status:", style={'margin-bottom': '1rem', 'color': '#1e1e1e'}),
                        html.Div(id="equipamentos-status-resumo")
                    ], style={'width': '60%', 'display': 'inline-block', 'paddingLeft': '2rem', 'verticalAlign': 'top'})
                ])
            ], className="chart-card", style={'width': '100%', 'marginBottom': '2rem'})
        ]),
        
        html.Div([
            html.Div([
                html.H4("� Equipamentos Críticos (Descartados/Danificados)", style={
                    'margin-bottom': '1.5rem',
                    'color': '#1e1e1e',
                    'fontWeight': '600',
                    'fontSize': '1.1rem'
                }),
                html.Div([
                    dcc.Graph(id="equipamentos-criticos-status-chart")
                ], style={'width': '100%'})
            ], className="chart-card", style={'width': '100%', 'marginBottom': '2rem'})
        ]),
        
        html.Div([
            html.Div([
                html.H4("�📋 Lista Detalhada - Todos os Equipamentos por Status", style={
                    'margin-bottom': '1.5rem',
                    'color': '#1e1e1e',
                    'fontWeight': '600',
                    'fontSize': '1.1rem'
                }),
                html.Div(id="equipamentos-status-table", style={
                    'maxHeight': '600px', 
                    'overflowY': 'auto',
                    'border': '1px solid #e9ecef',
                    'borderRadius': '8px'
                })
            ], className="chart-card", style={'width': '100%', 'marginBottom': '2rem'})
        ]),
        
        html.Div([
            html.Div([
                html.H4("💻 Inventário Completo de Equipamentos", style={
                    'margin-bottom': '1.5rem',
                    'color': '#1e1e1e',
                    'fontWeight': '600',
                    'fontSize': '1.1rem'
                }),
                html.Div(id="equipamentos-detalhado-table", style={
                    'maxHeight': '600px', 
                    'overflowY': 'auto',
                    'border': '1px solid #e9ecef',
                    'borderRadius': '8px'
                })
            ], className="chart-card")
        ]),
        
        dcc.Interval(
            id='interval-equipamentos',
            interval=300*1000,
            n_intervals=0
        )
    ])

def create_config_content():
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.H1("Configurações do Sistema"),
                    html.P("Configurações e informações do dashboard")
                ], className="header-title"),
            ], className="header-content")
        ], className="header"),
        
        html.Div([
            html.Div([
                html.H4("⚙️ Configurações de Conexão", style={
                    'margin-bottom': '1.5rem',
                    'color': '#1e1e1e',
                    'fontWeight': '600'
                }),
                html.P(f"Servidor: {DB_CONFIG['server']}", style={'marginBottom': '0.5rem'}),
                html.P(f"Banco: {DB_CONFIG['database']}", style={'marginBottom': '0.5rem'}),
                html.P(f"Usuário: {DB_CONFIG['username']}", style={'marginBottom': '0.5rem'}),
                html.P(f"Driver: {DB_CONFIG['driver']}", style={'marginBottom': '1rem'}),
                html.Button([
                    html.I(className="fas fa-database mr-2"),
                    "Testar Conexão"
                ], className="refresh-btn", id="test-connection-btn")
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            html.Div([
                html.H4("📊 Informações do Dashboard", style={
                    'margin-bottom': '1.5rem',
                    'color': '#1e1e1e',
                    'fontWeight': '600'
                }),
                html.P("Versão: 2.0", style={'marginBottom': '0.5rem'}),
                html.P("Última atualização: Setembro 2025", style={'marginBottom': '0.5rem'}),
                html.P("Atualização automática: 5 minutos", style={'marginBottom': '1rem'}),
                html.Div([
                    html.P("Powered by Wood", style={
                        'marginBottom': '0.5rem',
                        'fontWeight': '600',
                        'color': '#333',
                        'fontSize': '1.1rem'
                    })
                ], style={
                    'background': 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
                    'padding': '1rem',
                    'borderRadius': '8px',
                    'textAlign': 'center',
                    'border': '1px solid #dee2e6'
                }),
                html.Div(id="connection-status", style={'marginTop': '1rem'})
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'})
        ])
    ])

def create_linhas_moveis_content():
    """Cria conteúdo da aba de Linhas Móveis"""
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.H1("Linhas Móveis", style={'color': "#000000"}),
                    html.P("Análise de consumo dos últimos 6 meses", style={'color': '#7f8c8d'})
                ], className="header-title"),
            ], className="header-content")
        ], className="header"),
        
        # Navegação por abas
        html.Div([
            dcc.Tabs(id="linhas-tabs", value="sem-uso", children=[
                dcc.Tab(label="Linhas sem consumo", value="sem-uso", style={'fontFamily': 'Inter, sans-serif'}),
                dcc.Tab(label="Linhas em Uso", value="com-uso", style={'fontFamily': 'Inter, sans-serif'}),
                dcc.Tab(label="Métricas", value="metricas", style={'fontFamily': 'Inter, sans-serif'}),
            ], style={'fontFamily': 'Inter, sans-serif'})
        ], style={'margin': '20px 0'}),
        
        # Conteúdo das abas
        html.Div(id="linhas-content"),
        
        # Dados das linhas (oculto)
        html.Div(id="linhas-data", style={'display': 'none'}, children=[
            html.Script("""
                window.linhasSemUso = [
                    { telefone: '21-96729-8530', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-96747-1151', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-96747-4750', uso: 0.0, sessoes: 0, usuario: 'ALEX DE MELO MACHADO' },
                    { telefone: '21-96754-3199', uso: 0.0, sessoes: 0, usuario: 'HIAGO PEREIRA DAUDT' },
                    { telefone: '21-97161-9941', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-97218-5152', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-97286-8541', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-97295-0716', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-97546-4883', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-99308-8451', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-99417-4039', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-99573-5910', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-99582-8720', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-99628-2229', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-99638-6268', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-99642-6126', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-99720-0671', uso: 0.0, sessoes: 0, usuario: 'FRANCILEI ALVES PEREIRA' },
                    { telefone: '21-99748-9522', uso: 0.0, sessoes: 0, usuario: 'DIOGO FERREIRA RODRIGUES' },
                    { telefone: '21-99765-2489', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '21-99883-1246', uso: 0.0, sessoes: 0, usuario: 'MARCELO DELGADO LOPES' },
                    { telefone: '21-99927-7527', uso: 0.0, sessoes: 0, usuario: 'CARLOS EDUARDO FERREIRA' },
                    { telefone: '22-99221-6510', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' },
                    { telefone: '22-99256-3638', uso: 0.0, sessoes: 0, usuario: 'SEM CONSUMO RELEVANTE' }
                ];
            """)
        ]),
        
        dcc.Interval(
            id='interval-linhas',
            interval=300*1000,
            n_intervals=0
        )
    ])

def create_reducao_custos_content():
    """Cria conteúdo da aba de Redução de Custos"""
    # Carrega dados de desligamento
    df = load_desligamento_data()
    
    if df is None:
        return html.Div([
            html.H1("Erro no Sistema", style={'color': '#000', 'text-align': 'center', 'margin-top': '2rem'}),
            html.P("Não foi possível carregar os dados. Verifique o arquivo desligamento.xlsx.", 
                   style={'text-align': 'center', 'color': '#666'})
        ])
    
    # Adiciona colunas calculadas
    df['Data_Devolucao'] = df['Situação'].apply(extract_date_from_situation)
    df['Status'] = df['Situação'].apply(lambda x: 'Devolvido' if 'Devolvido' in str(x) else 'Aguardando')
    
    # Cálculos dos KPIs
    total_economia_mensal = df['Valor Economizado/mês'].sum()
    total_economia_anual = df['Valor Economizado/ano'].sum()
    
    economia_devolvidos_mensal = df[df['Status'] == 'Devolvido']['Valor Economizado/mês'].sum()
    economia_devolvidos_anual = df[df['Status'] == 'Devolvido']['Valor Economizado/ano'].sum()
    
    economia_pendente_mensal = df[df['Status'] == 'Aguardando']['Valor Economizado/mês'].sum()
    economia_pendente_anual = df[df['Status'] == 'Aguardando']['Valor Economizado/ano'].sum()
    
    qtd_devolvidos = len(df[df['Status'] == 'Devolvido'])
    qtd_aguardando = len(df[df['Status'] == 'Aguardando'])
    
    custo_atual_mensal = VALOR_FIXO_MENSAL - economia_devolvidos_mensal
    reducao_percentual = (economia_devolvidos_mensal / VALOR_FIXO_MENSAL) * 100 if VALOR_FIXO_MENSAL > 0 else 0
    
    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.Div([
                    html.H1("Redução de Custos"),
                    html.P("Monitoramento da economia com desligamentos e devoluções de equipamentos")
                ], className="header-title"),
                html.Div([
                    html.Span(id="current-time-reducao", className="time-badge"),
                    html.Button([
                        html.I(className="fas fa-sync-alt mr-2"),
                        "Atualizar Dados"
                    ], className="refresh-btn", id="refresh-btn-reducao")
                ], className="header-actions")
            ], className="header-content")
        ], className="header"),
        
        # KPIs Grid
        html.Div([
            create_kpi_card(
                "Economia Total Potencial/Mês", 
                format_currency(total_economia_mensal),
                "fas fa-chart-line",
                f"Anual: {format_currency(total_economia_anual)}"
            ),
            create_kpi_card(
                "Economia Realizada/Mês", 
                format_currency(economia_devolvidos_mensal),
                "fas fa-check-circle",
                f"{qtd_devolvidos} itens - {reducao_percentual:.1f}%"
            ),
            create_kpi_card(
                "Economia Pendente/Mês", 
                format_currency(economia_pendente_mensal),
                "fas fa-clock",
                f"{qtd_aguardando} itens aguardando"
            ),
            create_kpi_card(
                "Custo Atual/Mês", 
                format_currency(custo_atual_mensal),
                "fas fa-dollar-sign",
                f"Reduzido em {format_currency(economia_devolvidos_mensal)}"
            )
        ], className="kpi-grid"),
        
        # Charts
        html.Div([
            html.Div([
                html.Div([
                    html.H3("Evolução da Redução de Custos", className="chart-title")
                ]),
                dcc.Graph(id='timeline-reducao-chart')
            ], className="chart-card", style={'width': '65%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            html.Div([
                html.Div([
                    html.H3("Status dos Equipamentos", className="chart-title")
                ]),
                dcc.Graph(id='status-reducao-pie-chart')
            ], className="chart-card", style={'width': '33%', 'display': 'inline-block'})
        ], style={'marginBottom': '2rem'}),
        
        # Gráfico por tipo de equipamento
        html.Div([
            html.Div([
                html.H3("Economia por Tipo de Equipamento", className="chart-title")
            ]),
            dcc.Graph(id='tipo-reducao-bar-chart')
        ], className="chart-card", style={'marginBottom': '2rem'}),
        
        # Tabela detalhada
        html.Div([
            html.Div([
                html.H3("Detalhamento dos Equipamentos", className="chart-title")
            ]),
            html.Div(id='reducao-data-table')
        ], className="chart-card"),
        
        # Store para dados
        dcc.Store(id='reducao-data-store', data=df.to_dict('records')),
        
        # Interval para atualização automática
        dcc.Interval(
            id='interval-reducao-custos',
            interval=300*1000,
            n_intervals=0
        )
    ])

def create_dashboard_content():
    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.Div([
                    html.H1("Portal TI - Dashboard Analytics"),
                ], className="header-title"),
                html.Div([
                    html.Button([
                        html.I(className="fas fa-sync-alt mr-2"),
                        "Atualizar Dados"
                    ], className="refresh-btn", id="refresh-btn")
                ], className="header-actions")
            ], className="header-content")
        ], className="header"),

        # KPIs Grid
        html.Div(id="kpi-cards", className="kpi-grid"),
        
        # Seção de Alertas e Performance
        html.Div([
            html.H3("🚨 Central de Alertas", style={
                'color': '#1e1e1e', 
                'marginBottom': '1rem', 
                'fontWeight': '800',
                'fontSize': '1.3rem'
            }),
            html.Div(id="alerts-section", className="alerts-grid")
        ], style={'marginBottom': '2rem'}),
        
        # Charts Grid - 2 columns
        html.Div([
            html.Div([
                dcc.Graph(id="colaboradores-situacao")
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            html.Div([
                dcc.Graph(id="computadores-por-modelo")
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'})
        ], style={'marginBottom': '2rem'}),
        
        # Second row of charts
        html.Div([
            html.Div([
                dcc.Graph(id="estoque-modelos-idade")
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            html.Div([
                dcc.Graph(id="ocupacao-por-setor")
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'})
        ], style={'marginBottom': '2rem'}),
        
        # Tables Section
        html.Div([
            html.H3("📊 Análise Detalhada", style={
                'color': '#1e1e1e', 
                'marginBottom': '2rem', 
                'fontWeight': '800',
                'fontSize': '1.5rem'
            })
        ]),
        
        html.Div([
            html.Div([
                html.H4("⚠️ Terceirizados Inativos c/ Equipamentos", style={
                    'margin-bottom': '1.5rem',
                    'color': '#1e1e1e',
                    'fontWeight': '600',
                    'fontSize': '1.1rem'
                }),
                html.Div(id="terceirizados-inativos-table")
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            html.Div([
                html.H4("🚨 Colaboradores Demitidos c/ Equipamentos", style={
                    'margin-bottom': '1.5rem',
                    'color': '#1e1e1e',
                    'fontWeight': '600',
                    'fontSize': '1.1rem'
                }),
                html.Div(id="demitidos-equipamentos-table")
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'})
        ]),
        
        dcc.Interval(
            id='interval-component',
            interval=300*1000,  
            n_intervals=0
        )
    ])

app.layout = html.Div([
    create_sidebar(),
    html.Div([
        html.Div(id="page-content")
    ], className="main-content")
], className="dashboard-container")

@app.callback(
    Output('page-content', 'children'),
    [Input('nav-dashboard', 'n_clicks'),
     Input('nav-colaboradores', 'n_clicks'),
     Input('nav-equipamentos', 'n_clicks'),
     Input('nav-reducao-custos', 'n_clicks'),
     Input('nav-linhas-moveis', 'n_clicks'),
     Input('nav-config', 'n_clicks')]
)
def display_page(dash_clicks, colab_clicks, equip_clicks, reducao_clicks, linhas_clicks, config_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return create_dashboard_content()
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'nav-colaboradores':
        return create_colaboradores_content()
    elif button_id == 'nav-equipamentos':
        return create_equipamentos_content()
    elif button_id == 'nav-reducao-custos':
        return create_reducao_custos_content()
    elif button_id == 'nav-linhas-moveis':
        return create_linhas_moveis_content()
    elif button_id == 'nav-config':
        return create_config_content()
    else:
        return create_dashboard_content()

@app.callback(
    [Output('nav-dashboard', 'className'),
     Output('nav-colaboradores', 'className'),
     Output('nav-equipamentos', 'className'),
     Output('nav-reducao-custos', 'className'),
     Output('nav-linhas-moveis', 'className'),
     Output('nav-config', 'className')],
    [Input('nav-dashboard', 'n_clicks'),
     Input('nav-colaboradores', 'n_clicks'),
     Input('nav-equipamentos', 'n_clicks'),
     Input('nav-reducao-custos', 'n_clicks'),
     Input('nav-linhas-moveis', 'n_clicks'),
     Input('nav-config', 'n_clicks')]
)
def update_nav_classes(dash_clicks, colab_clicks, equip_clicks, reducao_clicks, linhas_clicks, config_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "nav-item active", "nav-item", "nav-item", "nav-item", "nav-item", "nav-item"
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    base_class = "nav-item"
    active_class = "nav-item active"
    
    if button_id == 'nav-dashboard':
        return active_class, base_class, base_class, base_class, base_class, base_class
    elif button_id == 'nav-colaboradores':
        return base_class, active_class, base_class, base_class, base_class, base_class
    elif button_id == 'nav-equipamentos':
        return base_class, base_class, active_class, base_class, base_class, base_class
    elif button_id == 'nav-reducao-custos':
        return base_class, base_class, base_class, active_class, base_class, base_class
    elif button_id == 'nav-linhas-moveis':
        return base_class, base_class, base_class, base_class, active_class, base_class
    elif button_id == 'nav-config':
        return base_class, base_class, base_class, base_class, base_class, active_class
    else:
        return active_class, base_class, base_class, base_class, base_class, base_class

@app.callback(
    Output('current-time', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_time(n):
    return datetime.now().strftime('%H:%M:%S - %d/%m/%Y')

@app.callback(
    Output('kpi-cards', 'children'),
    [Input('interval-component', 'n_intervals'),
     Input('refresh-btn', 'n_clicks')]
)
def update_kpis(n, refresh_clicks):
    df_total = execute_query(QUERIES['total_computadores'])
    total_computadores = df_total.iloc[0]['total_computadores'] if not df_total.empty else 0
    
    df_terc_inativos = execute_query(QUERIES['kpi_terceirizados_inativos'])
    terceirizados_inativos = df_terc_inativos.iloc[0]['total_terceirizados_inativos'] if not df_terc_inativos.empty else 0
    
    df_terc_ativos = execute_query(QUERIES['kpi_terceirizados_ativos'])
    terceirizados_ativos = df_terc_ativos.iloc[0]['total_terceirizados_ativos'] if not df_terc_ativos.empty else 0
    
    df_demitidos = execute_query(QUERIES['kpi_colaboradores_demitidos'])
    colaboradores_demitidos = df_demitidos.iloc[0]['total_colaboradores_demitidos'] if not df_demitidos.empty else 0
    
    df_aviso_previo = execute_query(QUERIES['kpi_colaboradores_aviso_previo'])
    colaboradores_aviso_previo = df_aviso_previo.iloc[0]['total_colaboradores_aviso_previo'] if not df_aviso_previo.empty else 0
    
    df_demitidos_equip = execute_query(QUERIES['kpi_demitidos_com_equipamentos'])
    demitidos_com_equipamentos = df_demitidos_equip.iloc[0]['total_demitidos_com_equipamentos'] if not df_demitidos_equip.empty else 0
    df_demitidos_equip_detail = execute_query(QUERIES['colaboradores_demitidos_com_equipamentos'])
    
    df_colab_ativos_equip = execute_query(QUERIES['kpi_colaboradores_ativos_com_equipamentos'])
    colaboradores_ativos_equipamentos = df_colab_ativos_equip.iloc[0]['total_colaboradores_ativos_com_equipamentos'] if not df_colab_ativos_equip.empty else 0
    
    df_equip_sem_dono = execute_query(QUERIES['kpi_equipamentos_sem_dono'])
    equipamentos_descartados = df_equip_sem_dono.iloc[0]['total_equipamentos_descartados'] if not df_equip_sem_dono.empty else 0
    
    df_ativos_sem_pc = execute_query(QUERIES['kpi_colaboradores_ativos_sem_computador'])
    colaboradores_ativos_sem_pc = df_ativos_sem_pc.iloc[0]['total_colaboradores_ativos_sem_computador'] if not df_ativos_sem_pc.empty else 0
    
    df_estoque_total = execute_query(QUERIES['total_equipamentos_estoque'])
    total_estoque = df_estoque_total.iloc[0]['TotalEmEstoque'] if not df_estoque_total.empty and df_estoque_total.iloc[0]['TotalEmEstoque'] is not None else 0
    
    df_equip_alocados = execute_query(QUERIES['kpi_equipamentos_alocados'])
    equipamentos_alocados = df_equip_alocados.iloc[0]['total_equipamentos_alocados'] if not df_equip_alocados.empty else 0
    taxa_alocacao = 0
    if (equipamentos_alocados or 0) + (total_estoque or 0) > 0:
        total_computadores_calc = equipamentos_alocados + total_estoque
        taxa_alocacao = round((equipamentos_alocados / total_computadores_calc) * 100, 1)
    
    df_equip_alugados = execute_query(QUERIES['kpi_equipamentos_alugados'])
    equipamentos_alugados = df_equip_alugados.iloc[0]['total_equipamentos_alugados'] if not df_equip_alugados.empty else 0
    
    idade_path = os.path.join(os.path.dirname(__file__), 'idade_computadores.xlsx')
    media_idade_anos = None
    if os.path.exists(idade_path):
        try:
            plan = pd.read_excel(idade_path)
            if 'Modelo' in plan.columns and ('AnoCompra' in plan.columns or 'DataCompra' in plan.columns):
                if 'AnoCompra' in plan.columns:
                    plan['AnoCompra'] = pd.to_numeric(plan['AnoCompra'], errors='coerce')
                else:
                    raw = plan['DataCompra']
                    ano_col = pd.to_numeric(raw, errors='coerce')
                    if ano_col.notna().any():
                        plan['AnoCompra'] = ano_col.astype('Int64')
                    else:
                        plan['DataCompra'] = pd.to_datetime(plan['DataCompra'], errors='coerce')
                        plan['AnoCompra'] = plan['DataCompra'].dt.year
                plan = plan.dropna(subset=['AnoCompra'])
                plan['AnoCompra'] = plan['AnoCompra'].astype(int)
                ano_atual = datetime.now().year
                plan = plan[(plan['AnoCompra'] >= 2010) & (plan['AnoCompra'] <= ano_atual)]
                
                plan['idade_anos'] = (ano_atual - plan['AnoCompra']).astype(float)
                plan = plan[plan['idade_anos'] <= 15]
                
                if not plan['idade_anos'].empty:
                    media_idade_anos = round(plan['idade_anos'].mean(), 1)
        except Exception as _:
            media_idade_anos = None
    
    detalhes_children = []
    if not df_demitidos_equip_detail.empty:
        registros = df_demitidos_equip_detail.to_dict('records')
        agrupado = {}
        for row in registros:
            nome = row.get('Colaborador', 'Sem Nome')
            chefia = row.get('Chefia', '-')
            comp = (row.get('ModeloComputador') or '').strip()
            perif = (row.get('ModeloPeriferico') or '').strip()
            chave = (nome, chefia)
            if chave not in agrupado:
                agrupado[chave] = []
            for equip in [comp, perif]:
                if equip and equip not in agrupado[chave]:
                    agrupado[chave].append(equip)
        itens = []
        for (nome, chefia), equipamentos_list in list(agrupado.items())[:10]:
            equipamentos = ' / '.join(equipamentos_list)
            descricao = f"{nome} — {chefia}" + (f" — {equipamentos}" if equipamentos else "")
            itens.append(html.Li(descricao, style={'borderBottom': '1px solid #e5e5e5', 'padding': '4px 0'}))
        detalhes_children = [
            html.Div("Ex funcionario com equipamento", style={'fontWeight': 'bold', 'marginBottom': '0.5rem'}),
            html.Ul(itens, style={'listStyleType': 'none', 'paddingLeft': 0, 'margin': 0})
        ]
    else:
        detalhes_children = [html.Div("Sem demitidos com equipamentos", style={'fontStyle': 'italic'})]

    card_total = create_kpi_card("Total de Computadores", total_computadores, "fas fa-desktop", "Total no sistema")
    card_terc_inativos = create_kpi_card("Terceirizados Inativos", terceirizados_inativos, "fas fa-user-times", "Com equipamentos")
    card_terc_ativos = create_kpi_card("Terceirizados Ativos", terceirizados_ativos, "fas fa-user-check", "Com equipamentos")
    card_demitidos = create_kpi_card("Colaboradores Demitidos", colaboradores_demitidos, "fas fa-user-slash", f"{demitidos_com_equipamentos} com equipamentos")
    card_aviso_wrapped = html.Div(create_kpi_card("Aviso Prévio", colaboradores_aviso_previo, "fas fa-clock", "Colaboradores"), id='kpi-aviso')
    card_colab_ativos = create_kpi_card("Colaboradores c/ Equipamentos", colaboradores_ativos_equipamentos, "fas fa-users", "Ativos com equipamentos")
    card_equip_nao_controlados = create_kpi_card("Equipamentos Críticos", equipamentos_descartados, "fas fa-exclamation-triangle", "Descartados/Danificados/Extraviados")
    card_ativos_sem_pc = create_kpi_card("Ativos sem computador", colaboradores_ativos_sem_pc, "fas fa-user", "Colaboradores ativos")
    card_taxa_aloc = create_kpi_card("Taxa de alocação", f"{taxa_alocacao}%", "fas fa-chart-line", "Equip. alocados / total")
    card_media_idade = create_kpi_card("Média idade PCs", media_idade_anos if media_idade_anos is not None else '-', "fas fa-hourglass-half", "Anos")
    card_equip_alugados = create_kpi_card("Equipamentos Alugados", equipamentos_alugados, "fas fa-handshake", "Computadores Samsung")

    df_aviso_detail = execute_query(QUERIES['colaboradores_aviso_previo'])
    aviso_children = []
    if not df_aviso_detail.empty:
        nomes = df_aviso_detail['Nome'].dropna().astype(str).head(15).tolist()
        itens_aviso = [html.Li(nome, style={'borderBottom': '1px solid #e5e5e5', 'padding': '4px 0'}) for nome in nomes]
        aviso_children = [
            html.Div("Colaboradores em aviso prévio", style={'fontWeight': 'bold', 'marginBottom': '0.5rem'}),
            html.Ul(itens_aviso, style={'listStyleType': 'none', 'paddingLeft': 0, 'margin': 0})
        ]
    else:
        aviso_children = [html.Div("Sem colaboradores em aviso prévio", style={'fontStyle': 'italic'})]

    popover_aviso = dbc.Popover([
        dbc.PopoverHeader("Aviso Prévio"),
        dbc.PopoverBody(aviso_children)
    ], id='popover-aviso', target='kpi-aviso', trigger='hover', placement='auto')

    return [
        card_total,
        card_terc_inativos,
        card_terc_ativos,
        card_demitidos,
        card_aviso_wrapped,
        card_colab_ativos,
        card_equip_nao_controlados,
        card_ativos_sem_pc,
        card_taxa_aloc,
        card_media_idade,
        card_equip_alugados,
        
        popover_aviso
    ]

@app.callback(
    Output('colaboradores-situacao', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('refresh-btn', 'n_clicks')]
)
def update_colaboradores_situacao(n, refresh_clicks):
    df_demitidos = execute_query(QUERIES['kpi_colaboradores_demitidos'])
    df_aviso_previo = execute_query(QUERIES['kpi_colaboradores_aviso_previo'])
    df_ativos = execute_query(QUERIES['kpi_colaboradores_ativos'])
    
    demitidos = df_demitidos.iloc[0]['total_colaboradores_demitidos'] if not df_demitidos.empty else 0
    aviso_previo = df_aviso_previo.iloc[0]['total_colaboradores_aviso_previo'] if not df_aviso_previo.empty else 0
    ativos = df_ativos.iloc[0]['total_colaboradores_ativos'] if not df_ativos.empty else 0
    
    if demitidos == 0 and aviso_previo == 0 and ativos == 0:
        return go.Figure().add_annotation(
            text="Sem dados disponíveis", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )
    
    categories = ['Ativos', 'Demitidos', 'Aviso Prévio']
    values = [ativos, demitidos, aviso_previo]
    colors = ['#00d4aa', '#ff6b6b', '#ffc107']
    
    fig = px.pie(values=values, names=categories, 
                 title='<b>Situação dos Colaboradores</b>',
                 color_discrete_sequence=colors)
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>',
        marker=dict(line=dict(color='#ffffff', width=3))
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e1e1e', size=12, family='Inter'),
        title=dict(
            font=dict(size=18, color='#1e1e1e', family='Inter'),
            x=0.5,
            y=0.95
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
            font=dict(size=11)
        ),
        margin=dict(t=60, b=60, l=20, r=20),
        height=400
    )
    
    return fig


@app.callback(
    Output('computadores-por-modelo', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('refresh-btn', 'n_clicks')]
)
def update_computadores_por_modelo(n, refresh_clicks):
    df = execute_query(QUERIES['computadores_por_modelo'])
    
    if df.empty:
        return go.Figure().add_annotation(
            text="Sem dados disponíveis", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )
    
    df_top = df.head(8)
    
    colors = ['#6366f1', '#8b5cf6', '#ec4899', '#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4']
    
    fig = go.Figure(data=[
        go.Bar(
            x=df_top['Modelo'], 
            y=df_top['quantidade'],
            marker=dict(
                color=colors[:len(df_top)],
                line=dict(color='rgba(255,255,255,0.8)', width=2)
            ),
            hovertemplate='<b>%{x}</b><br>Quantidade: %{y}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=dict(
            text='<b>Top 8 Modelos de Computadores</b>',
            font=dict(size=18, color='#1e1e1e', family='Inter'),
            x=0.5,
            y=0.95
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e1e1e', size=12, family='Inter'),
        showlegend=False,
        margin=dict(t=60, b=80, l=60, r=40),
        height=400,
        xaxis=dict(
            showgrid=False,
            tickangle=-45,
            title=dict(text='<b>Modelo</b>', font=dict(size=14)),
            linecolor='#e9ecef',
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(233,236,239,0.5)',
            title=dict(text='<b>Quantidade</b>', font=dict(size=14)),
            linecolor='#e9ecef'
        )
    )
    
    return fig

@app.callback(
    Output('ocupacao-por-setor', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('refresh-btn', 'n_clicks')]
)
def update_ocupacao_por_setor(n, refresh_clicks):
    df = execute_query(QUERIES['ocupacao_por_setor'])
    
    if df.empty:
        return go.Figure().add_annotation(
            text="Sem dados disponíveis", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )

    df_top = df.head(10)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_top['Setor'],
        x=df_top['TotalColaboradores'],
        orientation='h',
        name='Total Colaboradores',
        marker=dict(color='#e9ecef'),
        hovertemplate='<b>%{y}</b><br>Total: %{x}<extra></extra>'
    ))
    
    # Barras de colaboradores com equipamento (frente)
    fig.add_trace(go.Bar(
        y=df_top['Setor'],
        x=df_top['ComEquipamento'],
        orientation='h',
        name='Com Equipamento',
        marker=dict(color='#6366f1'),
        hovertemplate='<b>%{y}</b><br>Com Equipamento: %{x}<br>Taxa: %{customdata}%<extra></extra>',
        customdata=df_top['TaxaOcupacao']
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Taxa de Ocupação de Equipamentos por Setor</b>',
            font=dict(size=18, color='#1e1e1e', family='Inter'),
            x=0.5,
            y=0.95
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e1e1e', size=12, family='Inter'),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=11)
        ),
        margin=dict(t=60, b=80, l=150, r=40),
        height=400,
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(233,236,239,0.5)',
            title=dict(text='<b>Quantidade de Colaboradores</b>', font=dict(size=14)),
            linecolor='#e9ecef'
        ),
        yaxis=dict(
            showgrid=False,
            title=dict(text='<b>Setor</b>', font=dict(size=14)),
            linecolor='#e9ecef',
            tickfont=dict(size=10)
        ),
        barmode='overlay'
    )
    
    return fig

@app.callback(
    Output('estoque-modelos-idade', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('refresh-btn', 'n_clicks')]
)
def update_estoque_modelos_idade(n, refresh_clicks):
    # 1) Quantidade por modelo no estoque (DB)
    df_estoque = execute_query(QUERIES['modelos_em_estoque'])
    if df_estoque.empty:
        return go.Figure().add_annotation(
            text="Sem dados de estoque", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )
    df_estoque['Modelo'] = df_estoque['Modelo'].astype(str).str.strip()

    # 2) Idade média por modelo (Excel)
    idade_path = os.path.join(os.path.dirname(__file__), 'idade_computadores.xlsx')
    df_idade = None
    if os.path.exists(idade_path):
        try:
            plan = pd.read_excel(idade_path)
            if 'Modelo' in plan.columns and ('AnoCompra' in plan.columns or 'DataCompra' in plan.columns):
                plan['Modelo'] = plan['Modelo'].astype(str).str.strip()
                if 'AnoCompra' in plan.columns:
                    plan['AnoCompra'] = pd.to_numeric(plan['AnoCompra'], errors='coerce')
                else:
                    # DataCompra pode ser o ano direto (string/numero) ou uma data
                    ano_col = pd.to_numeric(plan['DataCompra'], errors='coerce')
                    if ano_col.notna().any():
                        plan['AnoCompra'] = ano_col.astype('Int64')
                    else:
                        plan['DataCompra'] = pd.to_datetime(plan['DataCompra'], errors='coerce')
                        plan['AnoCompra'] = plan['DataCompra'].dt.year
                plan = plan.dropna(subset=['Modelo', 'AnoCompra'])
                plan['AnoCompra'] = plan['AnoCompra'].astype(int)
                # Filtrar anos plausíveis (2010..ano atual) - equipamentos muito antigos podem estar com dados incorretos
                ano_atual = datetime.now().year
                plan = plan[(plan['AnoCompra'] >= 2010) & (plan['AnoCompra'] <= ano_atual)]
                
                # Filtrar outliers - idade máxima de 15 anos
                plan['idade_anos'] = (ano_atual - plan['AnoCompra']).astype(float)
                plan = plan[plan['idade_anos'] <= 15]
                df_idade = plan.groupby('Modelo', as_index=False)['idade_anos'].mean()
        except Exception:
            df_idade = None

    # 3) Join por modelo e montar donut chart (somente modelos presentes no Excel)
    if df_idade is None or df_idade.empty:
        return go.Figure().add_annotation(
            text="Excel sem dados válidos (Modelo + AnoCompra/DataCompra)", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )
    df_merge = pd.merge(df_estoque, df_idade, on='Modelo', how='inner')
    if df_merge.empty:
        return go.Figure().add_annotation(
            text="Nenhum modelo do Excel encontrado no estoque", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )

    # Cores modernas para o donut chart
    colors = ['#6366f1', '#8b5cf6', '#ec4899', '#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4']
    
    fig = go.Figure(data=[go.Pie(
        labels=df_merge['Modelo'],
        values=df_merge['Quantidade'],
        hole=0.4,
        marker=dict(
            colors=colors[:len(df_merge)],
            line=dict(color='#ffffff', width=3)
        ),
        hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Idade média: %{customdata:.1f} anos<extra></extra>',
        customdata=df_merge['idade_anos'],
        textposition='inside',
        textinfo='percent'
    )])
    
    fig.update_layout(
        title=dict(
            text='<b>Estoque por Modelo (com idade média)</b>',
            font=dict(size=18, color='#1e1e1e', family='Inter'),
            x=0.5,
            y=0.95
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e1e1e', size=12, family='Inter'),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=10)
        ),
        margin=dict(t=60, b=40, l=40, r=150),
        height=400,
        annotations=[
            dict(
                text="<b>Estoque<br>Total</b>",
                x=0.5, y=0.5,
                font_size=16,
                font_color='#6c757d',
                showarrow=False
            )
        ]
    )
    
    return fig

@app.callback(
    Output('terceirizados-inativos-table', 'children'),
    [Input('interval-component', 'n_intervals'),
     Input('refresh-btn', 'n_clicks')]
)
def update_terceirizados_inativos_table(n, refresh_clicks):
    df = execute_query(QUERIES['terceirizados_inativos_com_equipamentos'])
    
    if df.empty:
        return html.P("Nenhum terceirizado inativo com equipamentos", 
                     style={'text-align': 'center', 'color': '#6c757d', 'fontStyle': 'italic'})
    
    df_top = df.head(8)
    
    return dash_table.DataTable(
        data=df_top.to_dict('records'),
        columns=[
            {"name": "Serial", "id": "Serial"},
            {"name": "Modelo", "id": "Modelo"},
            {"name": "Nome", "id": "Nome"},
            {"name": "Matrícula", "id": "Matricula_Terc"},
            {"name": "Chefia", "id": "Chefia"}
        ],
        style_table={
            'overflowX': 'auto',
            'maxWidth': '100%',
            'borderRadius': '8px',
            'overflow': 'hidden'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '12px 16px',
            'fontFamily': 'Segoe UI, sans-serif',
            'fontSize': '0.875rem',
            'whiteSpace': 'normal',
            'height': 'auto',
            'border': 'none',
            'borderBottom': '1px solid #e9ecef'
        },
        style_header={
            'backgroundColor': '#1e1e1e',
            'color': 'white',
            'fontWeight': '600',
            'textTransform': 'uppercase',
            'letterSpacing': '0.5px',
            'fontSize': '0.8rem',
            'border': 'none'
        },
        style_data={
            'backgroundColor': '#ffffff',
            'border': 'none'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgba(99, 102, 241, 0.1)',
                'border': '1px solid #6366f1'
            }
        ]
    )

@app.callback(
    Output('demitidos-equipamentos-table', 'children'),
    [Input('interval-component', 'n_intervals'),
     Input('refresh-btn', 'n_clicks')]
)
def update_demitidos_equipamentos_table(n, refresh_clicks):
    df = execute_query(QUERIES['colaboradores_demitidos_com_equipamentos'])
    
    if df.empty:
        return html.P("Nenhum colaborador demitido com equipamentos", 
                     style={'text-align': 'center', 'color': '#6c757d', 'fontStyle': 'italic'})
    
    # Agrupa por colaborador para que o nome apareça uma única vez
    def _join_unique(series):
        valores = [str(x).strip() for x in series if pd.notna(x) and str(x).strip() != '']
        if not valores:
            return ''
        # Mantém ordem de aparição, removendo duplicados
        vistos = set()
        ordenado_sem_dup = []
        for v in valores:
            if v not in vistos:
                vistos.add(v)
                ordenado_sem_dup.append(v)
        return ' / '.join(ordenado_sem_dup)

    colunas_chave = ['Colaborador', 'CCusto', 'Chefia']
    for col in colunas_chave:
        if col not in df.columns:
            df[col] = None

    df_grouped = (
        df.groupby(colunas_chave, dropna=False)
          .agg({
              'ModeloComputador': _join_unique if 'ModeloComputador' in df.columns else lambda s: '',
              'ModeloPeriferico': _join_unique if 'ModeloPeriferico' in df.columns else lambda s: ''
          })
          .reset_index()
    )

    df_top = df_grouped.head(8)
    
    return dash_table.DataTable(
        data=df_top.to_dict('records'),
        columns=[
            {"name": "Colaborador", "id": "Colaborador"},
            {"name": "Centro Custo", "id": "CCusto"},
            {"name": "Chefia", "id": "Chefia"},
            {"name": "Computador", "id": "ModeloComputador"},
            {"name": "Periférico", "id": "ModeloPeriferico"}
        ],
        style_table={
            'overflowX': 'auto',
            'maxWidth': '100%',
            'borderRadius': '8px',
            'overflow': 'hidden'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '12px 16px',
            'fontFamily': 'Segoe UI, sans-serif',
            'fontSize': '0.875rem',
            'whiteSpace': 'normal',
            'height': 'auto',
            'border': 'none',
            'borderBottom': '1px solid #e9ecef'
        },
        style_header={
            'backgroundColor': '#1e1e1e',
            'color': 'white',
            'fontWeight': '600',
            'textTransform': 'uppercase',
            'letterSpacing': '0.5px',
            'fontSize': '0.8rem',
            'border': 'none'
        },
        style_data={
            'backgroundColor': '#ffffff',
            'border': 'none'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgba(99, 102, 241, 0.1)',
                'border': '1px solid #6366f1'
            }
        ]
    )

# ==================== CALLBACKS PARA ABA COLABORADORES ====================
@app.callback(
    Output('current-time-colab', 'children'),
    [Input('interval-colaboradores', 'n_intervals')]
)
def update_time_colab(n):
    return datetime.now().strftime('%H:%M:%S - %d/%m/%Y')

@app.callback(
    Output('colaboradores-por-setor', 'figure'),
    [Input('interval-colaboradores', 'n_intervals'),
     Input('refresh-btn-colab', 'n_clicks')]
)
def update_colaboradores_por_setor(n, refresh_clicks):
    df = execute_query(QUERIES['usuarios_por_setor'])
    
    if df.empty:
        return go.Figure().add_annotation(
            text="Sem dados disponíveis", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )
    
    # Pegar top 10 setores
    df_top = df.head(10)
    
    # Cores vibrantes para setores
    colors = ['#6366f1', '#8b5cf6', '#ec4899', '#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#84cc16', '#f59e0b']
    
    fig = go.Figure(data=[
        go.Bar(
            y=df_top['Setor'], 
            x=df_top['quantidade'],
            orientation='h',
            marker=dict(
                color=colors[:len(df_top)],
                line=dict(color='rgba(255,255,255,0.8)', width=2)
            ),
            hovertemplate='<b>%{y}</b><br>Colaboradores: %{x}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=dict(
            text='<b>Colaboradores por Setor</b>',
            font=dict(size=18, color='#1e1e1e', family='Inter'),
            x=0.5,
            y=0.95
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e1e1e', size=12, family='Inter'),
        showlegend=False,
        margin=dict(t=60, b=60, l=150, r=40),
        height=400,
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(233,236,239,0.5)',
            title=dict(text='<b>Quantidade</b>', font=dict(size=14)),
            linecolor='#e9ecef'
        ),
        yaxis=dict(
            showgrid=False,
            title=dict(text='<b>Setor</b>', font=dict(size=14)),
            linecolor='#e9ecef',
            tickfont=dict(size=10)
        )
    )
    
    return fig

@app.callback(
    Output('colaboradores-por-chefia', 'figure'),
    [Input('interval-colaboradores', 'n_intervals'),
     Input('refresh-btn-colab', 'n_clicks')]
)
def update_colaboradores_por_chefia(n, refresh_clicks):
    df = execute_query(QUERIES['colaboradores_por_chefia'])
    
    if df.empty:
        return go.Figure().add_annotation(
            text="Sem dados disponíveis", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )
    
    # Pegar top 8 chefias
    df_top = df.head(8)
    
    # Cores para o donut
    colors = ['#6366f1', '#8b5cf6', '#ec4899', '#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4']
    
    fig = go.Figure(data=[go.Pie(
        labels=df_top['Chefia'],
        values=df_top['quantidade'],
        hole=0.4,
        marker=dict(
            colors=colors[:len(df_top)],
            line=dict(color='#ffffff', width=3)
        ),
        hovertemplate='<b>%{label}</b><br>Colaboradores: %{value}<br>Percentual: %{percent}<extra></extra>',
        textposition='inside',
        textinfo='percent'
    )])
    
    fig.update_layout(
        title=dict(
            text='<b>Colaboradores por Chefia</b>',
            font=dict(size=18, color='#1e1e1e', family='Inter'),
            x=0.5,
            y=0.95
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e1e1e', size=12, family='Inter'),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=10)
        ),
        margin=dict(t=60, b=40, l=40, r=150),
        height=400,
        annotations=[
            dict(
                text="<b>Total<br>Colaboradores</b>",
                x=0.5, y=0.5,
                font_size=14,
                font_color='#6c757d',
                showarrow=False
            )
        ]
    )
    
    return fig

@app.callback(
    Output('colaboradores-detalhado-table', 'children'),
    [Input('interval-colaboradores', 'n_intervals'),
     Input('refresh-btn-colab', 'n_clicks')]
)
def update_colaboradores_detalhado_table(n, refresh_clicks):
    df = execute_query(QUERIES['colaboradores_detalhado'])
    
    if df.empty:
        return html.P("Nenhum colaborador encontrado", 
                     style={'text-align': 'center', 'color': '#6c757d', 'fontStyle': 'italic'})
    
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {"name": "Nome", "id": "Nome"},
            {"name": "Matrícula", "id": "Matricula"},
            {"name": "Setor", "id": "Setor"},
            {"name": "Chefia", "id": "Chefia"},
            {"name": "Status Equipamento", "id": "StatusEquipamento"},
            {"name": "Modelo Computador", "id": "ModeloComputador"}
        ],
        style_table={
            'overflowX': 'auto',
            'maxWidth': '100%',
            'borderRadius': '8px',
            'overflow': 'hidden'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '12px 16px',
            'fontFamily': 'Segoe UI, sans-serif',
            'fontSize': '0.875rem',
            'whiteSpace': 'normal',
            'height': 'auto',
            'border': 'none',
            'borderBottom': '1px solid #e9ecef'
        },
        style_header={
            'backgroundColor': '#1e1e1e',
            'color': 'white',
            'fontWeight': '600',
            'textTransform': 'uppercase',
            'letterSpacing': '0.5px',
            'fontSize': '0.8rem',
            'border': 'none'
        },
        style_data={
            'backgroundColor': '#ffffff',
            'border': 'none'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {'filter_query': 'StatusEquipamento = "Sem Equipamento"'},
                'backgroundColor': '#fff3cd',
                'color': '#856404'
            },
            {
                'if': {'filter_query': 'StatusEquipamento = "Com Equipamento"'},
                'backgroundColor': '#d1edff',
                'color': '#0c5460'
            },
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgba(99, 102, 241, 0.1)',
                'border': '1px solid #6366f1'
            }
        ],
        filter_action="native",
        sort_action="native",
        page_action="native",
        page_current=0,
        page_size=50
    )

def calcular_criticidade_equipamentos():
    """
    Calcula a criticidade dos equipamentos baseado na idade.
    Retorna DataFrame com criticidade calculada.
    """
    # Buscar equipamentos do banco
    df_equipamentos = execute_query(QUERIES['equipamentos_criticidade'])
    
    if df_equipamentos.empty:
        return pd.DataFrame()
    
    # Ler arquivo Excel com idades
    idade_path = os.path.join(os.path.dirname(__file__), 'idade_computadores.xlsx')
    if not os.path.exists(idade_path):
        return pd.DataFrame()
    
    try:
        plan = pd.read_excel(idade_path)
        
        if 'Modelo' not in plan.columns or ('AnoCompra' not in plan.columns and 'DataCompra' not in plan.columns):
            return pd.DataFrame()
        
        # Processar dados de idade
        plan['Modelo'] = plan['Modelo'].astype(str).str.strip()
        
        if 'AnoCompra' in plan.columns:
            plan['AnoCompra'] = pd.to_numeric(plan['AnoCompra'], errors='coerce')
        else:
            ano_col = pd.to_numeric(plan['DataCompra'], errors='coerce')
            if ano_col.notna().any():
                plan['AnoCompra'] = ano_col.astype('Int64')
            else:
                plan['DataCompra'] = pd.to_datetime(plan['DataCompra'], errors='coerce')
                plan['AnoCompra'] = plan['DataCompra'].dt.year
        
        plan = plan.dropna(subset=['Modelo', 'AnoCompra'])
        plan['AnoCompra'] = plan['AnoCompra'].astype(int)
        
        # Filtrar anos plausíveis
        ano_atual = datetime.now().year
        plan = plan[(plan['AnoCompra'] >= 2010) & (plan['AnoCompra'] <= ano_atual)]
        
        # Calcular idade
        plan['idade_anos'] = (ano_atual - plan['AnoCompra']).astype(float)
        plan = plan[plan['idade_anos'] <= 15]
        
        # Calcular idade média por modelo
        idade_media = plan.groupby('Modelo', as_index=False)['idade_anos'].mean()
        
        # Merge com equipamentos - INNER JOIN para manter apenas equipamentos com dados de idade
        df_merge = pd.merge(df_equipamentos, idade_media, on='Modelo', how='inner')
        
        # Melhorar informações de status
        def formatar_status(row):
            status = row.get('Status', '')
            if status == 'Descartado':
                return 'Equipamento Descartado'
            elif status == 'Estoque':
                return 'Reserva/Backup (Estoque)'
            else:
                return status
        
        df_merge['StatusDetalhado'] = df_merge.apply(formatar_status, axis=1)
        
        # Classificar criticidade (removido "Sem Dados" pois usamos inner join)
        def classificar_criticidade(idade):
            if idade >= 5:
                return 'Muito Crítico'
            elif idade >= 4:
                return 'Crítico'
            elif idade >= 3:
                return 'Atenção'
            elif idade >= 2:
                return 'Moderado'
            else:
                return 'Bom Estado'
        
        df_merge['Criticidade'] = df_merge['idade_anos'].apply(classificar_criticidade)
        df_merge['IdadeFormatada'] = df_merge['idade_anos'].apply(
            lambda x: f"{x:.1f} anos"
        )
        
        return df_merge
        
    except Exception as e:
        print(f"Erro ao calcular criticidade: {e}")
        return pd.DataFrame()

# ==================== CALLBACKS PARA ABA EQUIPAMENTOS ====================
@app.callback(
    Output('current-time-equip', 'children'),
    [Input('interval-equipamentos', 'n_intervals')]
)
def update_time_equip(n):
    return datetime.now().strftime('%H:%M:%S - %d/%m/%Y')

@app.callback(
    Output('equipamentos-por-status', 'figure'),
    [Input('interval-equipamentos', 'n_intervals'),
     Input('refresh-btn-equip', 'n_clicks')]
)
def update_equipamentos_por_status(n, refresh_clicks):
    df = execute_query(QUERIES['equipamentos_por_status'])
    
    if df.empty:
        return go.Figure().add_annotation(
            text="Sem dados disponíveis", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )
    
    colors = ['#22c55e', '#6366f1', '#ef4444']  # Verde para alocado, azul para estoque, vermelho para Descartado
    
    fig = go.Figure(data=[go.Pie(
        labels=df['Status'],
        values=df['quantidade'],
        hole=0.4,
        marker=dict(
            colors=colors[:len(df)],
            line=dict(color='#ffffff', width=3)
        ),
        hovertemplate='<b>%{label}</b><br>Equipamentos: %{value}<br>Percentual: %{percent}<extra></extra>',
        textposition='inside',
        textinfo='percent+label'
    )])
    
    fig.update_layout(
        title=dict(
            text='<b>Status dos Equipamentos</b>',
            font=dict(size=18, color='#1e1e1e', family='Inter'),
            x=0.5,
            y=0.95
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e1e1e', size=12, family='Inter'),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
            font=dict(size=11)
        ),
        margin=dict(t=60, b=60, l=20, r=20),
        height=400,
        annotations=[
            dict(
                text="<b>Total<br>Equipamentos</b>",
                x=0.5, y=0.5,
                font_size=14,
                font_color='#6c757d',
                showarrow=False
            )
        ]
    )
    
    return fig

@app.callback(
    Output('equipamentos-criticidade', 'figure'),
    [Input('interval-equipamentos', 'n_intervals'),
     Input('refresh-btn-equip', 'n_clicks')]
)
def update_equipamentos_criticidade(n, refresh_clicks):
    df = calcular_criticidade_equipamentos()
    
    if df.empty:
        return go.Figure().add_annotation(
            text="Sem dados de idade disponíveis", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )
    
    # Contar equipamentos por criticidade (Sem Dados já foi removido pela função calcular_criticidade_equipamentos)
    criticidade_counts = df['Criticidade'].value_counts()
    
    # Definir cores por nível de criticidade
    color_map = {
        'Muito Crítico': '#dc3545',    # Vermelho escuro
        'Crítico': '#fd7e14',          # Laranja
        'Atenção': '#ffc107',          # Amarelo
        'Moderado': '#20c997',         # Verde claro
        'Bom Estado': '#28a745'        # Verde
    }
    
    # Ordenar níveis de criticidade (removido "Sem Dados")
    ordem_criticidade = ['Muito Crítico', 'Crítico', 'Atenção', 'Moderado', 'Bom Estado']
    labels_ordenados = [c for c in ordem_criticidade if c in criticidade_counts.index]
    values_ordenados = [criticidade_counts[c] for c in labels_ordenados]
    colors_ordenados = [color_map[c] for c in labels_ordenados]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels_ordenados,
        values=values_ordenados,
        hole=0.4,
        marker=dict(
            colors=colors_ordenados,
            line=dict(color='#ffffff', width=3)
        ),
        hovertemplate='<b>%{label}</b><br>Equipamentos: %{value}<br>Percentual: %{percent}<extra></extra>',
        textposition='inside',
        textinfo='percent+label'
    )])
    
    fig.update_layout(
        title=dict(
            text='<b>Análise de Criticidade por Idade</b>',
            font=dict(size=18, color='#1e1e1e', family='Inter'),
            x=0.5,
            y=0.95
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e1e1e', size=12, family='Inter'),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=10)
        ),
        margin=dict(t=60, b=40, l=40, r=150),
        height=400,
        annotations=[
            dict(
                text="<b>Total<br>Analisados</b>",
                x=0.5, y=0.5,
                font_size=14,
                font_color='#6c757d',
                showarrow=False
            )
        ]
    )
    
    return fig

@app.callback(
    Output('equipamentos-criticos-table', 'children'),
    [Input('interval-equipamentos', 'n_intervals'),
     Input('refresh-btn-equip', 'n_clicks')]
)
def update_equipamentos_criticos_table(n, refresh_clicks):
    df = calcular_criticidade_equipamentos()
    
    if df.empty:
        return html.P("Sem dados de idade disponíveis", 
                     style={'text-align': 'center', 'color': '#6c757d', 'fontStyle': 'italic'})
    
    # Filtrar apenas equipamentos críticos e muito críticos
    df_criticos = df[df['Criticidade'].isin(['Muito Crítico', 'Crítico', 'Atenção'])].copy()
    
    # Ordenar por criticidade e idade
    ordem_criticidade = ['Muito Crítico', 'Crítico', 'Atenção']
    df_criticos['CriticidadeOrdem'] = df_criticos['Criticidade'].apply(lambda x: ordem_criticidade.index(x) if x in ordem_criticidade else 999)
    df_criticos = df_criticos.sort_values(['CriticidadeOrdem', 'idade_anos'], ascending=[True, False])
    
    if df_criticos.empty:
        return html.P("Nenhum equipamento crítico encontrado! 🎉", 
                     style={'text-align': 'center', 'color': '#28a745', 'fontWeight': '600'})
    
    return dash_table.DataTable(
        data=df_criticos.to_dict('records'),
        columns=[
            {"name": "Serial", "id": "Serial"},
            {"name": "Modelo", "id": "Modelo"},
            {"name": "Idade", "id": "IdadeFormatada"},
            {"name": "Criticidade", "id": "Criticidade"},
            {"name": "Status", "id": "Status"},
            {"name": "Usuário", "id": "Usuario"},
            {"name": "Colaborador", "id": "NomeColaborador"}
        ],
        style_table={
            'overflowX': 'auto',
            'maxWidth': '100%',
            'borderRadius': '8px',
            'overflow': 'hidden'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '12px 16px',
            'fontFamily': 'Segoe UI, sans-serif',
            'fontSize': '0.875rem',
            'whiteSpace': 'normal',
            'height': 'auto',
            'border': 'none',
            'borderBottom': '1px solid #e9ecef'
        },
        style_header={
            'backgroundColor': '#dc3545',
            'color': 'white',
            'fontWeight': '600',
            'textTransform': 'uppercase',
            'letterSpacing': '0.5px',
            'fontSize': '0.8rem',
            'border': 'none'
        },
        style_data={
            'backgroundColor': '#ffffff',
            'border': 'none'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {'filter_query': 'Criticidade = "Muito Crítico"'},
                'backgroundColor': '#f8d7da',
                'color': '#721c24',
                'fontWeight': '600'
            },
            {
                'if': {'filter_query': 'Criticidade = "Crítico"'},
                'backgroundColor': '#ffeaa7',
                'color': '#856404',
                'fontWeight': '600'
            },
            {
                'if': {'filter_query': 'Criticidade = "Atenção"'},
                'backgroundColor': '#fff3cd',
                'color': '#856404'
            },
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgba(99, 102, 241, 0.1)',
                'border': '1px solid #6366f1'
            }
        ],
        filter_action="native",
        sort_action="native",
        page_action="native",
        page_current=0,
        page_size=25
    )

@app.callback(
    Output('equipamentos-por-modelo-full', 'figure'),
    [Input('interval-equipamentos', 'n_intervals'),
     Input('refresh-btn-equip', 'n_clicks')]
)
def update_equipamentos_por_modelo_full(n, refresh_clicks):
    df = execute_query(QUERIES['computadores_por_modelo'])
    
    if df.empty:
        return go.Figure().add_annotation(
            text="Sem dados disponíveis", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )
    
    df_top = df.head(15)
    
    colors = ['#6366f1', '#8b5cf6', '#ec4899', '#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#84cc16', '#f59e0b', '#8b5a2b', '#6b21a8', '#dc2626', '#059669', '#0284c7']
    
    fig = go.Figure(data=[
        go.Bar(
            y=df_top['Modelo'], 
            x=df_top['quantidade'],
            orientation='h',
            marker=dict(
                color=colors[:len(df_top)],
                line=dict(color='rgba(255,255,255,0.8)', width=2)
            ),
            hovertemplate='<b>%{y}</b><br>Quantidade: %{x}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=dict(
            text='<b>Top 15 Modelos de Equipamentos</b>',
            font=dict(size=18, color='#1e1e1e', family='Inter'),
            x=0.5,
            y=0.95
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e1e1e', size=12, family='Inter'),
        showlegend=False,
        margin=dict(t=60, b=60, l=200, r=40),
        height=400,
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(233,236,239,0.5)',
            title=dict(text='<b>Quantidade</b>', font=dict(size=14)),
            linecolor='#e9ecef'
        ),
        yaxis=dict(
            showgrid=False,
            title=dict(text='<b>Modelo</b>', font=dict(size=14)),
            linecolor='#e9ecef',
            tickfont=dict(size=9)
        )
    )
    
    return fig

@app.callback(
    Output('equipamentos-detalhado-table', 'children'),
    [Input('interval-equipamentos', 'n_intervals'),
     Input('refresh-btn-equip', 'n_clicks')]
)
def update_equipamentos_detalhado_table(n, refresh_clicks):
    df = execute_query(QUERIES['equipamentos_detalhado'])
    
    if df.empty:
        return html.P("Nenhum equipamento encontrado", 
                     style={'text-align': 'center', 'color': '#6c757d', 'fontStyle': 'italic'})
    
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {"name": "Serial", "id": "Serial"},
            {"name": "Modelo", "id": "Modelo"},
            {"name": "Usuário", "id": "Usuario"},
            {"name": "Matrícula", "id": "Matricula"},
            {"name": "Colaborador", "id": "NomeColaborador"},
            {"name": "Status", "id": "Status"}
        ],
        style_table={
            'overflowX': 'auto',
            'maxWidth': '100%',
            'borderRadius': '8px',
            'overflow': 'hidden'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '12px 16px',
            'fontFamily': 'Segoe UI, sans-serif',
            'fontSize': '0.875rem',
            'whiteSpace': 'normal',
            'height': 'auto',
            'border': 'none',
            'borderBottom': '1px solid #e9ecef'
        },
        style_header={
            'backgroundColor': '#1e1e1e',
            'color': 'white',
            'fontWeight': '600',
            'textTransform': 'uppercase',
            'letterSpacing': '0.5px',
            'fontSize': '0.8rem',
            'border': 'none'
        },
        style_data={
            'backgroundColor': '#ffffff',
            'border': 'none'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {'filter_query': 'Status = "Estoque"'},
                'backgroundColor': '#cff4fc',
                'color': '#055160'
            },
            {
                'if': {'filter_query': 'Status = "Alocado"'},
                'backgroundColor': '#d1edff',
                'color': '#0c5460'
            },
            {
                'if': {'filter_query': 'Status = "Descartado"'},
                'backgroundColor': '#fff3cd',
                'color': '#856404'
            },
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgba(99, 102, 241, 0.1)',
                'border': '1px solid #6366f1'
            }
        ],
        filter_action="native",
        sort_action="native",
        page_action="native",
        page_current=0,
        page_size=50
    )

@app.callback(
    Output('connection-status', 'children'),
    [Input('test-connection-btn', 'n_clicks')]
)
def test_connection(n_clicks):
    if n_clicks is None:
        return ""
    
    try:
        engine = get_engine()
        if engine:
            test_df = pd.read_sql("SELECT 1 as test", engine)
            return html.Div([
                html.I(className="fas fa-check-circle", style={'color': '#22c55e', 'marginRight': '0.5rem'}),
                "Conexão estabelecida com sucesso!"
            ], style={'color': '#22c55e', 'fontWeight': '600'})
        else:
            return html.Div([
                html.I(className="fas fa-times-circle", style={'color': '#ef4444', 'marginRight': '0.5rem'}),
                "Erro na criação da engine"
            ], style={'color': '#ef4444', 'fontWeight': '600'})
    except Exception as e:
        return html.Div([
            html.I(className="fas fa-times-circle", style={'color': '#ef4444', 'marginRight': '0.5rem'}),
            f"Erro na conexão: {str(e)}"
        ], style={'color': '#ef4444', 'fontWeight': '600'})

if __name__ == '__main__':
    print("Testando conexão com banco de dados...")
    engine = get_engine()
    if engine:
        try:
            test_df = pd.read_sql("SELECT 1 as test", engine)
            print("✓ Conexão estabelecida com sucesso!")
        except Exception as e:
            print(f"✗ Erro no teste de conexão: {e}")
    else:
        print("✗ Erro na criação da engine. Verifique as configurações em DB_CONFIG")

# ==================== CALLBACKS PARA REDUÇÃO DE CUSTOS ====================

@app.callback(
    Output('custos-por-setor', 'figure'),
    [Input('interval-equipamentos', 'n_intervals'),
     Input('refresh-btn-equip', 'n_clicks')]
)
def update_custos_por_setor(n, refresh_clicks):
    """Atualiza gráfico de análise de custos por setor"""
    df = execute_query(QUERIES['custos_por_setor'])
    
    if df.empty:
        return go.Figure().add_annotation(
            text="Sem dados disponíveis", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )
    
    # Top 10 setores
    df_top = df.head(10)
    
    fig = go.Figure()
    
    # Barras de colaboradores (fundo)
    fig.add_trace(go.Bar(
        x=df_top['Setor'],
        y=df_top['QuantidadeColaboradores'],
        name='Colaboradores',
        marker=dict(color='#e9ecef'),
        yaxis='y',
        hovertemplate='<b>%{x}</b><br>Colaboradores: %{y}<extra></extra>'
    ))
    
    # Barras de equipamentos (frente)
    fig.add_trace(go.Bar(
        x=df_top['Setor'],
        y=df_top['QuantidadeEquipamentos'],
        name='Equipamentos',
        marker=dict(color='#6366f1'),
        yaxis='y',
        hovertemplate='<b>%{x}</b><br>Equipamentos: %{y}<extra></extra>'
    ))
    
    # Linha de ratio equipamento/colaborador
    fig.add_trace(go.Scatter(
        x=df_top['Setor'],
        y=df_top['EquipamentoPorColaborador'],
        mode='lines+markers',
        name='Ratio Equip/Colab',
        yaxis='y2',
        line=dict(color='#ef4444', width=3),
        marker=dict(size=8, color='#ef4444'),
        hovertemplate='<b>%{x}</b><br>Ratio: %{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Análise de Custos e Eficiência por Setor</b>',
            font=dict(size=18, color='#1e1e1e', family='Inter'),
            x=0.5,
            y=0.95
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e1e1e', size=12, family='Inter'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=80, b=100, l=60, r=60),
        height=500,
        xaxis=dict(
            showgrid=False,
            title=dict(text='<b>Setor</b>', font=dict(size=14)),
            linecolor='#e9ecef',
            tickangle=-45
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(233,236,239,0.5)',
            title=dict(text='<b>Quantidade</b>', font=dict(size=14)),
            linecolor='#e9ecef',
            side='left'
        ),
        yaxis2=dict(
            showgrid=False,
            title=dict(text='<b>Equipamento/Colaborador</b>', font=dict(size=14)),
            overlaying='y',
            side='right',
            linecolor='#ef4444',
            tickfont=dict(color='#ef4444')
        )
    )
    
    return fig

@app.callback(
    Output('equipamentos-status-chart', 'figure'),
    [Input('interval-equipamentos', 'n_intervals'),
     Input('refresh-btn-equip', 'n_clicks')]
)
def update_equipamentos_status_chart(n, refresh_clicks):
    """Atualiza gráfico de equipamentos por status real"""
    df = execute_query(QUERIES['equipamentos_por_status_real'])
    
    if df.empty:
        return go.Figure().add_annotation(
            text="Sem dados disponíveis", 
            showarrow=False,
            font=dict(size=16, color='#6c757d')
        )
    
    # Cores específicas para cada status
    color_map = {
        'Em Uso': '#28a745',
        'Em Estoque': '#007bff', 
        'Acesso Remoto': '#6f42c1',
        'Devolvido': '#20c997',
        'Descartado': '#dc3545',
        'Danificado': '#fd7e14',
        'Extraviado': '#ffc107',
        'Roubado': '#6c757d',
        'Sem Status': '#e9ecef',
        'Sem Dono': '#868e96'
    }
    
    colors = [color_map.get(status, '#6c757d') for status in df['Status']]
    
    fig = px.pie(
        df, 
        values='Quantidade', 
        names='Status',
        title='<b>Distribuição por Status</b>',
        color_discrete_sequence=colors
    )
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>',
        marker=dict(line=dict(color='#ffffff', width=2))
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e1e1e', size=10, family='Inter'),
        title=dict(
            font=dict(size=14, color='#1e1e1e', family='Inter'),
            x=0.5,
            y=0.95
        ),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            font=dict(size=9)
        ),
        margin=dict(t=40, b=20, l=20, r=150),
        height=400
    )
    
    return fig

@app.callback(
    Output('equipamentos-status-resumo', 'children'),
    [Input('interval-equipamentos', 'n_intervals'),
     Input('refresh-btn-equip', 'n_clicks')]
)
def update_equipamentos_status_resumo(n, refresh_clicks):
    """Atualiza resumo de equipamentos por status"""
    df = execute_query(QUERIES['equipamentos_por_status_real'])
    
    if df.empty:
        return html.Div("Sem dados disponíveis", style={'color': '#6c757d', 'fontStyle': 'italic'})
    
    cards = []
    color_map = {
        'Em Uso': '#28a745',
        'Em Estoque': '#007bff', 
        'Acesso Remoto': '#6f42c1',
        'Devolvido': '#20c997',
        'Descartado': '#dc3545',
        'Danificado': '#fd7e14',
        'Extraviado': '#ffc107',
        'Roubado': '#6c757d',
        'Reparo': '#ff6b35',
        'Status Indefinido': '#e9ecef'
    }
    
    icon_map = {
        'Em Uso': '✅',
        'Em Estoque': '📦',
        'Acesso Remoto': '🌐',
        'Devolvido': '↩️',
        'Descartado': '🗑️',
        'Danificado': '🔧',
        'Extraviado': '❓',
        'Roubado': '🚨',
        'Reparo': '🔧',
        'Sem Status': '❗',
        'Sem Dono': '❗',
        'Status Indefinido': '❗'
    }
    
    for _, row in df.iterrows():
        color = color_map.get(row['Status'], '#6c757d')
        icon = icon_map.get(row['Status'], '📊')
        
        card = html.Div([
            html.Div([
                html.Div([
                    html.Span(icon, style={'fontSize': '1.2rem', 'marginRight': '0.5rem'}),
                    html.Span(str(row['Quantidade']), style={
                        'fontSize': '1.4rem',
                        'fontWeight': '700',
                        'color': '#000000'
                    })
                ], style={'marginBottom': '0.3rem'}),
                html.Div(f"{row['Percentual']:.1f}%", style={
                    'fontSize': '0.8rem',
                    'color': '#000000',
                    'marginBottom': '0.3rem'
                }),
                html.Div(row['Status'], style={
                    'fontSize': '0.75rem',
                    'fontWeight': '500',
                    'color': '#000000',
                    'lineHeight': '1.2',
                    'textAlign': 'center'
                })
            ], style={
                'padding': '0.8rem',
                'border': '2px solid #000000',
                'borderRadius': '8px',
                'backgroundColor': 'white',
                'textAlign': 'center',
                'marginBottom': '0.5rem',
                'minHeight': '80px',
                'display': 'flex',
                'flexDirection': 'column',
                'justifyContent': 'center',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
            })
        ])
        cards.append(card)
    
    return html.Div(cards, style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(120px, 1fr))', 'gap': '0.5rem'})

@app.callback(
    Output('equipamentos-criticos-status-chart', 'figure'),
    [Input('interval-equipamentos', 'n_intervals'),
     Input('refresh-btn-equip', 'n_clicks')]
)
def update_equipamentos_criticos_status_chart(n, refresh_clicks):
    """Atualiza gráfico de equipamentos críticos por status"""
    df = execute_query(QUERIES['equipamentos_criticos_por_status'])
    
    if df.empty:
        return go.Figure().add_annotation(
            text="Nenhum equipamento crítico encontrado", 
            showarrow=False,
            font=dict(size=16, color='#28a745')
        )
    
    colors = ['#dc3545', '#fd7e14', '#ffc107', '#6c757d', '#e9ecef']
    
    fig = go.Figure()
    
    # Barras de quantidade
    fig.add_trace(go.Bar(
        x=df['StatusCritico'],
        y=df['Quantidade'],
        name='Quantidade',
        marker=dict(color=colors[:len(df)]),
        text=df['Quantidade'],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Quantidade: %{y}<br>Idade Média: %{customdata:.1f} anos<extra></extra>',
        customdata=df['IdadeMedia']
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Equipamentos em Situação Crítica</b>',
            font=dict(size=16, color='#1e1e1e', family='Inter'),
            x=0.5,
            y=0.95
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e1e1e', size=12, family='Inter'),
        showlegend=False,
        margin=dict(t=60, b=60, l=60, r=40),
        height=350,
        xaxis=dict(
            showgrid=False,
            title=dict(text='<b>Status</b>', font=dict(size=14)),
            linecolor='#e9ecef'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(233,236,239,0.5)',
            title=dict(text='<b>Quantidade</b>', font=dict(size=14)),
            linecolor='#e9ecef'
        )
    )
    
    return fig

@app.callback(
    Output('equipamentos-status-table', 'children'),
    [Input('interval-equipamentos', 'n_intervals'),
     Input('refresh-btn-equip', 'n_clicks')]
)
def update_equipamentos_status_table(n, refresh_clicks):
    """Atualiza tabela detalhada de equipamentos por status"""
    df = execute_query(QUERIES['equipamentos_detalhado_status'])
    
    if df.empty:
        return html.P("Nenhum equipamento encontrado", 
                     style={'text-align': 'center', 'color': '#6c757d', 'fontStyle': 'italic'})
    
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {"name": "Serial", "id": "Serial"},
            {"name": "Modelo", "id": "Modelo"}, 
            {"name": "Status", "id": "StatusRealizado"},
            {"name": "Campo Usuário", "id": "Usuario"},
            {"name": "Matrícula", "id": "Matricula"},
            {"name": "Colaborador", "id": "NomeColaborador"},
            {"name": "Setor", "id": "Setor"},
            {"name": "Idade (Anos)", "id": "IdadeAnos"}
        ],
        style_table={
            'overflowX': 'auto',
            'maxWidth': '100%',
            'borderRadius': '8px',
            'overflow': 'hidden'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px 12px',
            'fontFamily': 'Segoe UI, sans-serif',
            'fontSize': '0.85rem',
            'whiteSpace': 'normal',
            'height': 'auto',
            'border': 'none',
            'borderBottom': '1px solid #e9ecef'
        },
        style_header={
            'backgroundColor': '#1e1e1e',
            'color': 'white',
            'fontWeight': '600',
            'textTransform': 'uppercase',
            'letterSpacing': '0.5px',
            'fontSize': '0.75rem',
            'border': 'none'
        },
        style_data={
            'backgroundColor': '#ffffff',
            'border': 'none'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {'filter_query': 'StatusRealizado = "Descartado"'},
                'backgroundColor': '#f8d7da',
                'color': '#721c24'
            },
            {
                'if': {'filter_query': 'StatusRealizado = "Danificado"'},
                'backgroundColor': '#fff3cd',
                'color': '#856404'
            },
            {
                'if': {'filter_query': 'StatusRealizado = "Extraviado"'},
                'backgroundColor': '#fff3cd',
                'color': '#856404'
            },
            {
                'if': {'filter_query': 'StatusRealizado = "Roubado"'},
                'backgroundColor': '#f8d7da',
                'color': '#721c24'
            },
            {
                'if': {'filter_query': 'StatusRealizado = "Em Estoque"'},
                'backgroundColor': '#d1ecf1',
                'color': '#0c5460'
            },
            {
                'if': {'filter_query': 'StatusRealizado = "Alocado"'},
                'backgroundColor': '#d4edda',
                'color': '#155724'
            },
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgba(30, 30, 30, 0.1)',
                'border': '1px solid #1e1e1e'
            }
        ],
        filter_action="native",
        sort_action="native",
        page_action="native",
        page_current=0,
        page_size=25,
        tooltip_data=[
            {
                'StatusRealizado': {'value': 'Status atual do equipamento no sistema', 'type': 'markdown'},
                'Usuario': {'value': 'Campo Usuario na base de dados', 'type': 'markdown'},
                'IdadeAnos': {'value': 'Idade em anos desde a compra', 'type': 'markdown'}
            } for _ in range(len(df))
        ],
        tooltip_duration=None
    )

@app.callback(
    Output('timeline-reducao-chart', 'figure'),
    [Input('refresh-btn-reducao', 'n_clicks'),
     Input('interval-reducao-custos', 'n_intervals')]
)
def update_timeline_reducao_chart(refresh_clicks, n):
    """Atualiza gráfico de evolução da redução de custos"""
    df = load_desligamento_data()
    if df is None:
        return {}
    
    df['Data_Devolucao'] = df['Situação'].apply(extract_date_from_situation)
    df['Status'] = df['Situação'].apply(lambda x: 'Devolvido' if 'Devolvido' in str(x) else 'Aguardando')
    
    devolvidos = df[df['Status'] == 'Devolvido'].copy()
    
    if devolvidos.empty or devolvidos['Data_Devolucao'].isna().all():
        fig = go.Figure()
        fig.add_annotation(
            text="Nenhum item devolvido ainda<br>Aguardando primeiras devoluções para exibir evolução",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#666")
        )
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=400
        )
        return fig
    
    devolvidos = devolvidos.dropna(subset=['Data_Devolucao']).sort_values('Data_Devolucao')
    devolvidos['Economia_Acumulada'] = devolvidos['Valor Economizado/mês'].cumsum()
    devolvidos['Custo_Restante'] = VALOR_FIXO_MENSAL - devolvidos['Economia_Acumulada']

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=devolvidos['Data_Devolucao'],
        y=devolvidos['Custo_Restante'],
        mode='lines+markers',
        name='Custo Atual',
        line=dict(color='#000', width=3),
        marker=dict(size=8, color='#000', line=dict(width=2, color='white')),
        hovertemplate='<b>%{x}</b><br><b>%{y:,.0f}</b><extra></extra>'
    ))

    fig.update_layout(
        title="Evolução da Redução de Custos",
        xaxis_title="Data de Devolução",
        yaxis_title="Custo Mensal (R$)",
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400,
        font=dict(size=12),
        yaxis=dict(tickformat=',.0f', gridcolor='#f0f0f0'),
        xaxis=dict(gridcolor='#f0f0f0')
    )
    
    return fig

@app.callback(
    Output('status-reducao-pie-chart', 'figure'),
    [Input('refresh-btn-reducao', 'n_clicks'),
     Input('interval-reducao-custos', 'n_intervals')]
)
def update_status_reducao_pie(refresh_clicks, n):
    """Atualiza gráfico de pizza dos status"""
    df = load_desligamento_data()
    if df is None:
        return {}
    
    df['Status'] = df['Situação'].apply(lambda x: 'Devolvido' if 'Devolvido' in str(x) else 'Aguardando')
    
    qtd_devolvidos = len(df[df['Status'] == 'Devolvido'])
    qtd_aguardando = len(df[df['Status'] == 'Aguardando'])
    
    fig = px.pie(
        values=[qtd_devolvidos, qtd_aguardando],
        names=['Devolvido', 'Aguardando'],
        color_discrete_sequence=['#28a745', '#dc3545']  # Verde para Devolvido, Vermelho para Aguardando
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont_size=14,
        textfont_color='white'
    )
    
    fig.update_layout(
        title="Distribuição dos Equipamentos",
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400
    )
    
    return fig

@app.callback(
    Output('tipo-reducao-bar-chart', 'figure'),
    [Input('refresh-btn-reducao', 'n_clicks'),
     Input('interval-reducao-custos', 'n_intervals')]
)
def update_tipo_reducao_bar(refresh_clicks, n):
    """Atualiza gráfico de barras por tipo de equipamento"""
    df = load_desligamento_data()
    if df is None:
        return {}
    
    economia_por_tipo = df.groupby('Devolução').agg({
        'Valor Economizado/mês': 'sum',
        'CT': 'count'
    }).reset_index()
    economia_por_tipo.columns = ['Tipo', 'Economia_Mensal', 'Quantidade']
    economia_por_tipo = economia_por_tipo.sort_values('Economia_Mensal', ascending=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=economia_por_tipo['Tipo'],
        x=economia_por_tipo['Economia_Mensal'],
        orientation='h',
        marker=dict(color='#000'),
        text=[f'{q} un.' for q in economia_por_tipo['Quantidade']],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Economia Mensal por Tipo de Equipamento",
        xaxis_title="Economia Mensal (R$)",
        yaxis_title="Tipo de Equipamento",
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=500,
        margin=dict(l=150)
    )
    
    return fig

@app.callback(
    Output('reducao-data-table', 'children'),
    [Input('refresh-btn-reducao', 'n_clicks'),
     Input('interval-reducao-custos', 'n_intervals')]
)
def update_reducao_data_table(refresh_clicks, n):
    """Atualiza tabela detalhada de redução de custos"""
    df = load_desligamento_data()
    if df is None:
        return html.Div("Dados não disponíveis")
    
    # Prepara dados para a tabela
    df_display = df.copy()
    df_display['Economia Mensal'] = df_display['Valor Economizado/mês'].apply(format_currency)
    df_display['Economia Anual'] = df_display['Valor Economizado/ano'].apply(format_currency)
    df_display['Status'] = df_display['Situação'].apply(lambda x: 'Devolvido' if 'Devolvido' in str(x) else 'Aguardando')
    
    columns_to_show = ['CT', 'Devolução', 'Economia Mensal', 'Economia Anual', 'Status']
    df_display = df_display[columns_to_show]
    df_display.columns = ['CT', 'Tipo', 'Economia/Mês', 'Economia/Ano', 'Status']
    
    table = dash_table.DataTable(
        data=df_display.to_dict('records'),
        columns=[{"name": col, "id": col} for col in df_display.columns],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '12px',
            'fontFamily': 'Segoe UI',
            'fontSize': '14px'
        },
        style_header={
            'backgroundColor': '#000',
            'color': 'white',
            'fontWeight': '600'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': 'Status = "Devolvido"'},
                'backgroundColor': '#f9f9f9'
            }
        ],
        page_size=10
    )
    
    return table

@app.callback(
    Output('current-time-reducao', 'children'),
    [Input('interval-reducao-custos', 'n_intervals')]
)
def update_time_reducao(n):
    """Atualiza horário na aba de redução de custos"""
    return datetime.now().strftime('%d/%m/%Y %H:%M:%S')

@app.callback(
    Output('alerts-section', 'children'),
    [Input('interval-component', 'n_intervals'),
     Input('refresh-btn', 'n_clicks')]
)
def update_alerts_section(n, refresh_clicks):
    """Atualiza seção de alertas"""
    df_alertas = execute_query(QUERIES['alertas_sistema'])
    
    if df_alertas.empty:
        return [html.Div("Nenhum alerta no momento", style={'text-align': 'center', 'color': '#6c757d'})]
    
    alerts = []
    icon_map = {
        'Colaboradores Demitidos com Equipamentos': 'fas fa-exclamation-triangle',
        'Equipamentos Descartados/Danificados': 'fas fa-desktop',
        'Colaboradores Ativos Sem Equipamento': 'fas fa-user-slash'
    }
    
    for _, row in df_alertas.iterrows():
        icon = icon_map.get(row['TipoAlerta'], 'fas fa-info-circle')
        alert_card = create_alert_card(
            row['TipoAlerta'],
            row['Quantidade'],
            row['Prioridade'],
            icon
        )
        alerts.append(alert_card)
    
    return alerts

# ==================== CALLBACKS LINHAS MÓVEIS ====================
@app.callback(
    Output('linhas-content', 'children'),
    Input('linhas-tabs', 'value')
)
def render_linhas_content(active_tab):
    """Renderiza o conteúdo das abas de Linhas Móveis"""
    
    if active_tab == 'sem-uso':
        return create_linhas_sem_uso_content()
    elif active_tab == 'com-uso':
        return create_linhas_com_uso_content()
    elif active_tab == 'metricas':
        return create_linhas_metricas_content()
    else:
        return create_linhas_sem_uso_content()

def create_linhas_sem_uso_content():
    """Cria conteúdo da aba de linhas sem uso"""
    
    # Dados das linhas sem uso
    linhas_sem_uso = [
        {'telefone': '21-96729-8530', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-96747-1151', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-96747-4750', 'uso': 0.0, 'sessoes': 0, 'usuario': 'ALEX DE MELO MACHADO'},
        {'telefone': '21-96754-3199', 'uso': 0.0, 'sessoes': 0, 'usuario': 'HIAGO PEREIRA DAUDT'},
        {'telefone': '21-97161-9941', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-97218-5152', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-97286-8541', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-97295-0716', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-97546-4883', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-99308-8451', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-99417-4039', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-99573-5910', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-99582-8720', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-99628-2229', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-99638-6268', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-99642-6126', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-99720-0671', 'uso': 0.0, 'sessoes': 0, 'usuario': 'FRANCILEI ALVES PEREIRA'},
        {'telefone': '21-99748-9522', 'uso': 0.0, 'sessoes': 0, 'usuario': 'DIOGO FERREIRA RODRIGUES'},
        {'telefone': '21-99765-2489', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '21-99883-1246', 'uso': 0.0, 'sessoes': 0, 'usuario': 'MARCELO DELGADO LOPES'},
        {'telefone': '21-99927-7527', 'uso': 0.0, 'sessoes': 0, 'usuario': 'CARLOS EDUARDO FERREIRA'},
        {'telefone': '22-99221-6510', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
        {'telefone': '22-99256-3638', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'}
    ]
    
    return html.Div([
        # Cards de estatísticas
        html.Div([
            html.Div([
                html.H3("23", style={'fontSize': '2.5rem', 'fontWeight': '200', 'color': '#2c3e50', 'margin': '0'}),
                html.P("Linhas sem consumo relevante", style={'color': '#7f8c8d', 'margin': '10px 0 0 0'})
            ], className="chart-card", style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%', 'textAlign': 'center'}),
            
            html.Div([
                html.H3("14.6%", style={'fontSize': '2.5rem', 'fontWeight': '200', 'color': '#2c3e50', 'margin': '0'}),
                html.P("Do total", style={'color': '#7f8c8d', 'margin': '10px 0 0 0'})
            ], className="chart-card", style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%', 'textAlign': 'center'}),
            
            html.Div([
                html.H3("157", style={'fontSize': '2.5rem', 'fontWeight': '200', 'color': '#2c3e50', 'margin': '0'}),
                html.P("Total de linhas", style={'color': '#7f8c8d', 'margin': '10px 0 0 0'})
            ], className="chart-card", style={'width': '30%', 'display': 'inline-block', 'textAlign': 'center'})
        ], style={'marginBottom': '30px'}),
        
        # Tabela de linhas
        html.Div([
            html.H4("Todas as 23 linhas sem consumo relevante", 
                   style={'background': '#f8f9fa', 'padding': '20px', 'margin': '0', 'borderBottom': '1px solid #e0e0e0'}),
            
            dash_table.DataTable(
                data=[{
                    'Telefone': linha['telefone'],
                    'Usuário': linha['usuario'],
                    'Uso (GB)': f"{linha['uso']:.1f}",
                    'Sessões': linha['sessoes'],
                    'Status': 'Sem consumo relevante'
                } for linha in linhas_sem_uso],
                columns=[
                    {'name': 'Telefone', 'id': 'Telefone'},
                    {'name': 'Usuário', 'id': 'Usuário'},
                    {'name': 'Uso (GB)', 'id': 'Uso (GB)'},
                    {'name': 'Sessões', 'id': 'Sessões'},
                    {'name': 'Status', 'id': 'Status'}
                ],
                style_cell={
                    'textAlign': 'left',
                    'fontFamily': 'Inter, sans-serif',
                    'fontSize': '14px',
                    'padding': '12px'
                },
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': '600',
                    'borderBottom': '2px solid #dee2e6'
                },
                style_data_conditional=[
                    {
                        'if': {'column_id': 'Status'},
                        'backgroundColor': '#f8f9fa',
                        'color': '#dc3545',
                        'fontWeight': '500'
                    }
                ],
                page_size=15,
                style_table={'height': '600px', 'overflowY': 'auto'}
            )
        ], className="chart-card")
    ])

def create_linhas_com_uso_content():
    """Cria conteúdo da aba de linhas com uso"""
    
    # Dados completos das linhas com uso (todas as 134 linhas do HTML)
    linhas_com_uso = [
        {'telefone': '21-96726-8788', 'uso': 385.9, 'sessoes': 463, 'status': 'Alto uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-99528-6151', 'uso': 369.4, 'sessoes': 1655, 'status': 'Alto uso', 'usuario': 'DANIEL CARVALHO'},
        {'telefone': '21-99706-5399', 'uso': 255.1, 'sessoes': 1206, 'status': 'Alto uso', 'usuario': 'PAULO CEZAR DIAS'},
        {'telefone': '21-96716-7784', 'uso': 247.4, 'sessoes': 1598, 'status': 'Alto uso', 'usuario': 'BRUNA ROQUE'},
        {'telefone': '21-99973-8542', 'uso': 236.4, 'sessoes': 1287, 'status': 'Alto uso', 'usuario': 'SIMONE DUARTE'},
        {'telefone': '21-97223-6333', 'uso': 226.3, 'sessoes': 3155, 'status': 'Alto uso', 'usuario': 'DERICK JORDAN'},
        {'telefone': '21-96717-5841', 'uso': 204.9, 'sessoes': 1305, 'status': 'Alto uso', 'usuario': 'HENRIQUE PAIVA'},
        {'telefone': '22-99619-2915', 'uso': 203.9, 'sessoes': 1334, 'status': 'Alto uso', 'usuario': 'ANTONIO BARCELOS'},
        {'telefone': '21-99515-3760', 'uso': 187.2, 'sessoes': 1850, 'status': 'Alto uso', 'usuario': 'ESTOQUE'},
        {'telefone': '22-99763-2112', 'uso': 179.0, 'sessoes': 7304, 'status': 'Alto uso', 'usuario': 'ALEXANDRE MENEZES'},
        {'telefone': '21-96738-3209', 'uso': 176.7, 'sessoes': 1481, 'status': 'Alto uso', 'usuario': 'THAINÁ ISRAEL'},
        {'telefone': '21-97209-8873', 'uso': 176.5, 'sessoes': 981, 'status': 'Alto uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-97288-8996', 'uso': 168.3, 'sessoes': 258, 'status': 'Alto uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-97208-3724', 'uso': 166.1, 'sessoes': 2092, 'status': 'Alto uso', 'usuario': 'KLEBER LOPES'},
        {'telefone': '21-99958-7136', 'uso': 165.7, 'sessoes': 1017, 'status': 'Alto uso', 'usuario': 'LUCAS RICHARD'},
        {'telefone': '21-96724-2185', 'uso': 146.3, 'sessoes': 1131, 'status': 'Alto uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-99750-5062', 'uso': 138.1, 'sessoes': 4008, 'status': 'Alto uso', 'usuario': 'ALAN SILVA'},
        {'telefone': '21-99502-3196', 'uso': 124.9, 'sessoes': 1013, 'status': 'Alto uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-96774-7649', 'uso': 113.0, 'sessoes': 1893, 'status': 'Alto uso', 'usuario': 'EDUARDO CHAMUSCA'},
        {'telefone': '21-99855-3536', 'uso': 102.6, 'sessoes': 984, 'status': 'Alto uso', 'usuario': 'MAYARA TEIXEIRA'},
        {'telefone': '21-99524-3953', 'uso': 99.4, 'sessoes': 958, 'status': 'Alto uso', 'usuario': 'LILIAN PEREIRA'},
        {'telefone': '21-96754-3469', 'uso': 95.9, 'sessoes': 1203, 'status': 'Alto uso', 'usuario': 'LUCIENE NUNES'},
        {'telefone': '21-96717-7121', 'uso': 94.2, 'sessoes': 3621, 'status': 'Alto uso', 'usuario': 'THOMAZ PARAVIDINO'},
        {'telefone': '21-97214-7705', 'uso': 93.8, 'sessoes': 834, 'status': 'Alto uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-97208-8322', 'uso': 93.6, 'sessoes': 3726, 'status': 'Alto uso', 'usuario': 'LEONARDO AQUINO'},
        {'telefone': '21-97217-9427', 'uso': 83.6, 'sessoes': 708, 'status': 'Alto uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-99634-1045', 'uso': 79.9, 'sessoes': 986, 'status': 'Alto uso', 'usuario': 'EDMAR SILVA'},
        {'telefone': '22-99262-6851', 'uso': 77.8, 'sessoes': 5231, 'status': 'Alto uso', 'usuario': 'FABIO ALMEIDA'},
        {'telefone': '22-99755-8345', 'uso': 76.7, 'sessoes': 1183, 'status': 'Alto uso', 'usuario': 'JONAS TISSIANI'},
        {'telefone': '22-99800-9718', 'uso': 74.2, 'sessoes': 2655, 'status': 'Alto uso', 'usuario': 'DANIEL FERREIRA'},
        {'telefone': '21-97294-8830', 'uso': 71.1, 'sessoes': 1385, 'status': 'Alto uso', 'usuario': 'PABLO MORELATO'},
        {'telefone': '21-99924-8204', 'uso': 64.1, 'sessoes': 948, 'status': 'Alto uso', 'usuario': 'TATIANA TEIXEIRA'},
        {'telefone': '21-99521-1683', 'uso': 63.8, 'sessoes': 439, 'status': 'Alto uso', 'usuario': 'FELIPE SANTOS'},
        {'telefone': '22-99996-1936', 'uso': 62.8, 'sessoes': 1186, 'status': 'Alto uso', 'usuario': 'ESTOQUE'},
        {'telefone': '22-99781-3189', 'uso': 62.4, 'sessoes': 835, 'status': 'Alto uso', 'usuario': 'PETTERSON PRADO'},
        {'telefone': '21-99874-3007', 'uso': 61.3, 'sessoes': 968, 'status': 'Alto uso', 'usuario': 'HUGO MACHADO'},
        {'telefone': '21-99579-8537', 'uso': 55.9, 'sessoes': 636, 'status': 'Alto uso', 'usuario': 'SERGIO RAMOS'},
        {'telefone': '22-99725-3856', 'uso': 55.2, 'sessoes': 925, 'status': 'Alto uso', 'usuario': 'GUILHERME CHAGAS'},
        {'telefone': '21-99208-9960', 'uso': 54.4, 'sessoes': 741, 'status': 'Alto uso', 'usuario': 'DANIEL OLIVEIRA'},
        {'telefone': '21-99504-7033', 'uso': 50.3, 'sessoes': 2038, 'status': 'Alto uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-99570-2548', 'uso': 50.2, 'sessoes': 1026, 'status': 'Alto uso', 'usuario': 'SIRLEI CRUZ'},
        {'telefone': '21-97999-0034', 'uso': 46.8, 'sessoes': 636, 'status': 'Uso médio', 'usuario': 'JUSSANA MENEZES'},
        {'telefone': '21-99681-5331', 'uso': 46.5, 'sessoes': 1122, 'status': 'Uso médio', 'usuario': 'RODRIGO BARRETO'},
        {'telefone': '21-99797-6858', 'uso': 46.4, 'sessoes': 8465, 'status': 'Uso médio', 'usuario': 'JULIO GONÇALVES'},
        {'telefone': '21-98230-6390', 'uso': 45.8, 'sessoes': 1162, 'status': 'Uso médio', 'usuario': 'MANUELA MOTA'},
        {'telefone': '21-96779-7952', 'uso': 43.6, 'sessoes': 2020, 'status': 'Uso médio', 'usuario': 'ANA FERNANDES'},
        {'telefone': '21-99732-0033', 'uso': 39.6, 'sessoes': 612, 'status': 'Uso médio', 'usuario': 'ESTOQUE'},
        {'telefone': '21-96768-1635', 'uso': 39.4, 'sessoes': 1150, 'status': 'Uso médio', 'usuario': 'ESTOQUE'},
        {'telefone': '21-99876-3306', 'uso': 39.3, 'sessoes': 583, 'status': 'Uso médio', 'usuario': 'ESTOQUE'},
        {'telefone': '21-97269-2661', 'uso': 36.9, 'sessoes': 1270, 'status': 'Uso médio', 'usuario': 'ESTOQUE'},
        {'telefone': '22-99242-2399', 'uso': 36.7, 'sessoes': 1583, 'status': 'Uso médio', 'usuario': 'ESTOQUE'},
        {'telefone': '21-99566-4583', 'uso': 36.2, 'sessoes': 1174, 'status': 'Uso médio', 'usuario': 'ESTOQUE'},
        {'telefone': '21-99864-5825', 'uso': 34.4, 'sessoes': 1796, 'status': 'Uso médio', 'usuario': 'JACY ARAUJO'},
        {'telefone': '21-99743-1105', 'uso': 34.1, 'sessoes': 991, 'status': 'Uso médio', 'usuario': 'ANDERSON FRUTUOSO'},
        {'telefone': '22-99892-8993', 'uso': 33.8, 'sessoes': 3769, 'status': 'Uso médio', 'usuario': 'YANCA ANDRADE'},
        {'telefone': '21-97178-4590', 'uso': 32.3, 'sessoes': 626, 'status': 'Uso médio', 'usuario': 'PAULO MAFORT'},
        {'telefone': '22-99888-3735', 'uso': 32.1, 'sessoes': 823, 'status': 'Uso médio', 'usuario': 'ESTOQUE'},
        {'telefone': '21-99199-0035', 'uso': 32.1, 'sessoes': 1619, 'status': 'Uso médio', 'usuario': 'FARIS MIGUEL'},
        {'telefone': '21-99832-4617', 'uso': 31.2, 'sessoes': 1174, 'status': 'Uso médio', 'usuario': 'LUCAS CARVALHO'},
        {'telefone': '22-99795-6747', 'uso': 28.1, 'sessoes': 666, 'status': 'Uso médio', 'usuario': 'CASSIA MENDES'},
        {'telefone': '21-96739-4845', 'uso': 24.9, 'sessoes': 1522, 'status': 'Uso médio', 'usuario': 'PATRICIA LUDGERO'},
        {'telefone': '21-97564-4394', 'uso': 24.4, 'sessoes': 1293, 'status': 'Uso médio', 'usuario': 'REJANE ABREU'},
        {'telefone': '22-99227-9302', 'uso': 24.1, 'sessoes': 646, 'status': 'Uso médio', 'usuario': 'FABIO TAVARES'},
        {'telefone': '22-99994-5806', 'uso': 23.2, 'sessoes': 195, 'status': 'Uso médio', 'usuario': 'JESSICA PIMENTEL'},
        {'telefone': '22-99221-9109', 'uso': 22.8, 'sessoes': 377, 'status': 'Uso médio', 'usuario': 'GABRIEL SALES'},
        {'telefone': '21-99608-1270', 'uso': 22.8, 'sessoes': 1699, 'status': 'Uso médio', 'usuario': 'LUIS BECKMANN'},
        {'telefone': '21-99920-9130', 'uso': 21.1, 'sessoes': 1073, 'status': 'Uso médio', 'usuario': 'ESTOQUE'},
        {'telefone': '21-96734-8276', 'uso': 20.7, 'sessoes': 685, 'status': 'Uso médio', 'usuario': 'KAMILA NASCIMENTO'},
        {'telefone': '22-99872-8513', 'uso': 20.4, 'sessoes': 2272, 'status': 'Uso médio', 'usuario': 'ESTOQUE'},
        {'telefone': '21-99734-3746', 'uso': 20.0, 'sessoes': 884, 'status': 'Uso médio', 'usuario': 'HELIO OLIVEIRA'},
        {'telefone': '21-96726-5906', 'uso': 20.0, 'sessoes': 1293, 'status': 'Uso médio', 'usuario': 'RAONY XAVIER'},
        {'telefone': '21-99777-0805', 'uso': 18.0, 'sessoes': 1528, 'status': 'Uso médio', 'usuario': 'EMILLE SANTOS'},
        {'telefone': '21-97165-4636', 'uso': 17.9, 'sessoes': 242, 'status': 'Uso médio', 'usuario': 'GILDA MOLL'},
        {'telefone': '22-99262-5913', 'uso': 16.5, 'sessoes': 896, 'status': 'Uso médio', 'usuario': 'JAILSON SILVA'},
        {'telefone': '21-99694-5085', 'uso': 16.5, 'sessoes': 723, 'status': 'Uso médio', 'usuario': 'ANNA FERREIRA'},
        {'telefone': '22-99866-1702', 'uso': 16.5, 'sessoes': 846, 'status': 'Uso médio', 'usuario': 'PATRICIA LUSTOSA DIAS'},
        {'telefone': '22-99256-4392', 'uso': 15.0, 'sessoes': 570, 'status': 'Uso médio', 'usuario': 'VANGERGLEDSON ANDERSON'},
        {'telefone': '21-97223-9395', 'uso': 15.0, 'sessoes': 536, 'status': 'Uso médio', 'usuario': 'JOAO SILVA'},
        {'telefone': '22-99819-6785', 'uso': 14.2, 'sessoes': 582, 'status': 'Uso médio', 'usuario': 'ANA DUARTE'},
        {'telefone': '21-99597-7318', 'uso': 13.6, 'sessoes': 719, 'status': 'Uso médio', 'usuario': 'DRIELY CARVALHO'},
        {'telefone': '22-99267-9686', 'uso': 13.1, 'sessoes': 366, 'status': 'Uso médio', 'usuario': 'ESTOQUE'},
        {'telefone': '21-99846-9613', 'uso': 12.4, 'sessoes': 975, 'status': 'Uso médio', 'usuario': 'MARCIO SOSKA'},
        {'telefone': '21-97288-2275', 'uso': 12.2, 'sessoes': 742, 'status': 'Uso médio', 'usuario': 'ROSELENE OLIVEIRA'},
        {'telefone': '21-99710-5501', 'uso': 11.6, 'sessoes': 1065, 'status': 'Uso médio', 'usuario': 'WANDERSON JUNIOR'},
        {'telefone': '21-96728-0058', 'uso': 11.1, 'sessoes': 346, 'status': 'Uso médio', 'usuario': 'JAIR TAVARES'},
        {'telefone': '21-99934-9235', 'uso': 10.6, 'sessoes': 190, 'status': 'Uso médio', 'usuario': 'NIVEA ABREU'},
        {'telefone': '21-97471-8744', 'uso': 10.4, 'sessoes': 849, 'status': 'Uso médio', 'usuario': 'DANIELLY ARAUJO'},
        {'telefone': '21-96749-5305', 'uso': 10.4, 'sessoes': 519, 'status': 'Uso médio', 'usuario': 'ESTOQUE'},
        {'telefone': '22-99877-9352', 'uso': 10.1, 'sessoes': 474, 'status': 'Uso médio', 'usuario': 'RODRIGO RODRIGUES'},
        {'telefone': '21-99931-6723', 'uso': 9.1, 'sessoes': 1990, 'status': 'Baixo uso', 'usuario': 'JOSE ESTEVAO'},
        {'telefone': '21-99879-9914', 'uso': 8.5, 'sessoes': 1009, 'status': 'Baixo uso', 'usuario': 'JEAN SANTOS'},
        {'telefone': '21-96746-6127', 'uso': 8.1, 'sessoes': 1093, 'status': 'Baixo uso', 'usuario': 'RODRIGO MACEDO'},
        {'telefone': '21-96754-7661', 'uso': 7.4, 'sessoes': 957, 'status': 'Baixo uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-97159-8110', 'uso': 6.9, 'sessoes': 454, 'status': 'Baixo uso', 'usuario': 'MARIANA LIMA'},
        {'telefone': '21-99753-4031', 'uso': 6.6, 'sessoes': 1298, 'status': 'Baixo uso', 'usuario': 'SILVIA CARNEIRO'},
        {'telefone': '21-97230-8943', 'uso': 6.4, 'sessoes': 499, 'status': 'Baixo uso', 'usuario': 'ANDRE FREITAS'},
        {'telefone': '21-99422-4402', 'uso': 6.2, 'sessoes': 935, 'status': 'Baixo uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-97263-4285', 'uso': 4.3, 'sessoes': 212, 'status': 'Baixo uso', 'usuario': 'WALTER LOPES'},
        {'telefone': '21-99760-7989', 'uso': 4.3, 'sessoes': 451, 'status': 'Baixo uso', 'usuario': 'JOELSON CARVALHO'},
        {'telefone': '22-99215-5594', 'uso': 3.9, 'sessoes': 893, 'status': 'Baixo uso', 'usuario': 'BRENNO MARINI'},
        {'telefone': '21-97299-7210', 'uso': 3.8, 'sessoes': 599, 'status': 'Baixo uso', 'usuario': 'SORYANE CORDEIRO'},
        {'telefone': '22-99790-1463', 'uso': 3.7, 'sessoes': 186, 'status': 'Baixo uso', 'usuario': 'BRENNO MARINI'},
        {'telefone': '21-97999-0028', 'uso': 3.6, 'sessoes': 217, 'status': 'Baixo uso', 'usuario': 'MARIANA LIMA'},
        {'telefone': '21-99631-5374', 'uso': 3.5, 'sessoes': 63, 'status': 'Baixo uso', 'usuario': 'PAULO RIBAS'},
        {'telefone': '21-99576-0184', 'uso': 3.3, 'sessoes': 615, 'status': 'Baixo uso', 'usuario': 'FRANCISCO ALVES'},
        {'telefone': '21-97233-2159', 'uso': 3.3, 'sessoes': 339, 'status': 'Baixo uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-96764-5262', 'uso': 3.1, 'sessoes': 2046, 'status': 'Baixo uso', 'usuario': 'LUCIANE HOLANDA'},
        {'telefone': '21-99657-6916', 'uso': 3.1, 'sessoes': 2139, 'status': 'Baixo uso', 'usuario': 'BRUNO AGUIAR'},
        {'telefone': '21-99842-7494', 'uso': 3.0, 'sessoes': 731, 'status': 'Baixo uso', 'usuario': 'VITOR CARVALHO'},
        {'telefone': '22-99808-2623', 'uso': 2.8, 'sessoes': 88, 'status': 'Baixo uso', 'usuario': 'PHILIPE NALI'},
        {'telefone': '21-99937-9912', 'uso': 2.7, 'sessoes': 404, 'status': 'Baixo uso', 'usuario': 'ESTOQUE'},
        {'telefone': '22-99622-0196', 'uso': 2.6, 'sessoes': 417, 'status': 'Baixo uso', 'usuario': 'AYLA DIAS'},
        {'telefone': '22-99244-4881', 'uso': 2.2, 'sessoes': 29, 'status': 'Baixo uso', 'usuario': 'ANDERSON BARBOSA'},
        {'telefone': '22-99242-2380', 'uso': 2.2, 'sessoes': 857, 'status': 'Baixo uso', 'usuario': 'JOANNA AREAL'},
        {'telefone': '22-99214-8916', 'uso': 2.1, 'sessoes': 323, 'status': 'Baixo uso', 'usuario': 'RAFAELLA MACHADO'},
        {'telefone': '21-97113-2148', 'uso': 1.8, 'sessoes': 513, 'status': 'Baixo uso', 'usuario': 'GABRIELA CORREA'},
        {'telefone': '21-99657-9133', 'uso': 1.7, 'sessoes': 1303, 'status': 'Baixo uso', 'usuario': 'ANA MATTZA'},
        {'telefone': '21-99734-2485', 'uso': 1.6, 'sessoes': 348, 'status': 'Baixo uso', 'usuario': 'LEONARDO BORGES'},
        {'telefone': '22-99852-6544', 'uso': 1.4, 'sessoes': 518, 'status': 'Baixo uso', 'usuario': 'RAFAEL SÁ'},
        {'telefone': '21-99507-5745', 'uso': 1.4, 'sessoes': 580, 'status': 'Baixo uso', 'usuario': 'LUCIANA PIRES'},
        {'telefone': '21-97634-8422', 'uso': 1.2, 'sessoes': 40, 'status': 'Baixo uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-97111-3061', 'uso': 1.2, 'sessoes': 237, 'status': 'Baixo uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-99668-2956', 'uso': 1.1, 'sessoes': 115, 'status': 'Baixo uso', 'usuario': 'RAFAEL PARRILHA'},
        {'telefone': '21-99640-1089', 'uso': 0.9, 'sessoes': 223, 'status': 'Baixo uso', 'usuario': 'PATRICIA BENTO'},
        {'telefone': '21-99192-7921', 'uso': 0.9, 'sessoes': 1116, 'status': 'Baixo uso', 'usuario': 'TATIANA REIS'},
        {'telefone': '21-99681-2367', 'uso': 0.8, 'sessoes': 242, 'status': 'Baixo uso', 'usuario': 'LIDIANE SILVA'},
        {'telefone': '21-99262-3498', 'uso': 0.7, 'sessoes': 1656, 'status': 'Baixo uso', 'usuario': 'MARCO LOPES'},
        {'telefone': '21-99615-3703', 'uso': 0.5, 'sessoes': 92, 'status': 'Baixo uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-99626-1695', 'uso': 0.5, 'sessoes': 60, 'status': 'Baixo uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-97210-4140', 'uso': 0.5, 'sessoes': 55, 'status': 'Baixo uso', 'usuario': 'ESTOQUE'},
        {'telefone': '21-96727-4805', 'uso': 0.4, 'sessoes': 185, 'status': 'Baixo uso', 'usuario': 'SHEILA WILLIAMS'},
        {'telefone': '21-99999-4554', 'uso': 0.2, 'sessoes': 157, 'status': 'Baixo uso', 'usuario': 'EVANDRO FALCAO'},
        {'telefone': '21-97241-9862', 'uso': 0.0, 'sessoes': 200, 'status': 'Baixo uso', 'usuario': 'TIAGO CARNEIRO'},
        {'telefone': '21-99563-2227', 'uso': 0.0, 'sessoes': 155, 'status': 'Baixo uso', 'usuario': 'ISABELA PODORA'}
    ]
    
    return html.Div([
        # Cards de estatísticas
        html.Div([
            html.Div([
                html.H3("134", style={'fontSize': '2.5rem', 'fontWeight': '200', 'color': '#2c3e50', 'margin': '0'}),
                html.P("Linhas ativas", style={'color': '#7f8c8d', 'margin': '10px 0 0 0'})
            ], className="chart-card", style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%', 'textAlign': 'center'}),
            
            html.Div([
                html.H3("85.4%", style={'fontSize': '2.5rem', 'fontWeight': '200', 'color': '#2c3e50', 'margin': '0'}),
                html.P("Do total", style={'color': '#7f8c8d', 'margin': '10px 0 0 0'})
            ], className="chart-card", style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%', 'textAlign': 'center'}),
            
            html.Div([
                html.H3("127.1", style={'fontSize': '2.5rem', 'fontWeight': '200', 'color': '#2c3e50', 'margin': '0'}),
                html.P("GB médio por linha", style={'color': '#7f8c8d', 'margin': '10px 0 0 0'})
            ], className="chart-card", style={'width': '30%', 'display': 'inline-block', 'textAlign': 'center'})
        ], style={'marginBottom': '30px'}),
        
        # Tabela de linhas (todas as 134 linhas)
        html.Div([
            html.H4("Todas as 134 linhas com uso ativo",
                   style={'background': '#f8f9fa', 'padding': '20px', 'margin': '0', 'borderBottom': '1px solid #e0e0e0'}),
            
            dash_table.DataTable(
                data=[{
                    'Telefone': linha['telefone'],
                    'Usuário': linha['usuario'],
                    'Uso (GB)': f"{linha['uso']:.1f}",
                    'Sessões': linha['sessoes'],
                    'Status': linha['status']
                } for linha in linhas_com_uso],
                columns=[
                    {'name': 'Telefone', 'id': 'Telefone'},
                    {'name': 'Usuário', 'id': 'Usuário'},
                    {'name': 'Uso (GB)', 'id': 'Uso (GB)'},
                    {'name': 'Sessões', 'id': 'Sessões'},
                    {'name': 'Status', 'id': 'Status'}
                ],
                style_cell={
                    'textAlign': 'left',
                    'fontFamily': 'Inter, sans-serif',
                    'fontSize': '14px',
                    'padding': '12px'
                },
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': '600',
                    'borderBottom': '2px solid #dee2e6'
                },
                style_data_conditional=[
                    {
                        'if': {'column_id': 'Status', 'filter_query': 'Status = "Alto uso"'},
                        'backgroundColor': '#d4edda',
                        'color': '#155724',
                        'fontWeight': '500'
                    },
                    {
                        'if': {'column_id': 'Status', 'filter_query': 'Status = "Uso médio"'},
                        'backgroundColor': '#d1ecf1',
                        'color': '#0c5460',
                        'fontWeight': '500'
                    },
                    {
                        'if': {'column_id': 'Status', 'filter_query': 'Status = "Baixo uso"'},
                        'backgroundColor': '#fff3cd',
                        'color': '#856404',
                        'fontWeight': '500'
                    }
                ],
                page_size=20,
                style_table={'height': '700px', 'overflowY': 'auto'},
                filter_action="native",
                sort_action="native"
            )
        ], className="chart-card")
    ])

def create_linhas_metricas_content():
    """Cria conteúdo da aba de métricas"""
    
    return html.Div([
        # Cards de métricas principais
        html.Div([
            html.Div([
                html.H3("17.0", style={'fontSize': '2.5rem', 'fontWeight': '200', 'color': '#2c3e50', 'margin': '0'}),
                html.P("TB nos 6 meses", style={'color': '#7f8c8d', 'margin': '10px 0 0 0'}),
                html.H5("Consumo Total", style={'color': '#2c3e50', 'margin': '15px 0 0 0'})
            ], className="chart-card", style={'width': '23%', 'display': 'inline-block', 'marginRight': '2%', 'textAlign': 'center'}),
            
            html.Div([
                html.H3("385.9", style={'fontSize': '2.5rem', 'fontWeight': '200', 'color': '#2c3e50', 'margin': '0'}),
                html.P("GB em uma linha", style={'color': '#7f8c8d', 'margin': '10px 0 0 0'}),
                html.H5("Maior Consumidor", style={'color': '#2c3e50', 'margin': '15px 0 0 0'})
            ], className="chart-card", style={'width': '23%', 'display': 'inline-block', 'marginRight': '2%', 'textAlign': 'center'}),
            
            html.Div([
                html.H3("134", style={'fontSize': '2.5rem', 'fontWeight': '200', 'color': '#2c3e50', 'margin': '0'}),
                html.P("de 157 totais", style={'color': '#7f8c8d', 'margin': '10px 0 0 0'}),
                html.H5("Linhas Ativas", style={'color': '#2c3e50', 'margin': '15px 0 0 0'})
            ], className="chart-card", style={'width': '23%', 'display': 'inline-block', 'marginRight': '2%', 'textAlign': 'center'}),
            
            html.Div([
                html.H3("23", style={'fontSize': '2.5rem', 'fontWeight': '200', 'color': '#2c3e50', 'margin': '0'}),
                html.P("linhas canceláveis", style={'color': '#7f8c8d', 'margin': '10px 0 0 0'}),
                html.H5("Economia Potencial", style={'color': '#2c3e50', 'margin': '15px 0 0 0'})
            ], className="chart-card", style={'width': '23%', 'display': 'inline-block', 'textAlign': 'center'})
        ], style={'marginBottom': '30px'}),
        
        # Gráficos
        html.Div([
            html.Div([
                html.H4("Distribuição de Uso por Categoria", style={'textAlign': 'center', 'marginBottom': '20px'}),
                dcc.Graph(
                    figure=px.pie(
                        values=[23, 42, 51, 41],
                        names=['Sem Consumo', 'Baixo Uso', 'Uso Médio', 'Alto Uso'],
                        color_discrete_sequence=['#dc3545', '#ffc107', '#17a2b8', '#28a745']
                    ).update_layout(
                        font_family="Inter, sans-serif",
                        showlegend=True,
                        height=400
                    )
                )
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            html.Div([
                html.H4("Consumo por Faixa de Uso", style={'textAlign': 'center', 'marginBottom': '20px'}),
                dcc.Graph(
                    figure=px.bar(
                        x=['0 GB', '0-10 GB', '10-50 GB', '50+ GB'],
                        y=[23, 23, 67, 44],
                        color=['#6c757d', '#ffc107', '#17a2b8', '#28a745']
                    ).update_layout(
                        font_family="Inter, sans-serif",
                        showlegend=False,
                        height=400,
                        xaxis_title="Faixas de Consumo",
                        yaxis_title="Número de Linhas"
                    )
                )
            ], className="chart-card", style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'})
        ])
    ])

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)
