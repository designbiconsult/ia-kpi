import requests
import streamlit as st
import sqlite3
import pandas as pd

# Use a sua chave do OpenRouter salva em st.secrets ou direto no código
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "SUA_CHAVE_AQUI")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.3-70b-instruct:free"

def get_estrutura_context(sqlite_path):
    # Lê até 100 colunas/tabelas da estrutura_dinamica para dar contexto à IA
    contexto = []
    try:
        with sqlite3.connect(sqlite_path, timeout=10) as conn:
            df = pd.read_sql("SELECT tabela, coluna, tipo, descricao FROM estrutura_dinamica LIMIT 100", conn)
            for _, row in df.iterrows():
                contexto.append(f"Tabela: {row['tabela']} | Coluna: {row['coluna']} | Tipo: {row['tipo']} | Descrição: {row['descricao']}")
    except Exception as e:
        contexto = ["Contexto do banco não disponível."]
    return "\n".join(contexto)

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
        {"role": "user", "content": pergunta}
    ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 1200,
        "temperature": 0.2
    }
    try:
        # Pede para a IA gerar o SQL e a resposta pronta
        messages.append({"role": "system", "content": "Retorne o SQL para obter o resultado, e diga qual visual usar (tabela, cartão, gráfico). Responda o resultado ao usuário, não apenas o SQL."})
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        resp_json = response.json()
        resposta = resp_json["choices"][0]["message"]["content"]

        # Aqui você pode implementar a extração do SQL da resposta e execução automática (pode evoluir para parsing robusto)
        st.success(resposta)
    except Exception as e:
        st.error(f"Erro ao acessar o OpenRouter: {e}")
        st.exception(e)
