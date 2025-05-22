import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, inspect
import requests
import streamlit as st

def gerar_descricao_ia(nome_tabela, nome_coluna, tipo_dado, valor_exemplo):
    prompt = f"""
Você é um assistente de dados. Gere uma descrição simples e útil para um campo de banco de dados baseado nas seguintes informações:

- Tabela: {nome_tabela}
- Coluna: {nome_coluna}
- Tipo de dado: {tipo_dado}
- Exemplo de valor: {valor_exemplo}

Responda com uma frase curta que explique o que essa coluna representa.
"""
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "mistral",
                "messages": [
                    {"role": "system", "content": "Você é um assistente de BI."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }
        )
        if response.status_code == 200:
            return response.json()["message"]["content"].strip()
        else:
            return "Descrição não gerada (erro IA)"
    except:
        return "Erro ao conectar IA local"

def mapear_estrutura_banco(mysql_host, mysql_port, mysql_user, mysql_password, mysql_database):
    try:
        mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
        mysql_engine = create_engine(mysql_uri)
        inspector = inspect(mysql_engine)

        # Conecta ao SQLite local
        sqlite_path = "data/database.db"
        conn_sqlite = sqlite3.connect(sqlite_path)
        cursor = conn_sqlite.cursor()

        tabelas = inspector.get_table_names(schema=mysql_database)
        views = inspector.get_view_names(schema=mysql_database)
        todas = tabelas + views

        for tabela in todas:
            colunas = inspector.get_columns(tabela, schema=mysql_database)

            for col in colunas:
                nome_coluna = col["name"]
                tipo_dado = str(col["type"])

                # Tenta pegar um exemplo de valor da coluna
                exemplo_valor = ""
                try:
                    df_exemplo = pd.read_sql(f"SELECT `{nome_coluna}` FROM `{mysql_database}`.`{tabela}` WHERE `{nome_coluna}` IS NOT NULL LIMIT 1", mysql_engine)
                    if not df_exemplo.empty:
                        exemplo_valor = str(df_exemplo.iloc[0][0])
                except:
                    exemplo_valor = ""

                # Gera descrição com IA
                descricao = gerar_descricao_ia(tabela, nome_coluna, tipo_dado, exemplo_valor)

                # Insere no SQLite
                cursor.execute("""
                    INSERT INTO estrutura_dinamica (sistema_id, nome_tabela, nome_coluna, tipo_dado, valor_exemplo, descricao_gerada)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    mysql_database,
                    tabela,
                    nome_coluna,
                    tipo_dado,
                    exemplo_valor,
                    descricao
                ))
                conn_sqlite.commit()

        conn_sqlite.close()
        print("✅ Estrutura mapeada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao mapear estrutura: {e}")
def iniciar_mapeamento_via_streamlit():
    mysql_host = st.session_state.get("mysql_host")
    mysql_port = st.session_state.get("mysql_port")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")

    mapear_estrutura_banco(mysql_host, mysql_port, mysql_user, mysql_password, mysql_database)