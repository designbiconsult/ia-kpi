import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, inspect
import streamlit as st
import requests

def gerar_descricao_ia(nome_tabela, nome_coluna, tipo_dado, valor_exemplo):
    """
    Usa o modelo gratuito do OpenRouter (ou local) para gerar descrição automática.
    Troque a URL/modelo conforme necessário.
    """
    OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "SUA_API_KEY")
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "meta-llama/llama-3.3-70b-instruct:free"

    prompt = (
        f"Tabela: {nome_tabela}\n"
        f"Coluna: {nome_coluna}\n"
        f"Tipo de dado: {tipo_dado}\n"
        f"Valor exemplo: {valor_exemplo}\n\n"
        "Explique brevemente para um gestor o que representa essa coluna."
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Você é um assistente de BI que gera descrições simples para campos de banco de dados corporativos."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 120,
        "temperature": 0.2
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=25)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Descrição não gerada (erro: {e})"

def sync_mysql_to_sqlite():
    """
    Sincroniza todas as views e tabelas do schema de um banco MySQL para um banco SQLite local,
    usando as credenciais fornecidas pelo usuário via Streamlit.
    Só gera descrição para novas colunas.
    """
    mysql_host = st.session_state.get("mysql_host")
    mysql_port = st.session_state.get("mysql_port")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")
    output_sqlite_path = st.session_state.get("sqlite_path", "data/cliente_dados.db")

    if not all([mysql_host, mysql_port, mysql_user, mysql_password, mysql_database]):
        st.error("Credenciais incompletas. Verifique a conexão antes de sincronizar.")
        return

    mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
    mysql_engine = create_engine(mysql_uri)
    inspector = inspect(mysql_engine)

    os.makedirs(os.path.dirname(output_sqlite_path), exist_ok=True)
    with sqlite3.connect(output_sqlite_path, timeout=30) as sqlite_conn:
        try:
            views = inspector.get_view_names(schema=mysql_database)
            tables = inspector.get_table_names(schema=mysql_database)
            entidades = views + tables

            for entidade in entidades:
                st.write(f"🔄 Sincronizando: {entidade}")
                df = pd.read_sql(f"SELECT * FROM `{mysql_database}`.`{entidade}`", mysql_engine)
                df.to_sql(entidade, con=sqlite_conn, if_exists="replace", index=False)

            salvar_estrutura_dinamica(entidades, sqlite_conn, mysql_engine, mysql_database)
            st.success("✅ Sincronização concluída com sucesso.")

        except Exception as e:
            st.error(f"❌ Erro ao sincronizar: {e}")
        finally:
            mysql_engine.dispose()

def salvar_estrutura_dinamica(entidades, conn_sqlite, mysql_engine, mysql_database):
    """
    Cria e preenche a tabela estrutura_dinamica apenas para novas colunas do SQLite.
    Gera descrição automática com IA só para o que não existe ainda.
    """
    cursor = conn_sqlite.cursor()
    # Certifica-se que a tabela existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estrutura_dinamica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tabela TEXT,
            coluna TEXT,
            tipo TEXT,
            exemplo TEXT,
            descricao TEXT
        )
    ''')
    conn_sqlite.commit()

    # Carrega todas as colunas já mapeadas
    cursor.execute("SELECT tabela, coluna FROM estrutura_dinamica")
    existentes = set((row[0], row[1]) for row in cursor.fetchall())

    # Percorre cada entidade e coluna
    from sqlalchemy import inspect as insp_sql
    inspector = insp_sql(mysql_engine)

    for tabela in entidades:
        try:
            colunas = inspector.get_columns(tabela, schema=mysql_database)
            for col in colunas:
                nome_coluna = col["name"]
                tipo_coluna = str(col["type"])

                # Só adiciona se ainda não existe mapeamento
                if (tabela, nome_coluna) not in existentes:
                    # Busca um exemplo
                    exemplo = ""
                    try:
                        df_exemplo = pd.read_sql(f"SELECT `{nome_coluna}` FROM `{mysql_database}`.`{tabela}` WHERE `{nome_coluna}` IS NOT NULL LIMIT 1", mysql_engine)
                        if not df_exemplo.empty:
                            exemplo = str(df_exemplo.iloc[0][0])
                    except:
                        exemplo = ""

                    # Gera descrição via IA só para novas colunas!
                    descricao = gerar_descricao_ia(tabela, nome_coluna, tipo_coluna, exemplo)

                    cursor.execute('''
                        INSERT INTO estrutura_dinamica (tabela, coluna, tipo, exemplo, descricao)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (tabela, nome_coluna, tipo_coluna, exemplo, descricao))
                    conn_sqlite.commit()
        except Exception as e:
            print(f"Erro ao processar tabela {tabela}: {e}")

    cursor.close()
