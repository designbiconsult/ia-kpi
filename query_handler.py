import requests
import streamlit as st

# Coloque aqui a sua chave da OpenRouter (prefira colocar em segredo/variável ambiente)
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "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")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4-turbo"  # Pode escolher outro do OpenRouter se quiser

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")
    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    # Opcional: adicione contexto do banco/localização do usuário, etc.

    # Monte a mensagem do chat:
    messages = [
        {"role": "system", "content": "Você é um assistente inteligente para análise de indicadores de gestão empresarial. Seja objetivo e forneça respostas claras com base nos dados disponíveis."},
        {"role": "user", "content": pergunta},
    ]

    # Monta requisição ao OpenRouter
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
