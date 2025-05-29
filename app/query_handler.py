import requests
import streamlit as st

OLLAMA_URL = "http://localhost:11434/api/chat"

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")
    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    prompt = (
        "Você é um assistente inteligente para análise de indicadores de gestão empresarial. "
        "Responda sempre baseado nos dados do banco local. Peça ao usuário para escolher entre análise sintética (por referência/descrição) "
        "ou analítica (por cor/tamanho) se a pergunta não estiver clara."
        "\n\nPergunta: " + pergunta
    )

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3",  # Ou outro modelo instalado localmente!
                "messages": [
                    {"role": "system", "content": "Você é um assistente de BI local."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        # Ollama local responde: {"message": {"role": "...", "content": "..."}}
        resposta = data["message"]["content"]
        st.success(resposta)
    except Exception as e:
        st.error(f"Erro ao acessar IA local: {e}")
        st.exception(e)
