import requests
import streamlit as st
import sqlite3
import pandas as pd

# IA LOCAL via Ollama
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3"

def get_estrutura_prompt(sqlite_path):
    try:
        with sqlite3.connect(sqlite_path) as conn:
            df = pd.read_sql("SELECT tabela, coluna, tipo, exemplo, descricao FROM estrutura_dinamica", conn)
        estrutura = ""
        for nome_tabela in df["tabela"].unique():
            colunas = df[df["tabela"] == nome_tabela]
            estrutura += f"\nTabela: {nome_tabela}\n"
            for _, row in colunas.iterrows():
                estrutura += f"  - {row['coluna']} ({row['tipo']}): {row['descricao']}\n"
        return estrutura
    except Exception as e:
        return "Estrutura dinâmica não carregada. A resposta pode ser limitada."

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")

    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    estrutura = get_estrutura_prompt(sqlite_path)

    prompt_system = (
        "Você é um assistente de BI. Responda apenas com base nas tabelas e colunas disponíveis abaixo:\n"
        f"{estrutura}\n"
        "Ao gerar SQL, use SOMENTE essas tabelas e colunas, nunca invente nomes. "
        "Se não houver dados suficientes, peça refinamento ao usuário. "
        "Depois de executar o SQL, retorne um resumo ou tabela clara e, se possível, sugira um formato visual (ex: tabela, gráfico de barras, cartão etc)."
    )

    messages = [
        {"role": "system", "content": prompt_system},
        {"role": "user", "content": pergunta},
    ]

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False
            },
            timeout=5000
        )
        response.raise_for_status()
        resposta = response.json()["message"]["content"]
        st.success(resposta)
        # Exibir o SQL extraído da resposta da IA, se quiser debug, pode extrair via regex ou analisar a resposta.
    except Exception as e:
        st.error(f"Erro ao acessar IA local: {e}")
        st.exception(e)
