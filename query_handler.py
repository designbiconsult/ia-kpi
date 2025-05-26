import requests
import streamlit as st
import sqlite3
import pandas as pd

# Pega a chave da API do OpenRouter a partir do secrets.toml
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemma-3-27b-it:free"  # Modelo gratuito

def get_estrutura_dinamica(sqlite_path):
    """Busca estrutura dinâmica se existir"""
    try:
        with sqlite3.connect(sqlite_path) as conn:
            df = pd.read_sql("SELECT tabela, coluna, tipo, exemplo, descricao FROM estrutura_dinamica", conn)
        if not df.empty:
            return df
    except Exception as e:
        return None
    return None

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")
    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    estrutura = get_estrutura_dinamica(sqlite_path)
    estrutura_msg = ""
    if estrutura is not None:
        exemplos = []
        for i, row in estrutura.iterrows():
            exemplos.append(f"Tabela: {row['tabela']}, Coluna: {row['coluna']}, Descrição: {row['descricao']}, Tipo: {row['tipo']}, Exemplo: {row['exemplo']}")
            if i > 30:
                exemplos.append("...")
                break
        estrutura_msg = "\nExemplo da estrutura do banco:\n" + "\n".join(exemplos)
    else:
        estrutura_msg = "\n(Estrutura dinâmica não carregada. A resposta pode ser limitada.)"

    # Mensagem para IA, orientando a pedir detalhamento se necessário
    system_content = (
        "Você é um assistente de BI. "
        "Responda perguntas de negócio analisando dados de um banco relacional conforme estrutura abaixo. "
        "Nunca peça ao usuário a estrutura das tabelas; use apenas o que está na estrutura dinâmica (exemplo abaixo). "
        "Quando o usuário perguntar, verifique se precisa perguntar algo (ex: se quer um resultado analítico ou sintético) antes de responder. "
        "Ao responder, gere a análise ideal em texto, em tabela ou gráfico — sem mostrar SQL. "
        "Se não encontrar dados, avise que não foi possível localizar o dado solicitado. "
        "Se a estrutura não for suficiente, tente deduzir pelas descrições. "
        + estrutura_msg
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": pergunta},
    ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 900,
        "temperature": 0.1
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        resposta = response.json()["choices"][0]["message"]["content"]
        st.success(resposta)
    except Exception as e:
        st.error(f"Erro ao acessar o OpenRouter: {e}")
        st.exception(e)
