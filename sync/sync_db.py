# sync_db.py
from sqlalchemy import create_engine, inspect
import pandas as pd
import sqlite3
import streamlit as st

def obter_lista_tabelas_views_remotas():
    # Usa variáveis do session_state
    mysql_host = st.session_state.get("mysql_host")
    mysql_port = st.session_state.get("mysql_port")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")
    try:
        mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
        mysql_engine = create_engine(mysql_uri)
        inspector = inspect(mysql_engine)
        tabelas = inspector.get_table_names(schema=mysql_database)
        views = inspector.get_view_names(schema=mysql_database)
        return tabelas + views
    except Exception as e:
        st.error(f"Erro ao buscar tabelas remotas: {e}")
        return []

def sync_mysql_to_sqlite(tabelas_sync):
    mysql_host = st.session_state.get("mysql_host")
    mysql_port = st.session_state.get("mysql_port")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")
    output_sqlite_path = st.session_state.get("sqlite_path", "data/cliente_dados.db")

    try:
        mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
        mysql_engine = create_engine(mysql_uri)
        os.makedirs(os.path.dirname(output_sqlite_path), exist_ok=True)
        with sqlite3.connect(output_sqlite_path, timeout=30) as sqlite_conn:
            for entidade in tabelas_sync:
                st.write(f"🔄 Sincronizando: {entidade}")
                df = pd.read_sql(f"SELECT * FROM `{mysql_database}`.`{entidade}`", mysql_engine)
                df.to_sql(entidade, con=sqlite_conn, if_exists="replace", index=False)
        st.success("✅ Sincronização concluída com sucesso.")
    except Exception as e:
        st.error(f"❌ Erro ao sincronizar: {e}")
