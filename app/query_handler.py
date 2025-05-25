import streamlit as st
from app.agent import run_agent
import pandas as pd
import time

# Coloque sua chave de API aqui se não estiver usando secrets:
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "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")

def executar_pergunta(pergunta: str, sqlite_path: str):
    """
    Executa a pergunta do usuário utilizando o modelo e exibe o resultado do SQL sugerido.
    Não chama sincronismo! Só trabalha com o banco local.
    """
    if not pergunta:
        st.warning("Digite uma pergunta para continuar.")
        return

    st.subheader("⏱ Tempo de execução")
    tempo = st.empty()
    status = st.empty()
    status.info("Consultando a IA...")

    start_time = time.time()
    resultado = None

    try:
        while resultado is None:
            tempo.text(f"{int(time.time() - start_time)} segundos...")
            resultado = run_agent(pergunta, sqlite_path)
            break
    except Exception as e:
        st.error(f"Erro ao consultar a IA: {e}")
        return

    if not resultado:
        return

    sqlite_engine, sql_code = resultado

    st.subheader("📄 Consulta sugerida pela IA:")
    st.code(sql_code, language="sql")

    if st.button("Executar consulta"):
        try:
            df_result = pd.read_sql(sql_code, con=sqlite_engine)
            st.dataframe(df_result, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao executar SQL: {e}")
