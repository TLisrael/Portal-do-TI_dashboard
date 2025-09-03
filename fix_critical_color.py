import re

# Lê o arquivo
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Substitui a cor do título "Equipamentos Críticos (Descartados/Danificados)"
# Usa regex para encontrar especificamente essa seção
pattern = r"(html\.H4\(\"🚨 Equipamentos Críticos \(Descartados/Danificados\)\", style=\{\s+'margin-bottom': '1\.5rem',\s+)'color': '#1e1e1e',"
replacement = r"\1'color': 'white',"

if re.search(pattern, content):
    content = re.sub(pattern, replacement, content)
    print("✓ Título do card 'Equipamentos Críticos' alterado para cor branca!")
    
    # Salva o arquivo
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
else:
    print("❌ Padrão não encontrado. Listando ocorrências...")
    # Procura por padrões similares para debug
    matches = re.findall(r"html\.H4\(.*?Equipamentos Críticos.*?\)", content, re.DOTALL)
    for i, match in enumerate(matches):
        print(f"Match {i+1}: {match[:200]}...")

print("Script concluído!")
