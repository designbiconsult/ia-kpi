from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from typing import Dict, List
import pymysql
import pandas as pd

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "database.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

@app.on_event("startup")
def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                tipo_banco TEXT,
                host TEXT,
                porta TEXT,
                usuario_banco TEXT,
                senha_banco TEXT,
                schema TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                email TEXT UNIQUE,
                senha TEXT,
                perfil TEXT DEFAULT 'usuario',   -- 'usuario' ou 'admin_geral'
                empresa_id INTEGER,
                FOREIGN KEY (empresa_id) REFERENCES empresas(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tabelas_sincronizadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER,
                nome_tabela TEXT,
                ultima_sincronizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(empresa_id, nome_tabela)
            )
        """)
        # Tabela de relacionamentos
        conn.execute("""
            CREATE TABLE IF NOT EXISTS relacionamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER,
                tabela_origem TEXT,
                coluna_origem TEXT,
                tabela_destino TEXT,
                coluna_destino TEXT,
                tipo_relacionamento TEXT, -- Ex: '1-1', '1-N', 'N-N'
                UNIQUE(empresa_id, tabela_origem, coluna_origem, tabela_destino, coluna_destino)
            )
        """)
        conn.commit()

def get_current_user(email: str, senha: str):
    with get_conn() as conn:
        user = conn.execute(
            "SELECT id, nome, email, senha, perfil, empresa_id FROM usuarios WHERE email=? AND senha=?",
            (email, senha)
        ).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Credenciais inválidas.")
        return {
            "id": user[0],
            "nome": user[1],
            "email": user[2],
            "senha": user[3],
            "perfil": user[4],       # 'admin_geral' ou 'usuario'
            "empresa_id": user[5]
        }

# --- LOGIN ---
@app.post("/login")
def login(credentials: dict = Body(...)):
    email = credentials.get("email")
    senha = credentials.get("senha")
    user = get_current_user(email, senha)
    return user

# --- CADASTRAR EMPRESA + USUÁRIO ADMIN ---
@app.post("/empresas/cadastrar")
def cadastrar_empresa(dados: dict = Body(...)):
    empresa = dados.get("empresa")
    usuario = dados.get("usuario")
    if not empresa or not usuario:
        raise HTTPException(status_code=400, detail="Dados incompletos.")

    with get_conn() as conn:
        # Cria empresa
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO empresas (nome, tipo_banco, host, porta, usuario_banco, senha_banco, schema)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                empresa.get("nome"), empresa.get("tipo_banco"), empresa.get("host"), empresa.get("porta"),
                empresa.get("usuario_banco"), empresa.get("senha_banco"), empresa.get("schema")
            )
        )
        empresa_id = cur.lastrowid
        # Cria usuário admin (perfil 'admin_geral')
        cur.execute(
            """INSERT INTO usuarios (nome, email, senha, perfil, empresa_id)
               VALUES (?, ?, ?, 'admin_geral', ?)""",
            (
                usuario.get("nome"), usuario.get("email"), usuario.get("senha"), empresa_id
            )
        )
        conn.commit()
        return {"ok": True, "empresa_id": empresa_id}

# --- DADOS DA EMPRESA ---
@app.get("/empresas/{empresa_id}")
def dados_empresa(empresa_id: int, email: str = Query(...), senha: str = Query(...)):
    user = get_current_user(email=email, senha=senha)
    if user["perfil"] != "admin_geral" and user["empresa_id"] != empresa_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")
    with get_conn() as conn:
        row = conn.execute("""
            SELECT id, nome, tipo_banco, host, porta, usuario_banco, senha_banco, schema
            FROM empresas WHERE id=?
        """, (empresa_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Empresa não encontrada.")
        return {
            "id": row[0],
            "nome": row[1],
            "tipo_banco": row[2],
            "host": row[3],
            "porta": row[4],
            "usuario_banco": row[5],
            "senha_banco": row[6],
            "schema": row[7]
        }

# --- ATUALIZAR CONEXÃO DA EMPRESA ---
@app.put("/empresas/{empresa_id}/conexao")
def atualizar_conexao(
    empresa_id: int = Path(...),
    dados: dict = Body(...),
    email: str = Query(...),
    senha: str = Query(...)
):
    user = get_current_user(email=email, senha=senha)
    if user["perfil"] != "admin_geral" and user["empresa_id"] != empresa_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")
    with get_conn() as conn:
        conn.execute("""
            UPDATE empresas SET
                tipo_banco = ?,
                host = ?,
                porta = ?,
                usuario_banco = ?,
                senha_banco = ?,
                schema = ?
            WHERE id = ?
        """, (
            dados.get("tipo_banco"), dados.get("host"), dados.get("porta"),
            dados.get("usuario_banco"), dados.get("senha_banco"), dados.get("schema"),
            empresa_id
        ))
        conn.commit()
    return {"ok": True}

# --- ENDPOINT DE LISTA DE TABELAS PARA SINCRONISMO ---
@app.get("/sincronismo/tabelas")
def listar_tabelas_sincronismo(
    empresa_id: int = Query(...),
    email: str = Query(...),
    senha: str = Query(...)
):
    user = get_current_user(email=email, senha=senha)
    if user["perfil"] != "admin_geral" and user["empresa_id"] != empresa_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    with get_conn() as conn:
        res1 = conn.execute("SELECT nome_tabela FROM tabelas_sincronizadas WHERE empresa_id=?", (empresa_id,))
        sincronizadas = [r[0] for r in res1.fetchall()]
        empresa_row = conn.execute(
            "SELECT tipo_banco, host, porta, usuario_banco, senha_banco, schema FROM empresas WHERE id=?",
            (empresa_id,)
        ).fetchone()
    if not empresa_row:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    tipo_banco, host, porta, usuario_banco, senha_banco, schema = empresa_row

    novas_tabelas = []
    if tipo_banco == "mysql":
        try:
            conn_mysql = pymysql.connect(
                host=host, port=int(porta), user=usuario_banco, password=senha_banco,
                database=schema, charset='utf8mb4'
            )
            with conn_mysql.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (schema,))
                resultado_tabelas = [row[0] for row in cur.fetchall()]
                cur.execute("SELECT table_name FROM information_schema.views WHERE table_schema = %s", (schema,))
                resultado_views = [row[0] for row in cur.fetchall()]
            conn_mysql.close()
            todas = resultado_tabelas + resultado_views
            novas_tabelas = [t for t in todas if t not in sincronizadas]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao conectar MySQL: {str(e)}")
    else:
        novas_tabelas = []

    return {
        "sincronizadas": sincronizadas,
        "novas": novas_tabelas
    }

# --- SINCRONIZAR NOVAS TABELAS ---
@app.post("/sincronismo/sincronizar-novas")
def sincronizar_novas(
    body: dict = Body(...)
):
    empresa_id = body.get("empresa_id")
    tabelas = body.get("tabelas", [])
    email = body.get("email")
    senha = body.get("senha")

    user = get_current_user(email=email, senha=senha)
    if user["perfil"] != "admin_geral" and user["empresa_id"] != empresa_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    with get_conn() as conn:
        empresa = conn.execute(
            "SELECT tipo_banco, host, porta, usuario_banco, senha_banco, schema FROM empresas WHERE id=?",
            (empresa_id,)
        ).fetchone()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada.")
        tipo_banco, host, porta, usuario_banco, senha_banco, schema = empresa

    if tipo_banco != "mysql":
        raise HTTPException(status_code=400, detail="Sincronização suportada apenas para MySQL.")

    try:
        conn_mysql = pymysql.connect(
            host=host, port=int(porta), user=usuario_banco, password=senha_banco,
            database=schema, charset='utf8mb4'
        )
        tabelas_sincronizadas = []
        for tabela in tabelas:
            df = pd.read_sql(f"SELECT * FROM `{tabela}`", conn_mysql)
            with sqlite3.connect(DB_PATH) as conn_sqlite:
                df.to_sql(tabela, conn_sqlite, if_exists='replace', index=False)
            tabelas_sincronizadas.append(tabela)
        conn_mysql.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao sincronizar: {str(e)}")

    with get_conn() as conn:
        for tabela in tabelas_sincronizadas:
            conn.execute(
                """
                INSERT OR REPLACE INTO tabelas_sincronizadas (empresa_id, nome_tabela, ultima_sincronizacao)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (empresa_id, tabela)
            )
        conn.commit()

    return {"ok": True, "sincronizadas": tabelas_sincronizadas}

# ===============================
# === ENDPOINTS DE RELACIONAMENTOS ===
# ===============================

@app.get("/relacionamentos")
def listar_relacionamentos(empresa_id: int = Query(...), email: str = Query(...), senha: str = Query(...)):
    user = get_current_user(email=email, senha=senha)
    if user["empresa_id"] != empresa_id and user["perfil"] != "admin_geral":
        raise HTTPException(status_code=403, detail="Acesso negado.")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, tabela_origem, coluna_origem, tabela_destino, coluna_destino, tipo_relacionamento "
            "FROM relacionamentos WHERE empresa_id=?", (empresa_id,)
        ).fetchall()
    return [
        {
            "id": r[0], "tabela_origem": r[1], "coluna_origem": r[2],
            "tabela_destino": r[3], "coluna_destino": r[4],
            "tipo_relacionamento": r[5]
        } for r in rows
    ]

@app.post("/relacionamentos")
def adicionar_relacionamento(body: dict = Body(...)):
    empresa_id = body.get("empresa_id")
    tabela_origem = body.get("tabela_origem")
    coluna_origem = body.get("coluna_origem")
    tabela_destino = body.get("tabela_destino")
    coluna_destino = body.get("coluna_destino")
    tipo_relacionamento = body.get("tipo_relacionamento")
    email = body.get("email")
    senha = body.get("senha")
    user = get_current_user(email=email, senha=senha)
    if user["empresa_id"] != empresa_id and user["perfil"] != "admin_geral":
        raise HTTPException(status_code=403, detail="Acesso negado.")
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO relacionamentos "
            "(empresa_id, tabela_origem, coluna_origem, tabela_destino, coluna_destino, tipo_relacionamento) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (empresa_id, tabela_origem, coluna_origem, tabela_destino, coluna_destino, tipo_relacionamento)
        )
        conn.commit()
    return {"ok": True}

@app.delete("/relacionamentos/{relacionamento_id}")
def excluir_relacionamento(relacionamento_id: int, email: str = Query(...), senha: str = Query(...)):
    user = get_current_user(email=email, senha=senha)
    with get_conn() as conn:
        conn.execute("DELETE FROM relacionamentos WHERE id=?", (relacionamento_id,))
        conn.commit()
    return {"ok": True}

# Utilidade: retornar colunas de uma tabela do SQLite
@app.get("/tabelas/colunas")
def listar_colunas(tabela: str = Query(...)):
    with get_conn() as conn:
        cols = conn.execute(f"PRAGMA table_info({tabela})").fetchall()
    return [c[1] for c in cols]

# Utilidade: listar tabelas sincronizadas para seleção de relacionamento
@app.get("/tabelas/listar")
def listar_tabelas_sync(empresa_id: int = Query(...)):
    with get_conn() as conn:
        rows = conn.execute("SELECT nome_tabela FROM tabelas_sincronizadas WHERE empresa_id=?", (empresa_id,))
    return [r[0] for r in rows]
