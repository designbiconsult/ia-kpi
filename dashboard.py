import streamlit as st
import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt
from app.query_handler import executar_pergunta
from sync.sync_db import sync_mysql_to_sqlite

DB_PATH = "data/database.db"
os.makedirs("data", exist_ok=True)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Criação da tabela de usuários
c.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    host TEXT,
    porta TEXT,
    usuario_banco TEXT,
    senha_banco TEXT,
    schema TEXT
)
""")
conn.commit()

st.set_page_config(page_title="IA KPI", layout="wide", initial_sidebar_state="expanded")

# Estados de sessão
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "login"

def autenticar(email, senha):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
    resultado = c.fetchone()
    conn.close()
    return resultado

def carregar_indicadores(sqlite_path, mes_ano):
    try:
        conn = sqlite3.connect(sqlite_path)

        total_modelos = pd.read_sql(f"""
            SELECT COUNT(DISTINCT PROD.REFERENCIA_PRODUTO) AS total
            FROM VW_CTO_ORDEM_PRODUCAO_ITEM ITEM
            JOIN VW_CTO_PRODUTO PROD ON ITEM.CODIGO_INTERNO_PRODUTO = PROD.CODIGO_INTERNO_PRODUTO
            WHERE ITEM.TIPO_MOVIMENTACAO = 'Produzida'
              AND strftime('%Y-%m', ITEM.DATA_MOVIMENTACAO) = '{mes_ano}'
        """, conn)["total"][0] or 0

        qtd_mes = pd.read_sql(f"""
            SELECT SUM(QTD_MOVIMENTACAO) as total
            FROM VW_CTO_ORDEM_PRODUCAO_ITEM
            WHERE TIPO_MOVIMENTACAO = 'Produzida'
              AND strftime('%Y-%m', DATA_MOVIMENTACAO) = '{mes_ano}'
        """, conn)["total"][0] or 0

        produto_top = pd.read_sql("""
            SELECT ITEM.CODIGO_INTERNO_PRODUTO, PROD.DESCRICAO_PRODUTO, SUM(ITEM.QTD_MOVIMENTACAO) as total
            FROM VW_CTO_ORDEM_PRODUCAO_ITEM ITEM
            LEFT JOIN VW_CTO_PRODUTO PROD ON ITEM.CODIGO_INTERNO_PRODUTO = PROD.CODIGO_INTERNO_PRODUTO
            WHERE ITEM.TIPO_MOVIMENTACAO = 'Produzida'
              AND ITEM.DATA_MOVIMENTACAO >= date('now', '-3 months')
            GROUP BY ITEM.CODIGO_INTERNO_PRODUTO
            ORDER BY total DESC
            LIMIT 1
        """, conn)

        nome_produto = produto_top["DESCRICAO_PRODUTO"][0] if not produto_top.empty else "Nenhum"
        qtd_produto = produto_top["total"][0] if not produto_top.empty else 0

        grafico_df = pd.read_sql("""
            SELECT strftime('%Y-%m', DATA_MOVIMENTACAO) as mes, SUM(QTD_MOVIMENTACAO) as total
            FROM VW_CTO_ORDEM_PRODUCAO_ITEM
            WHERE TIPO_MOVIMENTACAO = 'Produzida'
              AND DATA_MOVIMENTACAO >= date('now', '-6 months')
            GROUP BY mes
            ORDER BY mes
        """, conn)

        conn.close()

        st.subheader("📊 Indicadores básicos")
        col1, col2, col3 = st.columns(3)
        col1.metric("Modelos produzidos", total_modelos)
        col2.metric("Total produzido", int(qtd_mes))
        col3.metric("Mais produzido (3 meses)", f"{nome_produto} ({int(qtd_produto)})")

        st.subheader("📈 Produção - últimos 6 meses")
        fig, ax = plt.subplots()
        ax.bar(grafico_df["mes"], grafico_df["total"])
        ax.set_ylabel("Qtd Produzida")
        ax.set_xlabel("Mês")
        ax.set_title("Produção Mensal")
        st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Erro ao carregar indicadores: {e}")
        st.exception(e)

# Exemplo de uso:
if st.session_state.get("logado") and st.session_state.get("pagina") == "dashboard":
    # seletor de mês/ano
    meses = pd.date_range(end=pd.Timestamp.today(), periods=12, freq="M").strftime("%Y-%m").tolist()
    mes_ano = st.selectbox("📅 Selecione o mês para os indicadores", meses[::-1])
    
    if "sqlite_path" in st.session_state:
        carregar_indicadores(st.session_state["sqlite_path"], mes_ano)
