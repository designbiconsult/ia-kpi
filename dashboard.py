import streamlit as st
import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from app.query_handler import executar_pergunta
from sync.sync_db import sync_mysql_to_sqlite

DB_PATH = "data/database.db"
os.makedirs("data", exist_ok=True)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Criação/upgrade da tabela de usuários com campos de sincronização
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

st.set_page_config(page_title="IA KPI", layout="wide", initial_sidebar_state="expanded")

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

def atualizar_usuario_campo(id_usuario, campo, valor):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"UPDATE usuarios SET {campo} = ? WHERE id = ?", (valor, id_usuario))
    conn.commit()
    conn.close()

def carregar_indicadores(sqlite_path):
    try:
        conn = sqlite3.connect(sqlite_path)
        # ... [seus indicadores] ...
        conn.close()
        st.write("Indicadores aqui")
    except Exception as e:
        st.error(f"❌ Erro ao carregar indicadores: {e}")

# ====================== LOGIN ==============================
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
            st.session_state["pagina"] = "dashboard"
            st.rerun()
        else:
            st.error("Credenciais inválidas.")

    st.markdown("---")
    st.markdown("Ainda não possui cadastro?")
    if st.button("👉 Cadastre-se aqui"):
        st.session_state["pagina"] = "cadastro"
        st.rerun()

# =================== CADASTRO ==============================
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

# =============== DASHBOARD ========================
elif st.session_state["logado"] and st.session_state["pagina"] == "dashboard":
    st.title(f"🎯 Bem-vindo, {st.session_state['usuario']['nome']}")

    # Configuração dos dados de conexão ao banco
    if not st.session_state['usuario']["host"]:
        st.warning("Configure a conexão com o banco de dados para continuar.")
        with st.form("conexao_form"):
            host = st.text_input("Host do banco")
            porta = st.text_input("Porta", value="3306")
            usuario_banco = st.text_input("Usuário do banco")
            senha_banco = st.text_input("Senha do banco", type="password")
            schema = st.text_input("Schema (ex: dbview)")
            intervalo_sync = st.selectbox("Intervalo de sincronização (min):", [5,10,15,30,60,120,240,1440], index=4)
            submitted = st.form_submit_button("Salvar conexão")

            if submitted:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute(
                        "UPDATE usuarios SET host = ?, porta = ?, usuario_banco = ?, senha_banco = ?, schema = ?, intervalo_sync = ? WHERE id = ?",
                        (host, porta, usuario_banco, senha_banco, schema, intervalo_sync, st.session_state["usuario"]["id"])
                    )
                    conn.commit()
                    conn.close()
                    st.session_state["usuario"].update({
                        "host": host,
                        "porta": porta,
                        "usuario_banco": usuario_banco,
                        "senha_banco": senha_banco,
                        "schema": schema,
                        "intervalo_sync": intervalo_sync
                    })
                    st.success("Conexão salva com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar conexão: {e}")
    else:
        # === Controle de sincronização automática ===
        id_usuario = st.session_state["usuario"]["id"]
        sqlite_path = f"data/cliente_{id_usuario}.db"
        intervalo_sync = st.session_state["usuario"].get("intervalo_sync", 60)
        ultimo_sync_str = st.session_state["usuario"].get("ultimo_sync")
        precisa_sync = False

        # Checa se precisa sincronizar
        if not ultimo_sync_str:
            precisa_sync = True
        else:
            try:
                dt_ultimo = datetime.fromisoformat(ultimo_sync_str)
                if datetime.now() > dt_ultimo + timedelta(minutes=int(intervalo_sync)):
                    precisa_sync = True
            except Exception:
                precisa_sync = True

        # Executa sincronização se necessário
        if precisa_sync:
            with st.spinner("Sincronizando dados do banco..."):
                sync_mysql_to_sqlite()
                novo_sync = datetime.now().isoformat()
                atualizar_usuario_campo(id_usuario, "ultimo_sync", novo_sync)
                st.session_state["usuario"]["ultimo_sync"] = novo_sync
                st.success("Dados atualizados automaticamente!")
        else:
            st.info(f"Última sincronização: {ultimo_sync_str}")

        # Botão manual
        if st.button("🔄 Sincronizar agora"):
            with st.spinner("Sincronizando dados do banco..."):
                sync_mysql_to_sqlite()
                novo_sync = datetime.now().isoformat()
                atualizar_usuario_campo(id_usuario, "ultimo_sync", novo_sync)
                st.session_state["usuario"]["ultimo_sync"] = novo_sync
                st.success("Dados atualizados manualmente!")

        # Diagnóstico: tabelas no SQLite
        try:
            conn_debug = sqlite3.connect(sqlite_path)
            tabelas = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn_debug)
            st.sidebar.subheader("📚 Tabelas no banco local:")
            st.sidebar.write(tabelas)
            conn_debug.close()
            if os.path.exists(sqlite_path):
                st.sidebar.success("📁 Banco sincronizado com sucesso!")
            else:
                st.sidebar.error("❌ Banco local SQLite não encontrado.")
        except Exception as e:
            st.sidebar.error(f"Erro ao acessar banco local: {e}")

        # Indicadores
        carregar_indicadores(sqlite_path)

        # Pergunta para IA
        st.subheader("Faça sua pergunta à IA")
        pergunta = st.text_input("Exemplo: Qual o produto mais produzido em abril de 2025?")
        if st.button("🧠 Consultar IA"):
            executar_pergunta(pergunta, sqlite_path)

        if st.sidebar.button("Sair"):
            st.session_state["logado"] = False
            st.session_state["pagina"] = "login"
            st.rerun()
