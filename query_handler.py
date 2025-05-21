import streamlit as st
from app.agent import sync_mysql_to_sqlite_and_run_agent
import pandas as pd
import time

def executar_pergunta(pergunta: str, sqlite_path: str):
    """
    Executa a pergunta do usuário utilizando o modelo local e exibe o resultado do SQL sugerido,
    com um contador de tempo visível.
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
        # Mostra contador em tempo real enquanto executa a função
        while resultado is None:
            tempo.text(f"{int(time.time() - start_time)} segundos...")
            resultado = sync_mysql_to_sqlite_and_run_agent(pergunta)
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
