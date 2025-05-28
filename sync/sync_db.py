import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, inspect
import streamlit as st

def listar_tabelas_mysql():
    # Retorna listas de nomes de tabelas/views e tipos
    mysql_host = st.session_state.get("mysql_host")
    mysql_port = st.session_state.get("mysql_port")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")
    if not all([mysql_host, mysql_port, mysql_user, mysql_password, mysql_database]):
        st.error("Credenciais incompletas para listar tabelas/views.")
        return [], []

    mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
    mysql_engine = create_engine(mysql_uri)
    inspector = inspect(mysql_engine)

    views = inspector.get_view_names(schema=mysql_database)
    tables = inspector.get_table_names(schema=mysql_database)
    tipos = ["view"] * len(views) + ["tabela"] * len(tables)
    return views + tables, tipos

def atualizar_tabelas_sincronizadas(usuario_id, selecionadas, tipos_mysql):
    with sqlite3.connect("data/database.db", timeout=10) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM tabelas_sincronizadas WHERE usuario_id = ?", (usuario_id,))
        for nome in selecionadas:
            tipo = "view" if "VW_" in nome.upper() else "tabela"
            c.execute("INSERT INTO tabelas_sincronizadas (usuario_id, nome_tabela, tipo, ultima_sync) VALUES (?, ?, ?, ?)",
                      (usuario_id, nome, tipo, None))
        conn.commit()

def sync_mysql_to_sqlite(tabelas_sync):
    # Recebe uma lista de (nome_tabela, tipo) vindos do dashboard
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

    os.makedirs(os.path.dirname(output_sqlite_path), exist_ok=True)
    with sqlite3.connect(output_sqlite_path, timeout=30) as sqlite_conn:
        for (nome_tabela, tipo) in tabelas_sync:
            try:
                df = pd.read_sql(f"SELECT * FROM `{mysql_database}`.`{nome_tabela}`", mysql_engine)
                df.to_sql(nome_tabela, con=sqlite_conn, if_exists="replace", index=False)
            except Exception as e:
                st.warning(f"Erro ao sincronizar {nome_tabela}: {e}")

    mysql_engine.dispose()
