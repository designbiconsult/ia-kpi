from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import sqlite3

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
                nome TEXT NOT NULL,
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
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                perfil TEXT NOT NULL,
                empresa_id INTEGER,
                FOREIGN KEY(empresa_id) REFERENCES empresas(id)
            )
        """)
        conn.commit()

class ConexaoInput(BaseModel):
    tipo_banco: str
    host: str
    porta: str
    usuario_banco: str
    senha_banco: str
    schema: str
    email: str
    senha: str

def get_current_user(email: str, senha: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, nome, perfil, empresa_id FROM usuarios WHERE email=? AND senha=?",
            (email, senha)
        )
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Credenciais inválidas.")
        return {
            "id": row[0],
            "nome": row[1],
            "perfil": row[2],
            "empresa_id": row[3]
        }

@app.put("/empresas/{empresa_id}/conexao")
def atualizar_conexao(
    empresa_id: int,
    conexao: ConexaoInput,  # <-- Aqui está o truque: só o tipo!
):
    user = get_current_user(conexao.email, conexao.senha)
    if user["perfil"] not in ["admin_geral", "admin_cliente"] or user["empresa_id"] != empresa_id:
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
            conexao.tipo_banco, conexao.host, conexao.porta,
            conexao.usuario_banco, conexao.senha_banco, conexao.schema,
            empresa_id
        ))
        conn.commit()
    return {"ok": True}

@app.post("/empresas")
def cadastrar_empresa(nome: str = Query(...)):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO empresas (nome) VALUES (?)", (nome,))
        empresa_id = c.lastrowid
        conn.commit()
        return {"ok": True, "empresa_id": empresa_id}

@app.post("/usuarios")
def cadastrar_usuario(
    nome: str = Query(...),
    email: str = Query(...),
    senha: str = Query(...),
    perfil: str = Query(...),
    empresa_id: int = Query(...)
):
    with get_conn() as conn:
        try:
            conn.execute("""
                INSERT INTO usuarios (nome, email, senha, perfil, empresa_id)
                VALUES (?, ?, ?, ?, ?)
            """, (nome, email, senha, perfil, empresa_id))
            conn.commit()
            return {"ok": True}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Email já cadastrado.")

@app.post("/login")
def login(email: str = Query(...), senha: str = Query(...)):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, nome, perfil, empresa_id FROM usuarios WHERE email = ? AND senha = ?",
            (email, senha)
        )
        user = c.fetchone()
        if user:
            return {
                "id": user[0],
                "nome": user[1],
                "perfil": user[2],
                "empresa_id": user[3],
                "email": email,
                "senha": senha
            }
        else:
            raise HTTPException(status_code=401, detail="Credenciais inválidas.")

from fastapi import FastAPI, HTTPException, Query, Path, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from typing import List, Dict, Optional
import pymysql

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

# Autenticação
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
        conn.commit()

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
        # Cria usuário admin
        cur.execute(
            """INSERT INTO usuarios (nome, email, senha, perfil, empresa_id)
               VALUES (?, ?, ?, 'admin', ?)""",
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

# --- ENDPOINT CRUCIAL PARA O FRONTEND DE SINCRONISMO FUNCIONAR ---
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

# Você pode continuar expandindo a API com outros endpoints conforme necessidade!

