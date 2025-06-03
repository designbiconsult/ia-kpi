import requests
import streamlit as st
import sqlite3
import pandas as pd

USE_LOCAL_OLLAMA = True  # True = IA local (Ollama), False = OpenRouter

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "sqlcoder:15b" # <- Modelo correto aqui

OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "sua_chave_aqui")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

def carregar_estrutura_dinamica(sqlite_path):
    try:
        with sqlite3.connect(sqlite_path) as conn:
            df = pd.read_sql("SELECT tabela, coluna, tipo, descricao FROM estrutura_dinamica", conn)
        if df.empty:
            return None, "Tabela estrutura_dinamica está vazia."
        estrutura_txt = ""
        for row in df.itertuples():
            estrutura_txt += f"Tabela: {row.tabela}, Coluna: {row.coluna}, Tipo: {row.tipo}, Descrição: {row.descricao}\n"
        return estrutura_txt, None
    except Exception as e:
        return None, f"Erro ao ler estrutura_dinamica: {e}"

def extrair_sql(resposta_ia):
    """
    Extrai o primeiro bloco começando com SELECT.
    """
    linhas = resposta_ia.splitlines()
    sql_block = ""
    in_sql = False
    for l in linhas:
        if l.strip().upper().startswith("SELECT"):
            in_sql = True
        if in_sql:
            sql_block += l + "\n"
        if in_sql and l.strip() == "":
            break
    return sql_block.strip()

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")

    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    estrutura, erro_estrutura = carregar_estrutura_dinamica(sqlite_path)
    if not estrutura:
        st.error(f"Estrutura dinâmica não carregada. {erro_estrutura or ''}\nTente sincronizar as tabelas primeiro.")
        return

    # Prompt objetivo para SQLCoder: gere apenas SQL
    prompt_base = (
        "Você é um assistente que converte perguntas em SQL para análise de dados. "
        "Use SOMENTE as tabelas e colunas listadas abaixo. "
        "Nunca explique ou faça comentários, apenas gere o SQL pedido e nada mais. "
        "Se o usuário pedir dados para datas futuras, gere o SQL normalmente com o filtro de datas pedido. "
        "Estrutura do banco:\n"
        f"{estrutura}\n"
        "Pergunta do usuário: "
    )

    messages = [
        {"role": "system", "content": prompt_base},
        {"role": "user", "content": pergunta}
    ]

    try:
        if USE_LOCAL_OLLAMA:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False
                },
                timeout=5000
            )
            if response.status_code == 200:
                content = response.json()
                ia_response = content.get("message", {}).get("content", "")
            else:
                st.error(f"Erro ao acessar IA local: {response.text}")
                return
        else:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            body = {
                "model": OPENROUTER_MODEL,
                "messages": messages,
                "max_tokens": 900,
                "temperature": 0.2
            }
            response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=120)
            response.raise_for_status()
            result = response.json()
            ia_response = result["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Erro ao acessar IA: {e}")
        st.exception(e)
        return

    # Extrai SQL e mostra
    sql_sugerido = extrair_sql(ia_response)
    if sql_sugerido:
        st.write("**SQL sugerido pela IA:**")
        st.code(sql_sugerido, language="sql")
        # Tenta executar o SQL!
        try:
            df_result = pd.read_sql(sql_sugerido, sqlite3.connect(sqlite_path))
            if not df_result.empty:
                st.dataframe(df_result)
            else:
                st.info("Consulta SQL executada, mas não retornou resultados.")
        except Exception as e:
            st.error(f"Erro ao executar SQL gerado: {e}")
    else:
        st.warning("A IA não retornou um SQL válido. Resposta completa da IA:")
        st.info(ia_response)
