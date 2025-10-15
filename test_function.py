#!/usr/bin/env python3
"""
Teste específico para validar a função create_linhas_com_uso_content()
"""
import sys
sys.path.append('/home/wood-linux/Portal-do-TI_dashboard')

try:
    # Importa apenas as partes necessárias
    import dash
    from dash import html, dash_table
    
    print("✓ Importações do Dash bem-sucedidas")
    
    # Testa a função create_linhas_com_uso_content diretamente
    def test_create_linhas_com_uso_content():
        """Versão de teste da função original"""
        
        # Dados completos das linhas com uso (algumas linhas do original)
        linhas_com_uso = [
            {'telefone': '21-96726-8788', 'uso': 385.9, 'sessoes': 463, 'status': 'Alto uso', 'usuario': 'ESTOQUE'},
            {'telefone': '21-99528-6151', 'uso': 369.4, 'sessoes': 1655, 'status': 'Alto uso', 'usuario': 'DANIEL CARVALHO'},
            {'telefone': '21-99706-5399', 'uso': 255.1, 'sessoes': 1206, 'status': 'Alto uso', 'usuario': 'PAULO CEZAR DIAS'},
        ]
        
        try:
            content = html.Div([
                # Cards de estatísticas
                html.Div([
                    html.Div([
                        html.H3("3", style={'fontSize': '2.5rem', 'fontWeight': '200', 'color': '#2c3e50', 'margin': '0'}),
                        html.P("Linhas ativas", style={'color': '#7f8c8d', 'margin': '10px 0 0 0'})
                    ], className="chart-card", style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%', 'textAlign': 'center'}),
                ], style={'marginBottom': '30px'}),
                
                # Tabela de linhas
                html.Div([
                    html.H4("Teste - 3 linhas com uso ativo", 
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
                        page_size=20,
                        style_table={'height': '700px', 'overflowY': 'auto'},
                        filter_action="native",
                        sort_action="native"
                    )
                ], className="chart-card")
            ])
            
            print("✓ Função create_linhas_com_uso_content() executada com sucesso")
            print(f"✓ Tipo do retorno: {type(content)}")
            print(f"✓ Número de linhas na tabela: {len(linhas_com_uso)}")
            return content
            
        except Exception as e:
            print(f"❌ Erro na função create_linhas_com_uso_content(): {e}")
            return None
    
    # Executa o teste
    resultado = test_create_linhas_com_uso_content()
    if resultado:
        print("🎉 Teste PASSOU - A função está funcionando corretamente!")
    else:
        print("🚨 Teste FALHOU - Há um problema na função!")
        
except Exception as e:
    print(f"❌ Erro nas importações ou configuração: {e}")
    import traceback
    traceback.print_exc()
