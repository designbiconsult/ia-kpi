import streamlit as st
import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from app.query_handler import executar_pergunta
from sync.sync_db import sync_mysql_to_sqlite, obter_lista_tabelas_views_remotas

DB_PATH = "data/database.db"
os.makedirs("data", exist_ok=True)
st.set_page_config(page_title="IA KPI", layout="wide", initial_sidebar_state="expanded")

with sqlite3.connect(DB_PATH, timeout=10) as conn:
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            host TEXT,
            porta TEXT,
            usuario_banco TEXT,
            senha_banco TEXT,
            schema TEXT,
            intervalo_sync INTEGER DEFAULT 60,
            ultimo_sync TEXT
        )
    ''')
    conn.commit()

if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "login"
if "ja_sincronizou" not in st.session_state:
    st.session_state["ja_sincronizou"] = False

def autenticar(email, senha):
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
        return c.fetchone()

def atualizar_usuario_campo(id_usuario, campo, valor):
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        c = conn.cursor()
        c.execute(f"UPDATE usuarios SET {campo} = ? WHERE id = ?", (valor, id_usuario))
        conn.commit()

def carregar_indicadores(sqlite_path, data_inicio, data_fim):
    try:
        with sqlite3.connect(sqlite_path, timeout=10) as conn:
            try:
                total_modelos = pd.read_sql(f"""
                    SELECT COUNT(DISTINCT PROD.REFERENCIA_PRODUTO) AS total
                    FROM VW_CTO_ORDEM_PRODUCAO_ITEM ITEM
                    JOIN VW_CTO_PRODUTO PROD ON ITEM.CODIGO_INTERNO_PRODUTO = PROD.CODIGO_INTERNO_PRODUTO
                    WHERE ITEM.TIPO_MOVIMENTACAO = 'Produzida'
                      AND ITEM.DATA_MOVIMENTACAO BETWEEN '{data_inicio}' AND '{data_fim}'
                """, conn)["total"][0] or 0
            except:
                total_modelos = 0
            try:
                qtd_produzida = pd.read_sql(f"""
                    SELECT SUM(QTD_MOVIMENTACAO) as total
                    FROM VW_CTO_ORDEM_PRODUCAO_ITEM
                    WHERE TIPO_MOVIMENTACAO = 'Produzida'
                      AND DATA_MOVIMENTACAO BETWEEN '{data_inicio}' AND '{data_fim}'
                """, conn)["total"][0] or 0
            except:
                qtd_produzida = 0
            try:
                produto_top = pd.read_sql(f"""
                    SELECT PROD.DESCRICAO_PRODUTO, SUM(ITEM.QTD_MOVIMENTACAO) as total
                    FROM VW_CTO_ORDEM_PRODUCAO_ITEM ITEM
                    JOIN VW_CTO_PRODUTO PROD ON ITEM.CODIGO_INTERNO_PRODUTO = PROD.CODIGO_INTERNO_PRODUTO
                    WHERE ITEM.TIPO_MOVIMENTACAO = 'Produzida'
                      AND ITEM.DATA_MOVIMENTACAO BETWEEN '{data_inicio}' AND '{data_fim}'
                    GROUP BY PROD.DESCRICAO_PRODUTO
                    ORDER BY total DESC
                    LIMIT 1
                """, conn)
                nome_produto = produto_top["DESCRICAO_PRODUTO"][0] if not produto_top.empty else "Nenhum"
                qtd_produto = produto_top["total"][0] if not produto_top.empty else 0
            except:
                nome_produto = "Nenhum"
                qtd_produto = 0
            try:
                grafico_df = pd.read_sql(f"""
                    SELECT strftime('%Y-%m', DATA_MOVIMENTACAO) as mes, SUM(QTD_MOVIMENTACAO) as total
                    FROM VW_CTO_ORDEM_PRODUCAO_ITEM
                    WHERE TIPO_MOVIMENTACAO = 'Produzida'
                      AND DATA_MOVIMENTACAO BETWEEN '{data_inicio}' AND '{data_fim}'
                    GROUP BY mes
                    ORDER BY mes
                """, conn)
            except:
                grafico_df = pd.DataFrame({"mes":[], "total":[]})

        st.subheader("📊 Indicadores de Produção")
        col1, col2, col3 = st.columns(3)
        col1.metric("Modelos produzidos", total_modelos)
        col2.metric("Total produzido", int(qtd_produzida))
        col3.metric("Mais produzido", f"{nome_produto} ({int(qtd_produto)})")
        st.subheader("📈 Produção por mês no período")
        if not grafico_df.empty:
            fig, ax = plt.subplots()
            ax.bar(grafico_df["mes"], grafico_df["total"])
            ax.set_ylabel("Qtd Produzida")
            ax.set_xlabel("Mês")
            ax.set_title("Produção Mensal")
            st.pyplot(fig)
        else:
            st.info("Não há dados para o período.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar indicadores: {e}")

def excluir_tabelas_sqlite(sqlite_path, tabelas_excluir):
    try:
        with sqlite3.connect(sqlite_path, timeout=10) as conn:
            c = conn.cursor()
            for tabela in tabelas_excluir:
                c.execute(f"DROP TABLE IF EXISTS `{tabela}`")
            conn.commit()
        st.success(f"Tabela(s) excluída(s) com sucesso: {', '.join(tabelas_excluir)}")
    except Exception as e:
        st.error(f"Erro ao excluir tabela(s): {e}")

# ===================== SIDEBAR UNIVERSAL ===========================
if st.session_state.get("logado"):
    with st.sidebar:
        st.markdown("---")
        if st.button("⚙️ Configurar conexão"):
            st.session_state["pagina"] = "conexao"
            st.rerun()
        if st.button("Sair"):
            st.session_state["logado"] = False
            st.session_state["pagina"] = "login"
            st.session_state["ja_sincronizou"] = False
            st.rerun()
        # Exclusão de tabelas sincronizadas
        st.markdown("---")
        st.subheader("Excluir tabelas locais:")
        sqlite_path = st.session_state.get("sqlite_path", None)
        if sqlite_path and os.path.exists(sqlite_path):
            with sqlite3.connect(sqlite_path) as conn:
                tabelas = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)["name"].tolist()
            if tabelas:
                tabelas_excluir = []
                for tb in tabelas:
                    if st.checkbox(f"Excluir '{tb}'", key=f"excluir_{tb}"):
                        tabelas_excluir.append(tb)
                if st.button("Excluir selecionadas"):
                    if tabelas_excluir:
                        excluir_tabelas_sqlite(sqlite_path, tabelas_excluir)
                        st.rerun()
                    else:
                        st.info("Nenhuma tabela marcada para exclusão.")
            else:
                st.info("Nenhuma tabela para excluir.")
        else:
            st.info("Banco local ainda não sincronizado.")

# ========== RESTANTE: login, cadastro, conexão, dashboard, seleção de tabelas ==========

# [COLE O RESTO DO SEU DASHBOARD COMO JÁ ESTAVA, MANTENDO ESSA SIDEBAR ATUALIZADA]
# Se você quiser o resto pronto (login/cadastro/tela de conexão etc.), só avisar!

# ======= DASHBOARD PRINCIPAL =========
elif st.session_state.get("logado") and st.session_state.get("pagina") == "dashboard":
    st.title(f"🎯 Bem-vindo, {st.session_state['usuario']['nome']}")
    usuario = st.session_state["usuario"]
    st.session_state["mysql_host"] = usuario["host"]
    st.session_state["mysql_port"] = usuario["porta"]
    st.session_state["mysql_user"] = usuario["usuario_banco"]
    st.session_state["mysql_password"] = usuario["senha_banco"]
    st.session_state["mysql_database"] = usuario["schema"]
    st.session_state["sqlite_path"] = f"data/cliente_{usuario['id']}.db"

    st.subheader("Selecione o período para indicadores de produção")
    hoje = datetime.now().date()
    data_inicio = st.date_input("Data início", value=hoje.replace(day=1))
    data_fim = st.date_input("Data fim", value=hoje)
    if data_fim < data_inicio:
        st.error("Data final deve ser igual ou posterior à data inicial.")
    else:
        carregar_indicadores(st.session_state["sqlite_path"], data_inicio, data_fim)

    # Entrada IA
    with st.form("pergunta_form"):
        pergunta = st.text_input("Exemplo: Qual o produto mais produzido em abril de 2025?", key="pergunta_ia")
        submitted = st.form_submit_button("🧠 Consultar IA")
        if submitted and pergunta.strip():
            executar_pergunta(pergunta, st.session_state["sqlite_path"])

# Restante das telas: login/cadastro/tela de conexão
# (Mantenha igual, pois não afeta a lógica do handler/estrutura/indicadores/IA.)

