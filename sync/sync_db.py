import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, inspect

def mapear_estrutura_banco(mysql_host, mysql_port, mysql_user, mysql_password, mysql_database):
    try:
        mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
        mysql_engine = create_engine(mysql_uri)
        inspector = inspect(mysql_engine)

        # Conecta ao SQLite local
        sqlite_path = "data/database.db"
        conn_sqlite = sqlite3.connect(sqlite_path)
        cursor = conn_sqlite.cursor()

        # Cria a tabela de estrutura se não existir
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

        tabelas = inspector.get_table_names(schema=mysql_database)
        views = inspector.get_view_names(schema=mysql_database)
        todas = tabelas + views

        for tabela in todas:
            colunas = inspector.get_columns(tabela, schema=mysql_database)
            for col in colunas:
                nome_coluna = col["name"]
                tipo_dado = str(col["type"])
                # Exemplo de valor
                exemplo_valor = ""
                try:
                    df_exemplo = pd.read_sql(f"SELECT `{nome_coluna}` FROM `{mysql_database}`.`{tabela}` WHERE `{nome_coluna}` IS NOT NULL LIMIT 1", mysql_engine)
                    if not df_exemplo.empty:
                        exemplo_valor = str(df_exemplo.iloc[0][0])
                except:
                    exemplo_valor = ""

                # Descrição gerada LOCALMENTE (sem IA!)
                descricao = f"Coluna '{nome_coluna}' da tabela '{tabela}'. Tipo: {tipo_dado}. Exemplo: {exemplo_valor}"

                # Insere na estrutura_dinamica
                cursor.execute("""
                    INSERT INTO estrutura_dinamica (tabela, coluna, tipo, exemplo, descricao)
                    VALUES (?, ?, ?, ?, ?)
                """, (tabela, nome_coluna, tipo_dado, exemplo_valor, descricao))
        conn_sqlite.commit()
        conn_sqlite.close()
        print("✅ Estrutura mapeada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao mapear estrutura: {e}")

def iniciar_mapeamento_via_streamlit():
    import streamlit as st
    mysql_host = st.session_state.get("mysql_host")
    mysql_port = st.session_state.get("mysql_port")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")

    mapear_estrutura_banco(mysql_host, mysql_port, mysql_user, mysql_password, mysql_database)
