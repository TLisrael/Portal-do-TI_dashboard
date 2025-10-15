# 📊 Portal do TI - Dashboard

Um dashboard interativo para gestão de equipamentos de TI, colaboradores e terceirizados, desenvolvido com Dash e Python.

## 🚀 Funcionalidades

### 📈 Dashboard Principal
- **KPIs em tempo real**: Visualização de métricas importantes do departamento de TI
- **Gráficos interativos**: Distribuição de equipamentos, status de colaboradores e terceirizados
- **Sistema de alertas**: Notificações automáticas para situações que requerem atenção

### 👥 Gestão de Pessoas
- **Colaboradores**: Controle de funcionários ativos, demitidos e em aviso prévio
- **Terceirizados**: Monitoramento de terceirizados ativos e inativos
- **Equipamentos por pessoa**: Rastreamento de equipamentos alocados

### 💻 Gestão de Equipamentos
- **Inventário**: Controle completo do estoque de computadores e periféricos
- **Status de equipamentos**: Monitoramento de equipamentos em uso, estoque, descartados, etc.
- **Alertas de gestão**: Identificação de colaboradores demitidos com equipamentos não devolvidos

### 📊 Relatórios e Análises
- **Distribuição por modelo**: Análise dos equipamentos por marca e modelo
- **Idade dos equipamentos**: Controle do ciclo de vida dos equipamentos
- **Relatórios de estoque**: Visualização detalhada do inventário disponível

## 🛠️ Tecnologias Utilizadas

- **Python 3.12+**
- **Dash** - Framework web para aplicações analíticas
- **Plotly** - Visualizações interativas
- **Pandas** - Manipulação de dados
- **SQLAlchemy** - ORM para banco de dados
- **SQL Server** - Banco de dados principal
- **Bootstrap** - Componentes de interface

## 📋 Pré-requisitos

### Sistema Operacional
- **Linux** (Ubuntu/Debian/CentOS/RHEL)
- **Windows** (compatibilidade mantida)

### Banco de Dados
- **SQL Server** (local ou remoto)
- **Drivers ODBC** configurados (para Linux)

### Python
- **Python 3.8+** (recomendado 3.12+)
- **pip** (gerenciador de pacotes)

## 🔧 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/TLisrael/Portal-do-TI_dashboard.git
cd Portal-do-TI_dashboard
```

### 2. Configure o ambiente virtual
```bash
# Criar ambiente virtual
python3 -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure os drivers de banco (Linux)
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y unixodbc unixodbc-dev freetds-dev freetds-bin tdsodbc

# CentOS/RHEL
sudo yum install -y unixODBC unixODBC-devel freetds freetds-devel

# Configure o FreeTDS
echo "[FreeTDS]
Description = FreeTDS Driver
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so" | sudo tee -a /etc/odbcinst.ini
```

### 5. Configure a conexão com o banco
Edite as configurações no arquivo `app.py`:

```python
DB_CONFIG = {
    'server': 'seu-servidor-sql',
    'database': 'ControleTI',
    'username': 'seu-usuario',
    'password': 'sua-senha',
    'port': '1433'
}
```

### 6. Teste a conexão
```bash
python test_connection.py
```

## 🚀 Execução

### Desenvolvimento
```bash
python app.py
```

### Produção
```bash
# Com Gunicorn (recomendado para produção)
pip install gunicorn
gunicorn app:server -b 0.0.0.0:8050

# Ou direto com Python
python app.py
```

O dashboard estará disponível em: `http://localhost:8050`

## 📁 Estrutura do Projeto

```
Portal-do-TI_dashboard/
├── app.py                    # Aplicação principal
├── requirements.txt          # Dependências
├── test_connection.py        # Teste de conexão
├── diagnostico_status.py     # Diagnósticos de status
├── fix_critical_color.py     # Correções de cores críticas
├── fix_status_color.py       # Correções de cores de status
├── teste_status.py          # Testes de status
├── SELECT.sql               # Queries SQL de referência
├── desligamento.xlsx        # Dados de desligamentos
├── idade_computadores.xlsx  # Dados de idade dos equipamentos
└── README.md               # Documentação
```

## 🔧 Configuração do Banco de Dados

### Estrutura Esperada

O sistema espera as seguintes tabelas no SQL Server:

#### Tabela `Colaboradores`
```sql
- Matricula (PK)
- Nome
- Situacao ('Ativo', 'Demitido', 'Aviso Prévio')
- CCusto
- Chefia
```

#### Tabela `Terceirizados`
```sql
- Matricula (PK)
- Nome
- Situacao (0 = Inativo, 1 = Ativo)
- Chefia
```

#### Tabela `Computadores`
```sql
- ID (PK)
- Serial
- Modelo
- Matricula (FK)
- Usuario
- Status
```

#### Tabela `Perifericos`
```sql
- ID (PK)
- Modelo
- Matricula (FK)
```

## 🔍 Funcionalidades Principais

### Dashboard Principal
- **Visão Geral**: Cards com métricas principais
- **Gráficos Dinâmicos**: Atualização automática dos dados
- **Filtros Interativos**: Seleção por período, departamento, etc.

### Alertas Inteligentes
- **Colaboradores demitidos com equipamentos**
- **Equipamentos sem responsável**
- **Colaboradores ativos sem equipamento**

### Relatórios
- **Exportação para Excel**
- **Gráficos de tendência**
- **Análises comparativas**

## 🐛 Solução de Problemas

### Erro de Conexão com Banco
1. Verifique as credenciais no `DB_CONFIG`
2. Teste a conectividade de rede com o servidor SQL
3. Execute `python test_connection.py` para diagnóstico

### Problemas com Drivers ODBC (Linux)
```bash
# Verificar drivers instalados
odbcinst -q -d

# Reinstalar drivers se necessário
sudo apt-get remove --purge unixodbc
sudo apt-get install unixodbc unixodbc-dev
```

### Porta já em uso
```bash
# Alterar porta no arquivo app.py
app.run(debug=False, host='0.0.0.0', port=8051)
```

## 🔒 Segurança

- **Nunca** commite credenciais no repositório
- Use variáveis de ambiente para configurações sensíveis
- Configure firewall apropriadamente para o ambiente de produção
- Implemente autenticação se necessário

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte e dúvidas:
- **Issues**: Abra uma issue no GitHub
- **Email**: Entre em contato com a equipe de desenvolvimento

## 🔄 Changelog

### v1.0.0
- Dashboard principal com KPIs
- Sistema de alertas
- Gestão de colaboradores e terceirizados
- Controle de equipamentos
- Compatibilidade com Linux

---

**Desenvolvido com ❤️ pela equipe de TI**
