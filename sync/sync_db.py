import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, inspect
import streamlit as st

def sync_mysql_to_sqlite():
    """
    Sincroniza todas as views e tabelas do schema de um banco MySQL para um banco SQLite local,
    usando as credenciais fornecidas pelo usuário via Streamlit.
    """
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
    # Use 'with' para garantir fechamento correto
    with sqlite3.connect(output_sqlite_path, timeout=30) as sqlite_conn:
        try:
            views = inspector.get_view_names(schema=mysql_database)
            tables = inspector.get_table_names(schema=mysql_database)
            entidades = views + tables

            for entidade in entidades:
                st.write(f"🔄 Sincronizando: {entidade}")
                df = pd.read_sql(f"SELECT * FROM `{mysql_database}`.`{entidade}`", mysql_engine)
                df.to_sql(entidade, con=sqlite_conn, if_exists="replace", index=False)

            salvar_estrutura_dinamica(entidades, sqlite_conn)
            st.success("✅ Sincronização concluída com sucesso.")

        except Exception as e:
            st.error(f"❌ Erro ao sincronizar: {e}")
        finally:
            mysql_engine.dispose()

def salvar_estrutura_dinamica(tabelas, conn_sqlite):
    """
    Cria e preenche a tabela estrutura_dinamica com as tabelas e colunas do SQLite.
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
        except Exception as e:
            print(f"Erro ao processar tabela {tabela}: {e}")

    conn_sqlite.commit()
    cursor.close()
