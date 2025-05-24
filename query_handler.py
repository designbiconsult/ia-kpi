import requests
import streamlit as st

# Sua chave OpenRouter – Troque para variáveis de ambiente depois!
import os
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

def responder_pergunta_openrouter(pergunta, contexto=""):
    """
    Envia a pergunta para a OpenRouter AI e retorna a resposta.
    contexto pode ser usado para passar informações sobre tabelas, colunas, etc.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    # Monte a mensagem, incluindo contexto se desejar
    prompt_usuario = pergunta
    if contexto:
        prompt_usuario += f"\n\nContexto:\n{contexto}"

    data = {
        "model": "meta-llama/llama-3-70b-instruct",  # Pode trocar por outro modelo suportado
        "messages": [
            {"role": "user", "content": prompt_usuario}
        ],
        "max_tokens": 600,
        "temperature": 0.2
    }
    resp = requests.post(url, json=data, headers=headers, timeout=60)
    resp.raise_for_status()
    resposta = resp.json()['choices'][0]['message']['content']
    return resposta

def executar_pergunta(pergunta, sqlite_path):
    """
    Recebe a pergunta do usuário, gera contexto das tabelas e chama a IA.
    """
    # (Opcional) Montar um resumo das tabelas para dar contexto ao LLM
    contexto = ""
    try:
        import sqlite3
        import pandas as pd
        with sqlite3.connect(sqlite_path, timeout=10) as conn:
            # Exemplo: listar as tabelas e colunas para o LLM usar como base
            estrutura = pd.read_sql("SELECT tabela, coluna, descricao FROM estrutura_dinamica LIMIT 30", conn)
            linhas = []
            for i, row in estrutura.iterrows():
                linhas.append(f"Tabela: {row['tabela']} | Coluna: {row['coluna']} | {row['descricao']}")
            contexto = "\n".join(linhas)
    except Exception as e:
        contexto = ""

    with st.spinner("Aguarde! A IA está pensando..."):
        try:
            resposta = responder_pergunta_openrouter(pergunta, contexto=contexto)
            st.success(resposta)
            # Aqui você pode salvar pergunta/resposta no banco para aprendizado futuro!
        except Exception as e:
            st.error(f"Erro ao acessar a OpenRouter: {e}")
