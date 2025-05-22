def sync_mysql_to_sqlite():
    """
    Sincroniza todas as views e tabelas do schema especificado de um banco MySQL para um banco SQLite local,
    usando as credenciais fornecidas via Streamlit.
    """
    import os
    import pandas as pd
    import sqlite3
    from sqlalchemy import create_engine, inspect
    import streamlit as st

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
    sqlite_conn = sqlite3.connect(output_sqlite_path)

    try:
        # Junta views e tabelas
        views = inspector.get_view_names(schema=mysql_database)
        tabelas = inspector.get_table_names(schema=mysql_database)
        entidades = views + tabelas

        for nome in entidades:
            st.write(f"🔄 Sincronizando: {nome}")
            df = pd.read_sql(f"SELECT * FROM `{mysql_database}`.`{nome}`", mysql_engine)
            df.to_sql(nome, con=sqlite_conn, if_exists="replace", index=False)

        st.success("✅ Sincronização de views e tabelas concluída com sucesso.")
    except Exception as e:
        st.error(f"❌ Erro ao sincronizar: {e}")
    finally:
        sqlite_conn.close()
        mysql_engine.dispose()
def salvar_estrutura_dinamica(sqlite_path):
    """
    Extrai a estrutura das tabelas do SQLite e salva em uma tabela chamada estrutura_dinamica.
    """
    conn = sqlite3.connect(sqlite_path)
    c = conn.cursor()

    # Cria a tabela se não existir
    c.execute("""
        CREATE TABLE IF NOT EXISTS estrutura_dinamica (
            tabela TEXT,
            coluna TEXT,
            tipo TEXT,
            exemplo TEXT,
            descricao TEXT
        )
    """)

    # Limpa dados anteriores
    c.execute("DELETE FROM estrutura_dinamica")

    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'")
    tabelas = [row[0] for row in cursor.fetchall()]

    for tabela in tabelas:
        colunas = conn.execute(f"PRAGMA table_info('{tabela}')").fetchall()
        exemplo = conn.execute(f"SELECT * FROM {tabela} LIMIT 1").fetchone()

        for idx, col in enumerate(colunas):
            nome = col[1]
            tipo = col[2]
            valor_exemplo = str(exemplo[idx]) if exemplo else "Exemplo indisponível"
            descricao = f"Coluna '{nome}' da tabela '{tabela}' com tipo {tipo}"
            c.execute("""
                INSERT INTO estrutura_dinamica (tabela, coluna, tipo, exemplo, descricao)
                VALUES (?, ?, ?, ?, ?)
            """, (tabela, nome, tipo, valor_exemplo, descricao))

    conn.commit()
    conn.close()
