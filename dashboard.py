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
        schema TEXT
    )
''')
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

def carregar_indicadores(sqlite_path):
    try:
        conn = sqlite3.connect(sqlite_path)

        total_produtos = pd.read_sql("SELECT COUNT(*) as total FROM VW_CTO_PRODUTO", conn)["total"][0]

        qtd_mes = pd.read_sql("""
            SELECT SUM(QTD_MOVIMENTACAO) as total
            FROM VW_CTO_ORDEM_PRODUCAO_ITEM
            WHERE TIPO_MOVIMENTACAO = 'Produzida'
              AND strftime('%Y-%m', DATA_MOVIMENTACAO) = strftime('%Y-%m', 'now')
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
        col1.metric("Produtos cadastrados", total_produtos)
        col2.metric("Produzido neste mês", int(qtd_mes))
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


# === Login
if st.session_state["pagina"] == "login" and not st.session_state["logado"]:
    st.title("🔐 Login IA KPI")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        usuario = autenticar(email, senha)
        if usuario:
            st.session_state["logado"] = True
            st.session_state["usuario"] = {
                "id": usuario[0],
                "nome": usuario[1],
                "email": usuario[2],
                "host": usuario[4],
                "porta": usuario[5],
                "usuario_banco": usuario[6],
                "senha_banco": usuario[7],
                "schema": usuario[8]
            }
            st.session_state["pagina"] = "dashboard"
            st.rerun()
        else:
            st.error("Credenciais inválidas.")

    st.markdown("---")
    st.markdown("Ainda não possui cadastro?")
    if st.button("👉 Cadastre-se aqui"):
        st.session_state["pagina"] = "cadastro"
        st.rerun()

# === Cadastro
elif st.session_state["pagina"] == "cadastro" and not st.session_state["logado"]:
    st.title("📊 Cadastro de Cliente IA KPI")
    with st.form("cadastro_form"):
        nome = st.text_input("Nome completo")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            if not (nome and email and senha):
                st.error("Preencha todos os campos.")
            else:
                try:
                    c.execute(
                        "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                        (nome, email, senha)
                    )
                    conn.commit()
                    st.success("Cadastro realizado com sucesso! Faça login para continuar.")
                    st.session_state["pagina"] = "login"
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Este email já está cadastrado.")

# === Dashboard
elif st.session_state["logado"] and st.session_state["pagina"] == "dashboard":
    st.title(f"🎯 Bem-vindo, {st.session_state['usuario']['nome']}")

    if not st.session_state['usuario']["host"]:
        st.warning("Configure a conexão com o banco de dados para continuar.")
        with st.form("conexao_form"):
            host = st.text_input("Host do banco")
            porta = st.text_input("Porta", value="3306")
            usuario_banco = st.text_input("Usuário do banco")
            senha_banco = st.text_input("Senha do banco", type="password")
            schema = st.text_input("Schema (ex: dbview)")
            submitted = st.form_submit_button("Salvar conexão")

            if submitted:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute(
                        "UPDATE usuarios SET host = ?, porta = ?, usuario_banco = ?, senha_banco = ?, schema = ? WHERE id = ?",
                        (host, porta, usuario_banco, senha_banco, schema, st.session_state["usuario"]["id"])
                    )
                    conn.commit()
                    conn.close()
                    st.session_state["usuario"].update({
                        "host": host,
                        "porta": porta,
                        "usuario_banco": usuario_banco,
                        "senha_banco": senha_banco,
                        "schema": schema
                    })
                    st.success("Conexão salva com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar conexão: {e}")
    else:
        st.session_state["mysql_host"] = st.session_state["usuario"]["host"]
        st.session_state["mysql_port"] = st.session_state["usuario"]["porta"]
        st.session_state["mysql_user"] = st.session_state["usuario"]["usuario_banco"]
        st.session_state["mysql_password"] = st.session_state["usuario"]["senha_banco"]
        st.session_state["mysql_database"] = st.session_state["usuario"]["schema"]
        st.session_state["sqlite_path"] = f"data/cliente_{st.session_state['usuario']['id']}.db"
        
        with st.sidebar:
            st.markdown("---")
    if st.button("🔄 Re-sincronizar dados"):
        with st.spinner("Sincronizando dados do banco..."):
            sync_mysql_to_sqlite()
            st.success("Dados atualizados com sucesso!")
            st.rerun()


        carregar_indicadores(st.session_state["sqlite_path"])
        if os.path.exists(st.session_state["sqlite_path"]):
            st.sidebar.success("📁 Banco sincronizado com sucesso!")
        else:
            st.sidebar.error("❌ Banco local SQLite não encontrado.")


        st.subheader("Faça sua pergunta à IA")
        pergunta = st.text_input("Exemplo: Qual o produto mais produzido em abril de 2025?")
        if st.button("🧠 Consultar IA"):
            executar_pergunta(pergunta, st.session_state["sqlite_path"])

        if st.sidebar.button("Sair"):
            st.session_state["logado"] = False
            st.session_state["pagina"] = "login"
            st.rerun()
