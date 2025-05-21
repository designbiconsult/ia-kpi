import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, inspect
import streamlit as st

def sync_mysql_to_sqlite():
    """
    Sincroniza todas as views do schema especificado de um banco MySQL para um banco SQLite local,
    usando as credenciais fornecidas pelo usuário via Streamlit.
    """
    # Captura as credenciais via Streamlit
    mysql_host = st.session_state.get("mysql_host")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")
    output_sqlite_path = st.session_state.get("sqlite_path", "data/cliente_dados.db")

    try:
        mysql_port = int(st.session_state.get("mysql_port"))
    except (ValueError, TypeError):
        st.error("⚠️ A porta deve ser um número inteiro válido.")
        return

    if not all([mysql_host, mysql_port, mysql_user, mysql_password, mysql_database]):
        st.error("Credenciais incompletas. Verifique a conexão antes de sincronizar.")
        return

    mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
    mysql_engine = create_engine(mysql_uri)
    inspector = inspect(mysql_engine)

    os.makedirs(os.path.dirname(output_sqlite_path), exist_ok=True)
    sqlite_conn = sqlite3.connect(output_sqlite_path)

    try:
        views = inspector.get_view_names(schema=mysql_database)

        for view in views:
            st.write(f"🔄 Sincronizando view: {view}...")
            df = pd.read_sql(f"SELECT * FROM `{mysql_database}`.`{view}`", mysql_engine)
            df.to_sql(view, con=sqlite_conn, if_exists="replace", index=False)

        st.success("✅ Sincronização concluída com sucesso.")

    except Exception as e:
        st.error(f"❌ Erro ao sincronizar views: {e}")

    finally:
        sqlite_conn.close()
        mysql_engine.dispose()
