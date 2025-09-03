#!/usr/bin/env python3
# Script para corrigir a cor do título da seção de Análise de Equipamentos por Status

# Lê o arquivo app.py
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Substitui a cor do título da seção específica
# Procura por uma string única que identifica essa seção
old_text = "html.H4(\"📊 Análise de Equipamentos por Status\", style={\n                    'margin-bottom': '1.5rem',\n                    'color': '#1e1e1e',"
new_text = "html.H4(\"📊 Análise de Equipamentos por Status\", style={\n                    'margin-bottom': '1.5rem',\n                    'color': 'white',"

# Faz a substituição
if old_text in content:
    content = content.replace(old_text, new_text)
    print("✓ Texto encontrado e substituído com sucesso!")
else:
    print("❌ Texto não encontrado. Vamos tentar uma busca mais genérica...")
    # Busca alternativa - procura pelo padrão específico
    import re
    pattern = r"(html\.H4\(\"📊 Análise de Equipamentos por Status\", style=\{\s*'margin-bottom': '1\.5rem',\s*)'color': '#1e1e1e',"
    replacement = r"\1'color': 'white',"
    
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        print("✓ Substituição feita usando regex!")
    else:
        print("❌ Não foi possível encontrar o padrão. Vamos listar as ocorrências...")
        # Mostra todas as ocorrências de H4 com "Análise"
        matches = re.findall(r"html\.H4\(.*?Análise.*?\)", content, re.DOTALL)
        for i, match in enumerate(matches):
            print(f"Match {i+1}: {match[:100]}...")

# Escreve o arquivo modificado
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Script executado!")
