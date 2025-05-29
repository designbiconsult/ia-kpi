import requests
import streamlit as st
import sqlite3
import re

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3"  # Troque para "mistral" ou outro se preferir

def executar_pergunta(pergunta, sqlite_path=None):
    st.markdown("#### 🤖 Resposta da IA")
    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    # Prompt para gerar SQL e resposta explicada
    messages = [
        {"role": "system", "content": (
            "Você é um assistente de BI. Com base na estrutura de dados disponível, gere uma consulta SQL para responder à pergunta do usuário. "
            "Depois, gere uma resposta explicando o resultado ao usuário em linguagem natural. "
            "Responda sempre neste formato:\n"
            "SQL:\n```sql\nSELECT ...\n```\n\nRESPOSTA:\n(Explicação da resposta)"
        )},
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
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        resposta = ""
        sql_detectado = ""
        explicacao = ""
        if "message" in result and "content" in result["message"]:
            resposta = result["message"]["content"]
            # Extrai o SQL do bloco ```sql ... ```
            sql_blocks = re.findall(r"```sql(.*?)```", resposta, re.DOTALL)
            if sql_blocks:
                sql_detectado = sql_blocks[0].strip()
                st.markdown("##### 📝 <span style='color:#02848a'>SQL sugerido pela IA:</span>", unsafe_allow_html=True)
                st.code(sql_detectado, language="sql")
                # Tenta rodar o SQL
                if sqlite_path and sql_detectado:
                    try:
                        with sqlite3.connect(sqlite_path) as conn:
                            resultado_sql = conn.execute(sql_detectado).fetchall()
                            columns = [desc[0] for desc in conn.execute(sql_detectado).description]
                            df = pd.DataFrame(resultado_sql, columns=columns)
                            if not df.empty:
                                st.dataframe(df)
                            else:
                                st.info("Consulta realizada, mas sem dados no resultado.")
                    except Exception as e:
                        st.error(f"Erro ao executar SQL gerado: {e}")
            else:
                st.info("A IA não retornou um SQL no formato esperado.")
            # Mostra a resposta explicativa se houver
            partes = re.split(r"```sql.*?```", resposta, flags=re.DOTALL)
            if len(partes) > 1:
                explicacao = partes[-1].strip()
                st.markdown("##### 🗨️ <span style='color:#02848a'>Resposta sugerida:</span>", unsafe_allow_html=True)
                st.write(explicacao)
            elif resposta:
                st.write(resposta)
        else:
            st.error("A IA local não retornou resposta no formato esperado.")
    except Exception as e:
        st.error(f"Erro ao acessar IA local: {e}")
        st.exception(e)
