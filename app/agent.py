import sqlite3
import pandas as pd
import streamlit as st
import requests
from sqlalchemy import create_engine, inspect

def run_agent(pergunta: str, sqlite_path: str):
    """
    Lê o schema do banco SQLite local e monta o prompt para a IA gerar a consulta SQL.
    NÃO sincroniza nada aqui!
    """
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    inspector = inspect(sqlite_engine)
    todas = inspector.get_table_names()

    explicacoes = {
        "VW_CTO_PRODUTO": "Cadastro completo dos produtos da empresa. Contém: código interno, nome, descrição, NCM, tipo (acabado, matéria-prima), origem, cor, tamanho, código de barras e código de produto com defeito.",
        "VW_CTO_ORDEM_PRODUCAO": "Cabeçalho das ordens de produção. Inclui empresa, número da OP, data de emissão, status e prestador.",
        "VW_CTO_ORDEM_PRODUCAO_ITEM": "Itens associados às ordens de produção. Informa o produto, quantidade produzida, data da produção e vínculo com a OP."
    }

    schema_description = ""
    for nome in todas:
        columns = inspector.get_columns(nome)
        colnames = ", ".join(col["name"] for col in columns)
        descricao = explicacoes.get(nome, "Sem descrição detalhada.")
        schema_description += f"- {nome}: {descricao}. Colunas principais: {colnames}\n"

    prompt = f"""
Você é um assistente de BI. O usuário fará perguntas sobre os dados do banco.
Responda com uma **consulta SQL compatível com SQLite**, usando somente as views e colunas listadas abaixo.
Não invente nomes. Responda somente com o SQL entre um bloco ```sql e ```.

Objetos disponíveis:
{schema_description}

Pergunta: {pergunta}
"""

    # Chame o modelo (OpenRouter ou outro) para gerar o SQL
    from app.query_handler import OPENROUTER_API_KEY
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "meta-llama/llama-3.3-70b-instruct:free"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Você é um assistente de BI que responde com SQL."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 600,
        "temperature": 0.2
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        sql_code = content.split("```sql")[-1].replace("```", "").strip()
        return sqlite_engine, sql_code
    except Exception as e:
        st.error(f"Erro ao acessar o OpenRouter: {e}")
        return None
