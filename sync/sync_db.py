import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, inspect

def sync_mysql_to_sqlite():
    import streamlit as st
    mysql_host = st.session_state.get("mysql_host")
    mysql_port = st.session_state.get("mysql_port")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")
    output_sqlite_path = st.session_state.get("sqlite_path", "data/cliente_dados.db")

    if not all([mysql_host, mysql_port, mysql_user, mysql_password, mysql_database]):
        return False, "Credenciais incompletas. Verifique a conexão antes de sincronizar."

    try:
        mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
        mysql_engine = create_engine(mysql_uri)
        inspector = inspect(mysql_engine)
        os.makedirs(os.path.dirname(output_sqlite_path), exist_ok=True)

        with sqlite3.connect(output_sqlite_path, timeout=30) as sqlite_conn:
            views = inspector.get_view_names(schema=mysql_database)
            tables = inspector.get_table_names(schema=mysql_database)
            entidades = views + tables

            for entidade in entidades:
                df = pd.read_sql(f"SELECT * FROM `{mysql_database}`.`{entidade}`", mysql_engine)
                df.to_sql(entidade, con=sqlite_conn, if_exists="replace", index=False)

            salvar_estrutura_dinamica(entidades, sqlite_conn)

        mysql_engine.dispose()
        return True, ""

    except Exception as e:
        return False, str(e)

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
                descricao = f"Coluna da tabela {tabela} chamada {coluna}, tipo {tipo}"
                cursor.execute('''
                    INSERT INTO estrutura_dinamica (tabela, coluna, tipo, exemplo, descricao)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tabela, coluna, tipo, exemplo, descricao))
        except Exception:
            pass
    conn_sqlite.commit()
    cursor.close()
