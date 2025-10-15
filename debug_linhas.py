#!/usr/bin/env python3
"""
Versão depurada focada apenas na seção de Linhas Móveis
"""
import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc

# Configuração do app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Dados das linhas com uso (apenas primeiras 10 para teste)
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
]

# Dados das linhas sem uso (apenas algumas para teste)
linhas_sem_uso = [
    {'telefone': '21-96729-8530', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
    {'telefone': '21-96747-1151', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
    {'telefone': '21-96747-4750', 'uso': 0.0, 'sessoes': 0, 'usuario': 'ALEX DE MELO MACHADO'},
    {'telefone': '21-96754-3199', 'uso': 0.0, 'sessoes': 0, 'usuario': 'HIAGO PEREIRA DAUDT'},
    {'telefone': '21-97161-9941', 'uso': 0.0, 'sessoes': 0, 'usuario': 'SEM CONSUMO RELEVANTE'},
]

def create_linhas_sem_uso_content():
    """Debug - Cria conteúdo da aba de linhas sem uso"""
    return html.Div([
        html.H3("🚫 LINHAS SEM USO - DEBUG", style={'color': '#dc3545', 'textAlign': 'center'}),
        html.P(f"Total: {len(linhas_sem_uso)} linhas", style={'textAlign': 'center'}),
        
        dash_table.DataTable(
            data=[{
                'Telefone': linha['telefone'],
                'Usuário': linha['usuario'],
                'Uso (GB)': f"{linha['uso']:.1f}",
                'Sessões': linha['sessoes']
            } for linha in linhas_sem_uso],
            columns=[
                {'name': 'Telefone', 'id': 'Telefone'},
                {'name': 'Usuário', 'id': 'Usuário'},
                {'name': 'Uso (GB)', 'id': 'Uso (GB)'},
                {'name': 'Sessões', 'id': 'Sessões'}
            ],
            style_cell={'textAlign': 'left', 'fontFamily': 'Arial', 'padding': '10px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            page_size=10
        )
    ])

def create_linhas_com_uso_content():
    """Debug - Cria conteúdo da aba de linhas com uso"""
    print("🔍 DEBUG: create_linhas_com_uso_content() foi chamada!")
    
    return html.Div([
        html.H3("✅ LINHAS EM USO - DEBUG", style={'color': '#28a745', 'textAlign': 'center'}),
        html.P(f"Total: {len(linhas_com_uso)} linhas", style={'textAlign': 'center'}),
        
        # Cards de estatísticas
        html.Div([
            html.Div([
                html.H3(str(len(linhas_com_uso)), style={'fontSize': '2.5rem', 'color': '#2c3e50', 'margin': '0'}),
                html.P("Linhas ativas", style={'color': '#7f8c8d'})
            ], style={'textAlign': 'center', 'backgroundColor': '#d4edda', 'padding': '20px', 'margin': '10px', 'borderRadius': '8px'})
        ], style={'marginBottom': '20px'}),
        
        # Tabela de linhas
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
            style_cell={'textAlign': 'left', 'fontFamily': 'Arial', 'padding': '10px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'column_id': 'Status', 'filter_query': '{Status} = Alto uso'},
                    'backgroundColor': '#d4edda',
                    'color': '#155724'
                }
            ],
            page_size=10,
            filter_action="native",
            sort_action="native"
        )
    ])

def create_linhas_metricas_content():
    """Debug - Cria conteúdo da aba de métricas"""
    return html.Div([
        html.H3("📊 MÉTRICAS - DEBUG", style={'color': '#007bff', 'textAlign': 'center'}),
        html.P("Métricas das linhas móveis", style={'textAlign': 'center'}),
        html.Hr(),
        html.P(f"Total de linhas com uso: {len(linhas_com_uso)}", style={'fontSize': '18px'}),
        html.P(f"Total de linhas sem uso: {len(linhas_sem_uso)}", style={'fontSize': '18px'}),
    ])

# Layout principal
app.layout = html.Div([
    html.Div([
        html.H1("📱 DEBUG - Linhas Móveis", style={'color': '#2c3e50', 'textAlign': 'center'}),
        html.P("Versão depurada para identificar problemas", style={'textAlign': 'center', 'color': '#6c757d'}),
        html.Hr(),
        
        # Navegação por abas
        html.Div([
            dcc.Tabs(id="debug-linhas-tabs", value="sem-uso", children=[
                dcc.Tab(label="🚫 Linhas sem consumo", value="sem-uso"),
                dcc.Tab(label="✅ Linhas em Uso", value="com-uso"),
                dcc.Tab(label="📊 Métricas", value="metricas"),
            ], style={'marginBottom': '20px'})
        ]),
        
        # Conteúdo das abas
        html.Div(id="debug-linhas-content"),
        
        # Status de debug
        html.Div(id="debug-status", style={'marginTop': '20px', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6'})
    ], style={'padding': '20px'})
])

@app.callback(
    [Output('debug-linhas-content', 'children'),
     Output('debug-status', 'children')],
    Input('debug-linhas-tabs', 'value')
)
def render_debug_linhas_content(active_tab):
    """Debug - Renderiza o conteúdo das abas de Linhas Móveis"""
    
    print(f"🔍 DEBUG: Callback chamado com active_tab = '{active_tab}'")
    
    status_msg = f"🎯 Aba ativa: '{active_tab}' | Timestamp: {pd.Timestamp.now()}"
    
    if active_tab == 'sem-uso':
        print("🔍 DEBUG: Renderizando linhas SEM uso")
        return create_linhas_sem_uso_content(), status_msg
    elif active_tab == 'com-uso':
        print("🔍 DEBUG: Renderizando linhas COM uso")
        return create_linhas_com_uso_content(), status_msg
    elif active_tab == 'metricas':
        print("🔍 DEBUG: Renderizando métricas")
        return create_linhas_metricas_content(), status_msg
    else:
        print(f"🔍 DEBUG: Aba desconhecida '{active_tab}', usando padrão")
        return create_linhas_sem_uso_content(), f"⚠️ Aba desconhecida: '{active_tab}'"

if __name__ == '__main__':
    import pandas as pd
    print("🚀 Iniciando aplicativo DEBUG...")
    print("📍 Acesse: http://127.0.0.1:8052")
    print("🔍 Verifique o console para mensagens de debug")
    app.run(debug=True, host='127.0.0.1', port=8052)
