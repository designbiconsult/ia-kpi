import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, inspect
import streamlit as st
import requests

# Função para gerar a descrição automática de uma coluna usando a IA (OpenRouter)
def gerar_descricao_ia(tabela, coluna, tipo, exemplo):
    OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "SUA_CHAVE_AQUI")
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "meta-llama/llama-3.3-70b-instruct:free"  # ou o modelo que preferir

    prompt = (
        f"Explique brevemente o que representa a coluna '{coluna}' da tabela '{tabela}', "
        f"do tipo '{tipo}'. Exemplo de valor: '{exemplo}'. Seja direto e útil para leigos."
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 120,
        "temperature": 0.1
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=25)
        response.raise_for_status()
        desc = response.json()["choices"][0]["message"]["content"]
        return desc.strip()
    except Exception as e:
        return f"Coluna '{coluna}' da tabela '{tabela}'. Tipo: {tipo}. Exemplo: {exemplo}"

# --- Função principal de sincronização
def sync_mysql_to_sqlite():
    mysql_host = st.session_state.get("mysql_host")
    mysql_port = st.session_state.get("mysql_port")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")
    output_sqlite_path = st.session_state.get("sqlite_path", "data/cliente_dados.db")

    if not all([mysql_host, mysql_port, mysql_user, mysql_password, mysql_database]):
        st.error("Credenciais incompletas. Verifique a conexão antes de sincronizar.")
        return

    mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
    mysql_engine = create_engine(mysql_uri)
    inspector = inspect(mysql_engine)

    os.makedirs(os.path.dirname(output_sqlite_path), exist_ok=True)
    with sqlite3.connect(output_sqlite_path, timeout=60) as sqlite_conn:
        try:
            views = inspector.get_view_names(schema=mysql_database)
            tables = inspector.get_table_names(schema=mysql_database)
            entidades = views + tables

            for entidade in entidades:
                # Carrega do MySQL e salva no SQLite
                df = pd.read_sql(f"SELECT * FROM `{mysql_database}`.`{entidade}`", mysql_engine)
                df.to_sql(entidade, con=sqlite_conn, if_exists="replace", index=False)
            # Gera estrutura dinâmica detalhada
            salvar_estrutura_dinamica(entidades, sqlite_conn)
            st.success("✅ Sincronização concluída com sucesso.")

        except Exception as e:
            st.error(f"❌ Erro ao sincronizar: {e}")
        finally:
            mysql_engine.dispose()

def salvar_estrutura_dinamica(tabelas, conn_sqlite):
    """
    Cria e preenche a tabela estrutura_dinamica com as tabelas e colunas do SQLite,
    incluindo descrição automática por IA.
    """
    cursor = conn_sqlite.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estrutura_dinamica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tabela TEXT,
            coluna TEXT,
            tipo TEXT,
            exemplo TEXT,
            descricao TEXT
        )
    ''')
    conn_sqlite.commit()
    cursor.execute("DELETE FROM estrutura_dinamica")  # Limpa antes de popular novamente

    for tabela in tabelas:
        try:
            df = pd.read_sql(f"SELECT * FROM {tabela} LIMIT 1", conn_sqlite)
            for coluna in df.columns:
                exemplo = str(df[coluna].iloc[0]) if not df.empty else ""
                tipo = str(df[coluna].dtype)
                descricao = gerar_descricao_ia(tabela, coluna, tipo, exemplo)
                cursor.execute('''
                    INSERT INTO estrutura_dinamica (tabela, coluna, tipo, exemplo, descricao)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tabela, coluna, tipo, exemplo, descricao))
        except Exception as e:
            print(f"Erro ao processar tabela {tabela}: {e}")

    conn_sqlite.commit()
    cursor.close()
