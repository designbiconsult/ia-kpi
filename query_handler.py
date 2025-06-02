import requests
import streamlit as st
import sqlite3
import pandas as pd
import json

USE_LOCAL_OLLAMA = True  # True = IA local (Ollama), False = OpenRouter

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3"

OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "sua_chave_aqui")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

def carregar_estrutura_dinamica(sqlite_path):
    try:
        with sqlite3.connect(sqlite_path) as conn:
            df = pd.read_sql("SELECT tabela, coluna, tipo, descricao FROM estrutura_dinamica", conn)
        if df.empty:
            return None, "Tabela estrutura_dinamica está vazia."
        estrutura_txt = ""
        for row in df.itertuples():
            estrutura_txt += f"Tabela: {row.tabela}, Coluna: {row.coluna}, Tipo: {row.tipo}, Descrição: {row.descricao}\n"
        return estrutura_txt, None
    except Exception as e:
        return None, f"Erro ao ler estrutura_dinamica: {e}"

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")

    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    estrutura, erro_estrutura = carregar_estrutura_dinamica(sqlite_path)
    if not estrutura:
        st.error(f"Estrutura dinâmica não carregada. {erro_estrutura or ''}\nTente sincronizar as tabelas primeiro.")
        return

    prompt_base = (
        "Você é um assistente de análise de dados. Responda SEMPRE com base apenas nas tabelas e colunas fornecidas abaixo.\n"
        "Não invente nomes de tabelas ou colunas. Use sempre os nomes exatos. Se precisar montar uma consulta SQL, use os nomes informados.\n"
        "Ao final, exiba o SQL gerado e responda o resultado da consulta (explique o que a consulta retorna).\n"
        "Estrutura do banco:\n"
        f"{estrutura}"
    )

    messages = [
        {"role": "system", "content": prompt_base},
        {"role": "user", "content": pergunta}
    ]

    try:
        if USE_LOCAL_OLLAMA:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False
                },
                timeout=5000
            )
            if response.status_code == 200:
                content = response.json()
                ia_response = content.get("message", {}).get("content", "")
                st.write("**SQL sugerido pela IA:**")
                linhas = ia_response.splitlines()
                sql_block = ""
                in_sql = False
                for l in linhas:
                    if l.strip().upper().startswith("SELECT"):
                        in_sql = True
                    if in_sql:
                        sql_block += l + "\n"
                    if l.strip() == "" and in_sql:
                        break
                if sql_block:
                    st.code(sql_block.strip(), language="sql")
                st.success(ia_response)
            else:
                st.error(f"Erro ao acessar IA local: {response.text}")
        else:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            body = {
                "model": OPENROUTER_MODEL,
                "messages": messages,
                "max_tokens": 800,
                "temperature": 0.2
            }
            response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=5000)
            response.raise_for_status()
            result = response.json()
            ia_response = result["choices"][0]["message"]["content"]
            st.write("**SQL sugerido pela IA:**")
            linhas = ia_response.splitlines()
            sql_block = ""
            in_sql = False
            for l in linhas:
                if l.strip().upper().startswith("SELECT"):
                    in_sql = True
                if in_sql:
                    sql_block += l + "\n"
                if l.strip() == "" and in_sql:
                    break
            if sql_block:
                st.code(sql_block.strip(), language="sql")
            st.success(ia_response)
    except Exception as e:
        st.error(f"Erro ao acessar IA local: {e}")
        st.exception(e)
