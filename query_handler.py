import requests
import streamlit as st
import sqlite3
import pandas as pd

# Recomendado: use st.secrets para a chave
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.3-70b-instruct:free"

def get_estrutura_para_prompt(sqlite_path):
    try:
        with sqlite3.connect(sqlite_path) as conn:
            df = pd.read_sql("SELECT tabela, coluna, tipo FROM estrutura_dinamica", conn)
            estrutura = ""
            for tab, grp in df.groupby("tabela"):
                cols = ", ".join(f"{row.coluna} ({row.tipo})" for idx, row in grp.iterrows())
                estrutura += f"Tabela {tab}: {cols}\n"
        return estrutura
    except Exception:
        return ""

def perguntar_ia_com_sql(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")
    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    estrutura = get_estrutura_para_prompt(sqlite_path)
    if not estrutura:
        st.error("Estrutura do banco não encontrada. Sincronize os dados primeiro!")
        return

    # 1º passo: pede o SQL para a IA
    messages_sql = [
        {"role": "system", "content": (
            f"Você é um assistente para análise de dados empresariais. "
            f"Baseie sua resposta SOMENTE nas tabelas e colunas abaixo (do SQLite):\n{estrutura}\n"
            f"Dada a pergunta do usuário, devolva SOMENTE a consulta SQL que retorna o resultado correto. "
            f"NÃO EXPLIQUE, NÃO COLOQUE ``` OU NENHUMA PALAVRA EXTRA. "
            f"Se precisar perguntar algo para refinar a pergunta, peça ao usuário."
        )},
        {"role": "user", "content": pergunta},
    ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body_sql = {
        "model": MODEL,
        "messages": messages_sql,
        "max_tokens": 400,
        "temperature": 0.1
    }

    try:
        r = requests.post(OPENROUTER_API_URL, headers=headers, json=body_sql, timeout=60)
        r.raise_for_status()
        sql_gerado = r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        st.error(f"Erro ao gerar SQL: {e}")
        st.stop()

    # 2º passo: executa SQL
    try:
        with sqlite3.connect(sqlite_path) as conn:
            df = pd.read_sql(sql_gerado, conn)
    except Exception as e:
        st.error(f"Erro ao executar SQL gerado: {e}\nSQL: {sql_gerado}")
        st.stop()

    if df.empty:
        st.info("Nenhum dado encontrado para sua consulta.")
        return

    # 3º passo: pede para a IA como exibir o resultado (visualização)
    colunas = ", ".join(df.columns)
    linhas = df.head(5).to_dict(orient="records")
    prompt_visual = (
        "Recebeu a seguinte tabela como resultado da consulta SQL. "
        f"As colunas são: {colunas}. Aqui estão as primeiras linhas:\n{linhas}\n"
        "Sugira qual a MELHOR visualização (gráfico de barras, tabela, indicador, etc) e forneça o texto explicativo para o usuário. "
        "Responda em português, explique de forma clara e curta para gestores."
    )

    messages_visual = [
        {"role": "system", "content": "Você é um especialista em BI e storytelling visual para dados de empresas."},
        {"role": "user", "content": prompt_visual},
    ]

    body_visual = {
        "model": MODEL,
        "messages": messages_visual,
        "max_tokens": 400,
        "temperature": 0.1
    }

    try:
        r = requests.post(OPENROUTER_API_URL, headers=headers, json=body_visual, timeout=60)
        r.raise_for_status()
        resposta_visual = r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        resposta_visual = "Resultado encontrado. Segue abaixo a tabela de dados."

    # Exibe o resultado
    st.markdown("##### Visualização sugerida pela IA:")
    st.info(resposta_visual)
    st.dataframe(df)
