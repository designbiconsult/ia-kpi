import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, inspect
import streamlit as st
import requests

def obter_descricao_coluna(nome_tabela, nome_coluna, tipo_coluna, exemplo):
    # Use a IA para descrever automaticamente a função da coluna
    prompt = (
        f"Explique resumidamente para um analista de BI o que representa a coluna '{nome_coluna}' (tipo: {tipo_coluna}, exemplo: {exemplo}) na tabela '{nome_tabela}'."
        " Seja claro e objetivo, considerando contexto de ERP/indústria."
    )
    try:
        api_key = st.secrets.get("OPENROUTER_API_KEY")
        model = "meta-llama/llama-3.3-70b-instruct:free"
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        messages = [{"role": "user", "content": prompt}]
        body = {"model": model, "messages": messages, "max_tokens": 80, "temperature": 0}
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return f"Coluna '{nome_coluna}' da tabela '{nome_tabela}', tipo {tipo_coluna}"

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
    with sqlite3.connect(output_sqlite_path, timeout=30) as sqlite_conn:
        try:
            views = inspector.get_view_names(schema=mysql_database)
            tables = inspector.get_table_names(schema=mysql_database)
            entidades = views + tables

            for entidade in entidades:
                df = pd.read_sql(f"SELECT * FROM `{mysql_database}`.`{entidade}`", mysql_engine)
                df.to_sql(entidade, con=sqlite_conn, if_exists="replace", index=False)

            salvar_estrutura_dinamica(entidades, sqlite_conn)
            st.success("✅ Sincronização concluída com sucesso.")
        except Exception as e:
            st.error(f"❌ Erro ao sincronizar: {e}")
        finally:
            mysql_engine.dispose()

def salvar_estrutura_dinamica(tabelas, conn_sqlite):
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

    for tabela in tabelas:
        try:
            df = pd.read_sql(f"SELECT * FROM {tabela} LIMIT 1", conn_sqlite)
            for coluna in df.columns:
                exemplo = str(df[coluna].iloc[0]) if not df.empty else ""
                tipo = str(df[coluna].dtype)
                descricao = obter_descricao_coluna(tabela, coluna, tipo, exemplo)
                cursor.execute('''
                    INSERT INTO estrutura_dinamica (tabela, coluna, tipo, exemplo, descricao)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tabela, coluna, tipo, exemplo, descricao))
        except Exception as e:
            print(f"Erro ao processar tabela {tabela}: {e}")

    conn_sqlite.commit()
    cursor.close()
