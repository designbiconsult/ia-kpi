import os
import pandas as pd
import sqlite3
import requests
from sqlalchemy import create_engine, inspect
import streamlit as st

def sync_mysql_to_sqlite_and_run_agent(pergunta: str):
    mysql_host = st.session_state.get("mysql_host")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")
    sqlite_path = st.session_state.get("sqlite_path", "data/cliente_dados.db")

    try:
        mysql_port = int(st.session_state.get("mysql_port"))
    except (ValueError, TypeError):
        st.error("⚠️ Porta inválida.")
        return None

    mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
    mysql_engine = create_engine(mysql_uri)

    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")

    try:
        inspector = inspect(mysql_engine)
        views = inspector.get_view_names(schema=mysql_database)
        tables = inspector.get_table_names(schema=mysql_database)
        todas = views + tables

        with sqlite_engine.begin() as conn_sqlite:
            for nome in todas:
                st.write(f"🔄 Sincronizando: {nome}")
                df = pd.read_sql(f"SELECT * FROM `{mysql_database}`.`{nome}`", mysql_engine)
                df.to_sql(nome, conn_sqlite, if_exists="replace", index=False)

        st.success("✅ Views e tabelas sincronizadas com sucesso.")
    except Exception as e:
        st.error(f"Erro ao sincronizar dados: {e}")
        return None

    inspector = inspect(sqlite_engine)

    explicacoes = {
        "VW_CTO_PRODUTO": "Cadastro completo dos produtos da empresa. Contém: código interno, nome, descrição, NCM, tipo (acabado, matéria-prima), origem, cor, tamanho, código de barras e código de produto com defeito.",
        "VW_CTO_ORDEM_PRODUCAO": "Cabeçalho das ordens de produção. Inclui empresa, número da OP, data de emissão, status e prestador.",
        "VW_CTO_ORDEM_PRODUCAO_ITEM": "Itens associados às ordens de produção. Informa o produto, quantidade produzida, data da produção e vínculo com a OP."
    }

    schema_description = ""
    st.markdown("### 🔍 Objetos sincronizados:")
    for nome in todas:
        columns = inspector.get_columns(nome)
        colnames = ", ".join(col["name"] for col in columns)
        descricao = explicacoes.get(nome, "Sem descrição detalhada.")
        schema_description += f"- {nome}: {descricao}. Colunas principais: {colnames}\n"
        st.markdown(f"- `{nome}`")

    prompt = f"""
Você é um assistente de BI. O usuário fará perguntas sobre os dados do banco. 
Responda com uma **consulta SQL compatível com SQLite**, usando somente as views e colunas listadas abaixo.
Não invente nomes. Responda somente com o SQL entre um bloco ```sql e ```.

Objetos disponíveis:
{schema_description}

Pergunta: {pergunta}
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "mistral",
                "messages": [
                    {"role": "system", "content": "Você é um assistente de BI que responde com SQL."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            content = response.json()["message"]["content"].strip()
            sql_code = content.split("```sql")[-1].replace("```", "").strip()
            return sqlite_engine, sql_code
        else:
            st.error(f"Erro ao consultar o modelo: {response.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("⏱ Tempo de resposta excedido (timeout). O modelo demorou demais para responder.")
        return None
    except Exception as e:
        st.error(f"Erro ao acessar o Ollama: {e}")
        return None
