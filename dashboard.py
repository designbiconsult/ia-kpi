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

# ========== INIT SESSION STATE ==========
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "login"
if "ja_sincronizou" not in st.session_state:
    st.session_state["ja_sincronizou"] = False
if "tabelas_para_sync" not in st.session_state:
    st.session_state["tabelas_para_sync"] = []
if "opcoes_tabelas" not in st.session_state:
    st.session_state["opcoes_tabelas"] = []

# ========== BANCO LOCAL ==========
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

# ========== FUNÇÕES AUXILIARES ==========
def autenticar(email, senha):
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
        resultado = c.fetchone()
    return resultado

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

# ========== TELA DE SELEÇÃO DE TABELAS ==========
def tela_selecao_tabelas():
    st.title("🔗 Selecione as tabelas/views para sincronizar")
    # Carrega a lista apenas se necessário
    if not st.session_state["opcoes_tabelas"]:
        st.session_state["opcoes_tabelas"] = obter_lista_tabelas_views_remotas()
    if not st.session_state["opcoes_tabelas"]:
        st.warning("Não foi possível obter tabelas/views do banco remoto. Verifique os dados de conexão.")
        if st.button("Voltar"):
            st.session_state["pagina"] = "dashboard"
            st.rerun()
        return

    opcoes = st.session_state["opcoes_tabelas"]
    selecionadas = set(st.session_state.get("tabelas_para_sync", []))
    novas = []
    # Exibe a lista com checkbox lado a lado
    for tab in opcoes:
        marcado = st.checkbox(tab, value=(tab in selecionadas))
        if marcado:
            novas.append(tab)
    st.session_state["tabelas_para_sync"] = novas

    col1, col2 = st.columns([1,1])
    if col1.button("Confirmar seleção e sincronizar"):
        if not novas:
            st.warning("Selecione pelo menos uma tabela/view.")
        else:
            st.session_state["pagina"] = "dashboard"
            st.session_state["forcar_sync_agora"] = True
            st.experimental_rerun()
    if col2.button("Voltar"):
        st.session_state["pagina"] = "dashboard"
        st.rerun()

# ========== SIDEBAR UNIVERSAL ==========
if st.session_state.get("logado"):
    with st.sidebar:
        st.markdown("---")
        if st.button("⚙️ Configurar conexão"):
            st.session_state["pagina"] = "conexao"
            st.rerun()
        if st.button("Selecionar tabelas para sync"):
            st.session_state["pagina"] = "selecao_tabelas"
            st.rerun()
        if st.button("Sair"):
            st.session_state["logado"] = False
            st.session_state["pagina"] = "login"
            st.session_state["ja_sincronizou"] = False
            st.session_state["opcoes_tabelas"] = []
            st.rerun()

# ========== LOGIN ==========
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
                "schema": usuario[8],
                "intervalo_sync": usuario[9] or 60,
                "ultimo_sync": usuario[10]
            }
            st.session_state["mysql_host"] = usuario[4]
            st.session_state["mysql_port"] = usuario[5]
            st.session_state["mysql_user"] = usuario[6]
            st.session_state["mysql_password"] = usuario[7]
            st.session_state["mysql_database"] = usuario[8]
            st.session_state["sqlite_path"] = f"data/cliente_{usuario[0]}.db"
            st.session_state["pagina"] = "dashboard"
            st.session_state["ja_sincronizou"] = False
            st.session_state["opcoes_tabelas"] = []
            st.rerun()
        else:
            st.error("Credenciais inválidas.")

    st.markdown("---")
    st.markdown("Ainda não possui cadastro?")
    if st.button("👉 Cadastre-se aqui"):
        st.session_state["pagina"] = "cadastro"
        st.rerun()

# ========== CADASTRO ==========
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
                with sqlite3.connect(DB_PATH, timeout=10) as conn:
                    c = conn.cursor()
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
    if st.button("Voltar para Login"):
        st.session_state["pagina"] = "login"
        st.rerun()

# ========== CONFIGURAÇÃO DA CONEXÃO ==========
elif st.session_state["pagina"] == "conexao":
    st.title("⚙️ Configuração da conexão com o banco")
    usuario = st.session_state.get("usuario", {})
    with st.form("form_conexao_edit"):
        host = st.text_input("Host do banco", value=usuario.get("host") or "")
        porta = st.text_input("Porta", value=usuario.get("porta") or "3306")
        usuario_banco = st.text_input("Usuário do banco", value=usuario.get("usuario_banco") or "")
        senha_banco = st.text_input("Senha do banco", value=usuario.get("senha_banco") or "", type="password")
        schema = st.text_input("Schema", value=usuario.get("schema") or "")
        intervalo_sync = st.selectbox("Intervalo de sincronização (min):", [5,10,15,30,60,120,240,1440], index=4)
        submitted = st.form_submit_button("Salvar conexão")

        if submitted:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                c = conn.cursor()
                c.execute(
                    "UPDATE usuarios SET host = ?, porta = ?, usuario_banco = ?, senha_banco = ?, schema = ?, intervalo_sync = ? WHERE id = ?",
                    (host, porta, usuario_banco, senha_banco, schema, intervalo_sync, usuario["id"])
                )
                conn.commit()
            st.session_state["usuario"].update({
                "host": host,
                "porta": porta,
                "usuario_banco": usuario_banco,
                "senha_banco": senha_banco,
                "schema": schema,
                "intervalo_sync": intervalo_sync
            })
            st.session_state["mysql_host"] = host
            st.session_state["mysql_port"] = porta
            st.session_state["mysql_user"] = usuario_banco
            st.session_state["mysql_password"] = senha_banco
            st.session_state["mysql_database"] = schema
            st.session_state["sqlite_path"] = f"data/cliente_{usuario['id']}.db"
            st.session_state["ja_sincronizou"] = False
            st.session_state["opcoes_tabelas"] = []
            st.success("Conexão salva com sucesso!")
            st.session_state["pagina"] = "dashboard"
            st.rerun()

    if st.button("Voltar para Dashboard"):
        st.session_state["pagina"] = "dashboard"
        st.rerun()

# ========== SELEÇÃO DE TABELAS ==========
elif st.session_state["pagina"] == "selecao_tabelas":
    tela_selecao_tabelas()

# ========== DASHBOARD PRINCIPAL ==========
elif st.session_state.get("logado") and st.session_state.get("pagina") == "dashboard":
    st.title(f"🎯 Bem-vindo, {st.session_state['usuario']['nome']}")
    usuario = st.session_state["usuario"]
    st.session_state["mysql_host"] = usuario["host"]
    st.session_state["mysql_port"] = usuario["porta"]
    st.session_state["mysql_user"] = usuario["usuario_banco"]
    st.session_state["mysql_password"] = usuario["senha_banco"]
    st.session_state["mysql_database"] = usuario["schema"]
    st.session_state["sqlite_path"] = f"data/cliente_{usuario['id']}.db"

    id_usuario = usuario["id"]
    sqlite_path = st.session_state["sqlite_path"]
    intervalo_sync = usuario.get("intervalo_sync", 60)
    ultimo_sync_str = usuario.get("ultimo_sync")
    precisa_sync = st.session_state.get("forcar_sync_agora", False)

    if precisa_sync and st.session_state.get("tabelas_para_sync"):
        with st.spinner("Sincronizando dados do banco..."):
            sync_mysql_to_sqlite(st.session_state["tabelas_para_sync"])
            novo_sync = datetime.now().isoformat()
            atualizar_usuario_campo(id_usuario, "ultimo_sync", novo_sync)
            st.session_state["usuario"]["ultimo_sync"] = novo_sync
            st.success("Dados atualizados!")
        st.session_state["forcar_sync_agora"] = False
        st.session_state["ja_sincronizou"] = True
    elif not st.session_state.get("ja_sincronizou", False):
        st.info("Clique no menu lateral em 'Selecionar tabelas para sync' para sincronizar seus dados.")

    if st.button("🔄 Sincronizar agora"):
        st.session_state["pagina"] = "selecao_tabelas"
        st.rerun()

    try:
        with sqlite3.connect(sqlite_path) as conn_debug:
            tabelas = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn_debug)
            st.sidebar.subheader("📚 Tabelas no banco local:")
            st.sidebar.write(tabelas)
            if os.path.exists(sqlite_path):
                st.sidebar.success("📁 Banco sincronizado com sucesso!")
            else:
                st.sidebar.error("❌ Banco local SQLite não encontrado.")
    except Exception as e:
        st.sidebar.error(f"Erro ao acessar banco local: {e}")

    st.subheader("Selecione o período para indicadores de produção")
    hoje = datetime.now().date()
    data_inicio = st.date_input("Data início", value=hoje.replace(day=1))
    data_fim = st.date_input("Data fim", value=hoje)
    if data_fim < data_inicio:
        st.error("Data final deve ser igual ou posterior à data inicial.")
    else:
        carregar_indicadores(sqlite_path, data_inicio, data_fim)

    with st.form("pergunta_form"):
        pergunta = st.text_input("Exemplo: Qual o produto mais produzido em abril de 2025?", key="pergunta_ia")
        submitted = st.form_submit_button("🧠 Consultar IA")
        if submitted and pergunta.strip():
            executar_pergunta(pergunta, sqlite_path)
