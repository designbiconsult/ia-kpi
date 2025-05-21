# 📊 IA-KPI – Assistente de Indicadores com Inteligência Artificial

**IA-KPI** é uma aplicação web que conecta-se a qualquer banco de dados e gera indicadores de negócio (KPIs) automaticamente com auxílio de Inteligência Artificial.

Desenvolvido especialmente para empresas que utilizam sistemas com views estruturadas (como `dbview`) e desejam extrair insights rápidos sem conhecimento técnico em SQL.

---

## 🚀 Funcionalidades

- 🔐 Cadastro e login de usuários
- 🔌 Conexão dinâmica a banco de dados (MySQL)
- 📥 Sincronização automática de views e tabelas para SQLite
- 📊 Indicadores básicos com cartões e gráficos
- 💬 Consulta de dados via IA (natural language to SQL)
- 🎯 Personalização e criação de novos KPIs com linguagem natural

---

## ✅ Pré-requisitos

- Python 3.10 ou superior
- MySQL (em produção) com views disponíveis
- Pip instalado
- Git (para versionamento e clonagem)

---

## ⚙️ Como rodar localmente

```bash
# Clone o repositório
git clone https://github.com/designbiconsult/ia-kpi.git
cd ia-kpi

# Crie o ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # no Windows

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
streamlit run Dashboard.py
