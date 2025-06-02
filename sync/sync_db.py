import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, inspect
import streamlit as st

def gerar_descricao_semantica(nome_tabela, nome_coluna):
    nome_tabela_low = nome_tabela.lower()
    if "pedido" in nome_tabela_low:
        tabela_desc = "Tabela de pedidos de venda realizados."
    elif "notafiscal" in nome_tabela_low or "saida" in nome_tabela_low:
        tabela_desc = "Tabela de notas fiscais de saída, representa o faturamento."
    elif "compra" in nome_tabela_low or "notaentrada" in nome_tabela_low or "entrada" in nome_tabela_low:
        tabela_desc = "Tabela de compras/nota de entrada, representa aquisições de materiais."
    else:
        tabela_desc = f"Tabela {nome_tabela}"

    if "referencia" in nome_coluna.lower():
        return f"{tabela_desc} - Código/referência do produto."
    if "descricao" in nome_coluna.lower():
        return f"{tabela_desc} - Descrição do produto."
    if "quant" in nome_coluna.lower():
        return f"{tabela_desc} - Quantidade relacionada ao item/produto."
    if "data" in nome_coluna.lower():
        return f"{tabela_desc} - Data relevante do processo."
    if "cor" in nome_coluna.lower():
        return f"{tabela_desc} - Cor do produto/material."
    if "tamanho" in nome_coluna.lower():
        return f"{tabela_desc} - Tamanho do produto/material."
    return f"{tabela_desc} - Coluna {nome_coluna}"

def salvar_estrutura_dinamica(entidades, conn_sqlite):
    cursor = conn_sqlite.cursor()
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
    cursor.execute("DELETE FROM estrutura_dinamica")
    conn_sqlite.commit()

    for tabela in entidades:
        try:
            df = pd.read_sql(f"SELECT * FROM {tabela} LIMIT 1", conn_sqlite)
            for coluna in df.columns:
                exemplo = str(df[coluna].iloc[0]) if not df.empty else ""
                tipo = str(df[coluna].dtype)
                descricao = gerar_descricao_semantica(tabela, coluna)
                cursor.execute('''
                    INSERT INTO estrutura_dinamica (tabela, coluna, tipo, exemplo, descricao)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tabela, coluna, tipo, exemplo, descricao))
        except Exception as e:
            print(f"Erro ao processar tabela {tabela}: {e}")
    conn_sqlite.commit()
    cursor.close()

def obter_lista_tabelas_views_remotas():
    mysql_host = st.session_state.get("mysql_host")
    mysql_port = st.session_state.get("mysql_port")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")
    try:
        mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
        mysql_engine = create_engine(mysql_uri)
        inspector = inspect(mysql_engine)
        tabelas = inspector.get_table_names(schema=mysql_database)
        views = inspector.get_view_names(schema=mysql_database)
        return tabelas + views
    except Exception as e:
        st.error(f"Erro ao buscar tabelas remotas: {e}")
        return []

def sync_mysql_to_sqlite(tabelas_sync):
    mysql_host = st.session_state.get("mysql_host")
    mysql_port = st.session_state.get("mysql_port")
    mysql_user = st.session_state.get("mysql_user")
    mysql_password = st.session_state.get("mysql_password")
    mysql_database = st.session_state.get("mysql_database")
    output_sqlite_path = st.session_state.get("sqlite_path", "data/cliente_dados.db")

    try:
        mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8"
        mysql_engine = create_engine(mysql_uri)
        os.makedirs(os.path.dirname(output_sqlite_path), exist_ok=True)
        with sqlite3.connect(output_sqlite_path, timeout=30) as sqlite_conn:
            for entidade in tabelas_sync:
                st.write(f"🔄 Sincronizando: {entidade}")
                df = pd.read_sql(f"SELECT * FROM `{mysql_database}`.`{entidade}`", mysql_engine)
                df.to_sql(entidade, con=sqlite_conn, if_exists="replace", index=False)
            salvar_estrutura_dinamica(tabelas_sync, sqlite_conn)
        st.success("✅ Sincronização concluída com sucesso.")
    except Exception as e:
        st.error(f"❌ Erro ao sincronizar: {e}")

def excluir_tabelas_sqlite(sqlite_path, tabelas_excluir):
    try:
        with sqlite3.connect(sqlite_path, timeout=10) as conn:
            c = conn.cursor()
            for tabela in tabelas_excluir:
                c.execute(f"DROP TABLE IF EXISTS `{tabela}`")
            conn.commit()
        st.success(f"Tabela(s) excluída(s) com sucesso: {', '.join(tabelas_excluir)}")
    except Exception as e:
        st.error(f"Erro ao excluir tabela(s): {e}")
