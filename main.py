import streamlit as st
import sqlite3
import os

# Banco de dados local
DB_PATH = "data/database.db"
os.makedirs("data", exist_ok=True)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Cria a tabela de usuários, se não existir
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


st.set_page_config(page_title="IA KPI - Cadastro", layout="centered")
st.title("📊 IA KPI - Cadastro de Acesso")

# Formulário de cadastro
with st.form("cadastro_form"):
    st.subheader("Cadastro de novo cliente")
    nome = st.text_input("Nome completo")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    st.markdown("---")
    st.subheader("Dados de conexão ao banco do cliente")
    host = st.text_input("Host do banco")
    porta = st.text_input("Porta", value="3306")
    usuario_banco = st.text_input("Usuário do banco")
    senha_banco = st.text_input("Senha do banco", type="password")
    schema = st.text_input("Schema (ex: dbview)")

    submitted = st.form_submit_button("Cadastrar")

    if submitted:
        if not (nome and email and senha and host and porta and usuario_banco and senha_banco and schema):
            st.error("Preencha todos os campos.")
        else:
            try:
                c.execute("INSERT INTO usuarios (nome, email, senha, host, porta, usuario_banco, senha_banco, schema) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          (nome, email, senha, host, porta, usuario_banco, senha_banco, schema))
                conn.commit()
                st.success("Cadastro realizado com sucesso! Agora você pode acessar o painel da IA.")
            except sqlite3.IntegrityError:
                st.error("Este email já está cadastrado.")
