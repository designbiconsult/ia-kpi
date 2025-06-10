import sqlite3
import pandas as pd

DB_PATH = "database.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def buscar_usuario(email, senha):
    with get_conn() as conn:
        row = conn.execute("SELECT id, nome, email, host, porta, usuario_banco, senha_banco, schema FROM usuarios WHERE email=? AND senha=?", (email, senha)).fetchone()
        if row:
            return {
                "id": row[0], "nome": row[1], "email": row[2],
                "host": row[3], "porta": row[4], "usuario_banco": row[5],
                "senha_banco": row[6], "schema": row[7]
            }
        return None

def salvar_conexao_usuario(usuario_id, dados):
    with get_conn() as conn:
        conn.execute(
            "UPDATE usuarios SET host=?, porta=?, usuario_banco=?, senha_banco=?, schema=? WHERE id=?",
            (
                dados.get("host"),
                dados.get("porta"),
                dados.get("usuario_banco"),
                dados.get("senha_banco"),
                dados.get("schema"),
                usuario_id,
            ),
        )
        conn.commit()

def listar_tabelas_sqlite():
    with get_conn() as conn:
        tabelas = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return [t[0] for t in tabelas if t[0] not in ("relacionamentos", "indicadores", "usuarios", "sqlite_sequence")]

def listar_colunas_sqlite(tabela):
    with get_conn() as conn:
        cols = conn.execute(f"PRAGMA table_info({tabela})").fetchall()
        return [c[1] for c in cols]

def sync_tabelas_mysql_sqlite(conn_mysql, tabelas, usuario_id):
    # Cria um arquivo SQLite exclusivo por usuário (ajuste se quiser)
    db_local = DB_PATH
    for tabela in tabelas:
        # Puxa dados do MySQL para pandas DataFrame
        df = pd.read_sql(f"SELECT * FROM {tabela}", conn_mysql)
        # Escreve no SQLite, sobrescrevendo
        with sqlite3.connect(db_local) as conn_sqlite:
            df.to_sql(tabela, conn_sqlite, if_exists='replace', index=False)
