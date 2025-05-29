# app/query_handler.py

import requests
import streamlit as st
import pandas as pd
import sqlite3

# CONFIG - URL IA LOCAL
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3"  # Pode ser outro modelo instalado no Ollama local

def carregar_estrutura_contexto(sqlite_path, limite_tabelas=15):
    """
    Carrega estrutura das tabelas e colunas do banco local,
    gera contexto para prompt da IA.
    """
    try:
        with sqlite3.connect(sqlite_path) as conn:
            df = pd.read_sql("SELECT tabela, coluna, tipo, exemplo, descricao FROM estrutura_dinamica", conn)
        if df.empty:
            return "Nenhuma tabela foi encontrada na estrutura dinâmica."
        # Limite de tabelas (para não explodir tokens)
        if len(df['tabela'].unique()) > limite_tabelas:
            tabelas = df['tabela'].unique()[:limite_tabelas]
            df = df[df['tabela'].isin(tabelas)]
        contexto = "Estrutura de dados disponível para análise:\n"
        for tabela in df['tabela'].unique():
            colunas = df[df['tabela']==tabela]
            cols_str = ", ".join([f"{r['coluna']} ({r['tipo']})" for _, r in colunas.iterrows()])
            contexto += f"  - {tabela}: {cols_str}\n"
        return contexto
    except Exception as e:
        return f"Estrutura dinâmica não carregada. A resposta pode ser limitada.\n(Erro: {e})"

def executar_pergunta(pergunta, sqlite_path):
    st.markdown("#### 🤖 Resposta da IA")

    if not pergunta.strip():
        st.info("Digite uma pergunta para a IA.")
        return

    # 1. Carrega a estrutura do banco para o contexto do prompt
    contexto_estrutura = carregar_estrutura_contexto(sqlite_path)
    st.info("**Estrutura disponível:**\n\n" + contexto_estrutura)

    # 2. Prompt de sistema para IA: NÃO inventar tabelas/colunas
    prompt_system = (
        "Você é um assistente de análise de dados conectado a um banco SQLite. "
        "Use apenas as tabelas e colunas abaixo para responder. "
        "Nunca invente tabelas ou colunas que não estejam nesta lista. "
        "Quando fizer SQL, utilize apenas esses nomes. "
        "Se possível, explique rapidamente o raciocínio e traga o resultado já formatado de forma clara. "
        "Se for possível, mostre a resposta em formato de tabela (quando apropriado)."
        "\n\n"
        f"{contexto_estrutura}"
    )

    # 3. Manda para IA local (Ollama)
    messages = [
        {"role": "system", "content": prompt_system},
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
            timeout=250
        )
        response.raise_for_status()
        resp_data = response.json()
        resposta_texto = resp_data.get("message", {}).get("content", "")

        # OPCIONAL: DEBUG - Mostrar SQL sugerido
        sql_start = resposta_texto.lower().find("select")
        sql_end = resposta_texto.lower().find(";", sql_start)
        sql_query = ""
        if sql_start != -1 and sql_end != -1:
            sql_query = resposta_texto[sql_start:sql_end+1]
            st.markdown(f"##### ⚡ SQL gerado pela IA (debug):\n```sql\n{sql_query}\n```")
            # Tenta executar o SQL, se possível
            try:
                with sqlite3.connect(sqlite_path) as conn:
                    df_result = pd.read_sql(sql_query, conn)
                st.markdown("#### 📋 Resultado em tabela:")
                st.dataframe(df_result)
            except Exception as e:
                st.error(f"Erro ao executar SQL gerado: {e}")
        else:
            st.markdown("ℹ️ Nenhum SQL detectado na resposta.")

        # Mostra a resposta completa da IA
        st.success(resposta_texto)
    except Exception as e:
        st.error(f"Erro ao acessar IA local: {e}")
        st.exception(e)
