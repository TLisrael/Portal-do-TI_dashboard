#!/usr/bin/env python3
"""
Teste específico para verificar se as linhas em uso estão sendo exibidas
"""
import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc

# Dados de teste das linhas em uso
linhas_com_uso = [
    {'telefone': '21-96726-8788', 'uso': 385.9, 'sessoes': 463, 'status': 'Alto uso', 'usuario': 'ESTOQUE'},
    {'telefone': '21-99528-6151', 'uso': 369.4, 'sessoes': 1655, 'status': 'Alto uso', 'usuario': 'DANIEL CARVALHO'},
    {'telefone': '21-99706-5399', 'uso': 255.1, 'sessoes': 1206, 'status': 'Alto uso', 'usuario': 'PAULO CEZAR DIAS'},
    {'telefone': '21-96716-7784', 'uso': 247.4, 'sessoes': 1598, 'status': 'Alto uso', 'usuario': 'BRUNA ROQUE'},
    {'telefone': '21-99973-8542', 'uso': 236.4, 'sessoes': 1287, 'status': 'Alto uso', 'usuario': 'SIMONE DUARTE'},
]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def create_linhas_com_uso_content():
    """Versão simplificada da aba de linhas com uso para teste"""
    
    return html.Div([
        html.H2("🔍 TESTE - Linhas em Uso", style={'color': '#2c3e50', 'textAlign': 'center'}),
        
        # Cards de estatísticas
        html.Div([
            html.Div([
                html.H3("5", style={'fontSize': '2.5rem', 'fontWeight': '200', 'color': '#2c3e50', 'margin': '0'}),
                html.P("Linhas de teste", style={'color': '#7f8c8d', 'margin': '10px 0 0 0'})
            ], style={'width': '30%', 'display': 'inline-block', 'textAlign': 'center', 'backgroundColor': '#f8f9fa', 'padding': '20px', 'margin': '10px', 'borderRadius': '8px'}),
        ], style={'marginBottom': '30px'}),
        
        # Tabela de linhas
        html.Div([
            html.H4("Teste - Linhas com uso ativo", 
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
                        'if': {'column_id': 'Status', 'filter_query': '{Status} = Alto uso'},
                        'backgroundColor': '#d4edda',
                        'color': '#155724',
                        'fontWeight': '500'
                    }
                ],
                page_size=10,
                style_table={'height': '400px', 'overflowY': 'auto'},
                filter_action="native",
                sort_action="native"
            )
        ], style={'backgroundColor': '#fff', 'border': '1px solid #e0e0e0', 'borderRadius': '8px'})
    ])

app.layout = html.Div([
    html.Div([
        html.H1("📱 Teste de Linhas Móveis", style={'color': '#2c3e50', 'textAlign': 'center'}),
        html.Hr(),
        
        # Navegação por abas
        dcc.Tabs(id="test-tabs", value="com-uso", children=[
            dcc.Tab(label="Linhas em Uso - TESTE", value="com-uso", style={'fontFamily': 'Inter, sans-serif'}),
        ], style={'fontFamily': 'Inter, sans-serif', 'marginBottom': '20px'}),
        
        # Conteúdo das abas
        html.Div(id="test-content"),
    ], style={'padding': '20px'})
])

@app.callback(
    Output('test-content', 'children'),
    Input('test-tabs', 'value')
)
def render_test_content(active_tab):
    """Renderiza o conteúdo do teste"""
    if active_tab == 'com-uso':
        return create_linhas_com_uso_content()
    else:
        return html.Div("Teste não implementado")

if __name__ == '__main__':
    print("🔍 Iniciando teste das linhas em uso...")
    print("📍 Acesse: http://127.0.0.1:8051")
    app.run(debug=True, host='127.0.0.1', port=8051)
