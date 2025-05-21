import os
import pandas as pd
from sqlalchemy import create_engine, inspect, text
import sqlite3
from langchain.chat_models import ChatOpenAI
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
import streamlit as st

def sync_mysql_to_sqlite_and_run_agent():
    # === CAPTURA AS CREDENCIAIS DA INTERFACE DO USUÁRIO ===
    mysql_host = st.session_state.get("mysql_host")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")
    sqlite_path = st.session_state.get("sqlite_path", "data/cliente_dados.db")

    try:
        mysql_port = int(st.session_state.get("mysql_port"))
    except (ValueError, TypeError):
        st.error("⚠️ Porta inválida.")
        return

    # === CONEXÃO COM O MYSQL
    mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
    mysql_engine = create_engine(mysql_uri)

    # === CONEXÃO COM O SQLITE LOCAL
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")

    # === SINCRONIZAÇÃO DAS VIEWS
    try:
        inspector = inspect(mysql_engine)
        views = inspector.get_view_names(schema=mysql_database)

        with sqlite_engine.begin() as conn_sqlite:
            for view in views:
                st.write(f"🔄 Sincronizando: {view}")
                df = pd.read_sql(f"SELECT * FROM `{mysql_database}`.`{view}`", mysql_engine)
                df.to_sql(view, conn_sqlite, if_exists="replace", index=False)

        st.success("✅ Views sincronizadas com sucesso.")
    except Exception as e:
        st.error(f"Erro ao sincronizar views: {e}")
        return

    # === GERA DESCRIÇÃO PARA IA
    inspector = inspect(sqlite_engine)
    schema_description = ""
    for view in inspector.get_table_names():
        columns = inspector.get_columns(view)
        colnames = ", ".join(col["name"] for col in columns)
        schema_description += f"- {view}: {colnames}\n"

    # === MONTA PROMPT
    initial_prompt = f"""
Você é um assistente de dados conectado a um banco SQLite.

Use exclusivamente os dados abaixo (views e colunas) para responder às perguntas.

NÃO invente dados. NÃO use conhecimento de mundo.
Se não houver dados suficientes, diga: "Não encontrei essa informação nos dados disponíveis."

Responda sempre com:
1. Explicação breve do que foi encontrado
2. Bloco SQL com a consulta usada

### Esquema disponível:
{schema_description}
"""

    # === PREPARA AGENTE IA
    db = SQLDatabase(engine=sqlite_engine)
    llm = ChatOpenAI(temperature=0, model="gpt-4")
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        agent_executor_kwargs={"prefix": initial_prompt}
    )

    return agent_executor
