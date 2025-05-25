import requests
import streamlit as st
import sqlite3
import pandas as pd
import os

# Chave no secrets.toml ou variável de ambiente
OPENROUTER_API_KEY = (
    st.secrets.get("OPENROUTER_API_KEY") or
    os.environ.get("OPENROUTER_API_KEY") or
    "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"
)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "meta-llama/llama-3-70b-instruct:free"   # Gratuito, conforme docs!

def get_db_structure(sqlite_path):
    with sqlite3.connect(sqlite_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT tabela, coluna, tipo FROM estrutura_dinamica")
        estrutura = cursor.fetchall()
        estrutura_txt = ""
        for tabela, coluna, tipo in estrutura:
            estrutura_txt += f"Tabela: {tabela}, Coluna: {coluna}, Tipo: {tipo}\n"
    return estrutura_txt

def perguntar_ia_com_sql(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")

    # 1. Contexto do banco para IA
    estrutura_txt = get_db_structure(sqlite_path)
    system_prompt = (
        "Você é um assistente de BI. Seu trabalho é: "
        "1. Gerar a SQL correta para responder à pergunta do usuário, usando apenas as tabelas/colunas abaixo.\n"
        "2. NÃO EXPLIQUE a query, apenas escreva o SQL puro."
        "\nEstrutura do banco:\n" + estrutura_txt
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": pergunta}
    ]
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.2
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=45)
        response.raise_for_status()
        sql_query = response.json()["choices"][0]["message"]["content"].strip()
        st.code(sql_query, language="sql")
    except Exception as e:
        st.error(f"Erro ao gerar SQL: {e}")
        return

    # 3. Executa o SQL no banco local
    try:
        with sqlite3.connect(sqlite_path) as conn:
            resultado_df = pd.read_sql(sql_query, conn)
        st.write("Resultado da consulta:")
        st.dataframe(resultado_df)
    except Exception as e:
        st.error(f"Erro ao executar SQL: {e}")
        return

    # 4. Envia o resultado para a IA criar a resposta
    resumo_prompt = (
        "Com base neste resultado SQL, gere uma resposta clara e, se possível, sugira o melhor visual (cartão, tabela, gráfico):\n"
        f"{resultado_df.to_string(index=False)}\n"
        "Pergunta original: " + pergunta
    )
    messages = [
        {"role": "system", "content": "Você é um analista de BI que resume resultados de consulta."},
        {"role": "user", "content": resumo_prompt}
    ]
    body["messages"] = messages
    body["max_tokens"] = 400
    try:
        response2 = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=45)
        response2.raise_for_status()
        resposta = response2.json()["choices"][0]["message"]["content"].strip()
        st.success(resposta)
    except Exception as e:
        st.error(f"Erro ao resumir resultado: {e}")
