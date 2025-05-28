import requests
import streamlit as st

# Configuração do endpoint local do Ollama (IA local)
OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL = "llama3"  # Substitua por outro modelo instalado se preferir

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")
    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    # Mensagem de sistema para orientar o modelo
    messages = [
        {
            "role": "system",
            "content": (
                "Você é um assistente inteligente para análise de indicadores empresariais. "
                "Faça perguntas de refinamento se necessário (exemplo: resultado analítico ou sintético?), "
                "e use dados do banco SQLite indicado. Sempre responda de forma objetiva, e caso necessário, "
                "retorne respostas estruturadas em texto e tabelas usando Markdown."
            )
        },
        {"role": "user", "content": pergunta}
    ]

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MODEL,
                "messages": messages,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        # A resposta pode variar dependendo da versão do Ollama. Normalmente:
        if "message" in data and "content" in data["message"]:
            resposta = data["message"]["content"]
        elif "choices" in data and data["choices"]:
            resposta = data["choices"][0]["message"]["content"]
        else:
            resposta = "Resposta não encontrada na resposta da IA local."
        st.success(resposta)
    except Exception as e:
        st.error(f"Erro ao acessar o Ollama local: {e}")
        st.exception(e)
