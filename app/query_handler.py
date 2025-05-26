import requests
import streamlit as st
import sqlite3

OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.3-70b-instruct:free"

def carregar_estrutura(sqlite_path):
    try:
        with sqlite3.connect(sqlite_path) as conn:
            df = pd.read_sql("SELECT tabela, coluna, tipo, exemplo, descricao FROM estrutura_dinamica", conn)
        return df
    except Exception as e:
        return None

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")
    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    estrutura_df = carregar_estrutura(sqlite_path)
    estrutura_contexto = ""
    if estrutura_df is not None:
        estrutura_contexto = "\n".join([
            f"[{row['tabela']}] {row['coluna']} ({row['tipo']} | exemplo: {row['exemplo']}): {row['descricao']}"
            for _, row in estrutura_df.iterrows()
        ])
    else:
        st.warning("Estrutura dinâmica não carregada. A resposta pode ser limitada.")

    messages = [
        {"role": "system", "content":
            f"""
            Você é um assistente de BI para empresas. Abaixo está a estrutura do banco, use-a para responder perguntas consultando os dados conforme necessário.
            Estrutura:
            {estrutura_contexto}
            Ao gerar a resposta, sempre mostre os resultados da consulta de forma amigável ao gestor, com tabelas, cartões ou gráficos, nunca apenas o SQL. Pergunte ao usuário se prefere análise sintética (resumida) ou analítica (detalhada) se a pergunta for ambígua.
            """},
        {"role": "user", "content": pergunta},
    ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 1200,
        "temperature": 0.15
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        resposta = response.json()["choices"][0]["message"]["content"]
        st.success(resposta)
    except Exception as e:
        st.error(f"Erro ao acessar o OpenRouter: {e}")
        st.exception(e)
