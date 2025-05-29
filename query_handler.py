import requests
import streamlit as st
import sqlite3
import pandas as pd

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "mistral"

def obter_estrutura_dinamica(sqlite_path):
    try:
        with sqlite3.connect(sqlite_path) as conn:
            df = pd.read_sql("SELECT tabela, coluna, tipo, exemplo, descricao FROM estrutura_dinamica", conn)
            estrutura = []
            for _, row in df.iterrows():
                estrutura.append(
                    f"Tabela: {row['tabela']}, Coluna: {row['coluna']} ({row['tipo']}), Exemplo: {row['exemplo']}, Descrição: {row['descricao']}"
                )
            return "\n".join(estrutura)
    except Exception as e:
        return "Estrutura dinâmica não carregada."

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")
    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    estrutura_tabelas = obter_estrutura_dinamica(sqlite_path)
    contexto_regras = f"""
REGRAS DE MAPEAMENTO SEMÂNTICO:
- "produto vendido": use tabelas de pedido.
- "produto faturado": use tabelas de nota fiscal de saída.
- "produto comprado": use tabelas de compra/nota de entrada.
- "maior atraso": analise datas de compra e recebimento.

Estrutura das tabelas disponíveis:
{estrutura_tabelas}
"""
    prompt = contexto_regras + "\nPergunta do usuário: " + pergunta

    body = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": contexto_regras},
            {"role": "user", "content": pergunta}
        ],
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=body, timeout=500)
        response.raise_for_status()
        resposta = response.json()["message"]["content"]
        st.code(response.json(), language="json")  # DEBUG VISUAL DO RETORNO BRUTO
        st.success(resposta)
    except Exception as e:
        st.error(f"Erro ao acessar IA local: {e}")
        st.exception(e)
