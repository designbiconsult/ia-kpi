import requests
import streamlit as st

OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")  # Nunca deixe exposta!
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.3-70b-instruct:free"

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")
    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    # Mensagem de contexto para a IA
    messages = [
        {"role": "system", "content": (
            "Você é um assistente inteligente para análise de indicadores de gestão empresarial. "
            "Seja objetivo e forneça respostas claras com base nos dados disponíveis no banco SQLite do projeto. "
            "Se necessário, peça esclarecimentos ao usuário sobre o tipo de análise desejada (ex: sintética ou analítica)."
        )},
        {"role": "user", "content": pergunta},
    ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 800,
        "temperature": 0.2
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=45)
        response.raise_for_status()
        resposta = response.json()["choices"][0]["message"]["content"]
        st.success(resposta)
    except Exception as e:
        st.error(f"Erro ao acessar o OpenRouter: {e}")
        st.exception(e)
