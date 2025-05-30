import requests
import sqlite3
import streamlit as st
import pandas as pd
import json

# Configuração para IA local ou OpenRouter (ajuste conforme necessário)
USE_LOCAL_IA = True
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3"

def carregar_estrutura(sqlite_path):
    try:
        with sqlite3.connect(sqlite_path) as conn:
            df = pd.read_sql("SELECT nome_tabela, nome_coluna, tipo_dado, valor_exemplo, descricao_gerada FROM estrutura_dinamica", conn)
        if df.empty:
            return None
        estrutura = {}
        for _, row in df.iterrows():
            tabela = row['nome_tabela']
            coluna = row['nome_coluna']
            tipo = row['tipo_dado']
            exemplo = row['valor_exemplo']
            desc = row['descricao_gerada']
            if tabela not in estrutura:
                estrutura[tabela] = []
            estrutura[tabela].append({
                "coluna": coluna,
                "tipo": tipo,
                "exemplo": exemplo,
                "descricao": desc
            })
        return estrutura
    except Exception as e:
        st.warning(f"Estrutura dinâmica não carregada. A resposta pode ser limitada. Erro: {e}")
        return None

def montar_prompt_sql(pergunta, estrutura):
    prompt = "Você é um assistente de BI. Gere apenas uma query SQL para a pergunta do usuário, usando EXCLUSIVAMENTE as tabelas e colunas listadas abaixo. Não explique, apenas gere o SQL.\n"
    if estrutura:
        prompt += "Estrutura do banco:\n"
        for tabela, colunas in estrutura.items():
            prompt += f"- {tabela} ("
            prompt += ", ".join([c['coluna'] for c in colunas])
            prompt += ")\n"
    else:
        prompt += "Estrutura dinâmica não carregada.\n"
    prompt += f"Pergunta: {pergunta}\nApenas a SQL, sem mais nada."
    return prompt

def montar_prompt_resposta(resultado_df, pergunta):
    prompt = (
        "Você é um assistente de BI. O usuário fez a pergunta: "
        f"'{pergunta}'."
        "\nAqui estão os dados encontrados no banco (em formato de tabela):\n"
    )
    prompt += resultado_df.to_markdown(index=False)
    prompt += (
        "\nGere uma resposta clara e resumida, explique o resultado, e se for relevante, apresente em formato de tabela ou resumo visual. Responda em português."
    )
    return prompt

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")

    estrutura = carregar_estrutura(sqlite_path)
    if not estrutura:
        st.warning("Estrutura dinâmica não carregada. Tente sincronizar as tabelas primeiro.")
        return

    # 1. Gera a consulta SQL usando a IA
    prompt_sql = montar_prompt_sql(pergunta, estrutura)
    if USE_LOCAL_IA:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt_sql}],
                "stream": False
            },
            timeout=5000
        )
        resposta_ia = response.json()['message']['content']
    else:
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        body = {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [{"role": "user", "content": prompt_sql}],
            "max_tokens": 900,
            "temperature": 0.2
        }
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=90)
        resposta_ia = response.json()["choices"][0]["message"]["content"]

    # Extrai apenas o SQL da resposta da IA
    import re
    sql_matches = re.findall(r"(?i)select[\s\S]+", resposta_ia)
    if not sql_matches:
        st.error("A IA não conseguiu gerar uma consulta SQL válida para esta pergunta.")
        st.info(f"Resposta da IA:\n{resposta_ia}")
        return

    sql_query = sql_matches[0].split(';')[0]  # Pega só a primeira query
    st.code(sql_query, language='sql')

    # 2. Executa a consulta SQL no SQLite e mostra o resultado
    try:
        with sqlite3.connect(sqlite_path) as conn:
            resultado_df = pd.read_sql(sql_query, conn)
        if resultado_df.empty:
            st.info("Nenhum resultado encontrado para esta consulta.")
            return
        st.dataframe(resultado_df)
    except Exception as e:
        st.error(f"Erro ao executar SQL gerado: {e}")
        return

    # 3. Manda o resultado para a IA resumir para o usuário
    prompt_resposta = montar_prompt_resposta(resultado_df, pergunta)
    if USE_LOCAL_IA:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt_resposta}],
                "stream": False
            },
            timeout=5000
        )
        resposta_final = response.json()['message']['content']
    else:
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        body = {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [{"role": "user", "content": prompt_resposta}],
            "max_tokens": 900,
            "temperature": 0.2
        }
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=90)
        resposta_final = response.json()["choices"][0]["message"]["content"]

    st.success(resposta_final)
