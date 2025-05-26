import requests
import streamlit as st
import sqlite3
import pandas as pd
import re

# Chave e modelo do OpenRouter
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "SUA_CHAVE_AQUI")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.3-70b-instruct:free"

def get_estrutura_context(sqlite_path):
    contexto = []
    try:
        with sqlite3.connect(sqlite_path, timeout=10) as conn:
            df = pd.read_sql("SELECT tabela, coluna, tipo, descricao FROM estrutura_dinamica LIMIT 100", conn)
            for _, row in df.iterrows():
                contexto.append(f"Tabela: {row['tabela']} | Coluna: {row['coluna']} | Tipo: {row['tipo']} | Descrição: {row['descricao']}")
    except Exception as e:
        contexto = ["Contexto do banco não disponível."]
    return "\n".join(contexto)

def extrair_sql(texto):
    # Regex para encontrar o primeiro bloco de código SQL
    padrao = r"(?s)```sql(.*?)```"
    match = re.search(padrao, texto)
    if match:
        return match.group(1).strip()
    # Tenta encontrar SELECT ... ; mesmo sem bloco
    padrao2 = r"(SELECT[\s\S]+?;)"
    match2 = re.search(padrao2, texto, re.IGNORECASE)
    if match2:
        return match2.group(1).strip()
    return None

def detectar_visual(texto):
    texto = texto.lower()
    if "cartão" in texto or "metric" in texto:
        return "card"
    if "gráfico" in texto or "grafico" in texto or "plot" in texto:
        return "chart"
    if "tabela" in texto or "dataframe" in texto:
        return "table"
    return "auto"

def perguntar_ia_com_sql(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")
    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    estrutura_contexto = get_estrutura_context(sqlite_path)

    messages = [
        {"role": "system", "content": (
            "Você é um assistente inteligente conectado a um banco SQLite."
            "Use apenas as tabelas/colunas abaixo para responder perguntas sobre os dados empresariais. "
            "Responda de forma simples e visual. "
            "NUNCA peça ao usuário para informar nomes de tabelas/colunas."
            "Caso precise, refine perguntando apenas sobre o NEGÓCIO, nunca sobre estrutura técnica."
            "Estrutura do banco:\n"
            f"{estrutura_contexto}"
        )},
        {"role": "user", "content": pergunta},
        {"role": "system", "content": (
            "Retorne o SQL necessário para obter o resultado (coloque entre ```sql e ```). "
            "Descreva também o melhor formato visual (tabela, cartão, gráfico, etc). "
            "Depois do SQL, explique o resultado ao usuário."
        )},
    ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 1400,
        "temperature": 0.2
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        resp_json = response.json()
        resposta = resp_json["choices"][0]["message"]["content"]

        # 1. Tenta extrair o SQL da resposta
        sql = extrair_sql(resposta)
        visual = detectar_visual(resposta)

        if sql:
            try:
                with sqlite3.connect(sqlite_path, timeout=15) as conn:
                    df = pd.read_sql(sql, conn)
                if df.empty:
                    st.warning("Nenhum resultado encontrado para esta consulta.")
                else:
                    # Visual sugerido
                    if visual == "card" and df.shape[1] >= 2:
                        st.metric(f"{df.columns[0]}", str(df.iloc[0, 0]))
                        st.metric(f"{df.columns[1]}", str(df.iloc[0, 1]))
                    elif visual == "chart" and df.shape[1] >= 2:
                        st.bar_chart(df.set_index(df.columns[0]))
                    else:
                        st.dataframe(df)
                st.info("Consulta SQL executada com sucesso!")
            except Exception as e:
                st.error(f"Erro ao executar SQL gerado: {e}")
        else:
            # Mostra resposta textual da IA caso não tenha SQL
            st.success(resposta)
    except Exception as e:
        st.error(f"Erro ao acessar o OpenRouter: {e}")
        st.exception(e)
