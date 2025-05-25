import requests
import streamlit as st

# RECOMENDADO: Use o secrets.toml, mas aqui já vai seu fallback
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "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")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3-70b-instruct"  # Modelo gratuito

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")
    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    # Mensagem do chat
    messages = [
        {"role": "system", "content": "Você é um assistente de BI e indicadores empresariais. Sempre que necessário, refine as perguntas do usuário pedindo informações adicionais para entregar respostas mais úteis."},
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
