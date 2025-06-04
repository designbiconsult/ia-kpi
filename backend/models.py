import sqlite3

DB_PATH = "database.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def criar_tabelas():
    with get_conn() as conn:
        # Usuários
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                email TEXT UNIQUE,
                senha TEXT
            )
        """)
        # Relacionamentos
        conn.execute("""
            CREATE TABLE IF NOT EXISTS relacionamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tabela_origem TEXT,
                coluna_origem TEXT,
                tabela_destino TEXT,
                coluna_destino TEXT,
                tipo_relacionamento TEXT
            )
        """)
        # Indicadores
        conn.execute("""
            CREATE TABLE IF NOT EXISTS indicadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                setor TEXT,
                nome TEXT,
                mapeamento TEXT
            )
        """)
        conn.commit()

# ---- Usuários ----

def autenticar_usuario(email, senha):
    with get_conn() as conn:
        row = conn.execute("SELECT id, nome, email FROM usuarios WHERE email=? AND senha=?", (email, senha)).fetchone()
        if row:
            return {"id": row[0], "nome": row[1], "email": row[2]}
        return None

def cadastrar_usuario(nome, email, senha):
    with get_conn() as conn:
        try:
            conn.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
            conn.commit()
            return {"ok": True}
        except sqlite3.IntegrityError:
            raise Exception("Email já cadastrado.")

# ---- Sincronização (stub/mock, implemente conforme sua lógica real) ----

def sync_dados(usuario_id):
    # Aqui vai a lógica de sync real (ex: copiar tabelas do MySQL para SQLite do usuário)
    pass

# ---- Tabelas e Colunas ----

def listar_tabelas():
    with get_conn() as conn:
        tabelas = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return [t[0] for t in tabelas if t[0] not in ("relacionamentos", "indicadores", "usuarios", "sqlite_sequence")]

def listar_colunas(tabela):
    with get_conn() as conn:
        cols = conn.execute(f"PRAGMA table_info({tabela})").fetchall()
        return [c[1] for c in cols]

# ---- Relacionamentos ----

def listar_relacionamentos():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM relacionamentos").fetchall()
        return [
            {
                "id": r[0],
                "tabela_origem": r[1],
                "coluna_origem": r[2],
                "tabela_destino": r[3],
                "coluna_destino": r[4],
                "tipo_relacionamento": r[5]
            }
            for r in rows
        ]

def criar_relacionamento(rel):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO relacionamentos (tabela_origem, coluna_origem, tabela_destino, coluna_destino, tipo_relacionamento) VALUES (?, ?, ?, ?, ?)",
            (rel["tabela_origem"], rel["coluna_origem"], rel["tabela_destino"], rel["coluna_destino"], rel["tipo_relacionamento"])
        )
        conn.commit()

def deletar_relacionamento(rel_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM relacionamentos WHERE id=?", (rel_id,))
        conn.commit()

# ---- Indicadores ----

def listar_indicadores():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM indicadores").fetchall()

def listar_indicadores_por_usuario(usuario_id, setor):
    with get_conn() as conn:
        res = conn.execute("SELECT id, nome, mapeamento FROM indicadores WHERE usuario_id=? AND setor=?", (usuario_id, setor)).fetchall()
        return [{"id": r[0], "nome": r[1], "mapeamento": r[2]} for r in res]

def criar_indicador(usuario_id, setor, nome, mapeamento):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO indicadores (usuario_id, setor, nome, mapeamento) VALUES (?, ?, ?, ?)",
            (usuario_id, setor, nome, mapeamento)
        )
        conn.commit()
