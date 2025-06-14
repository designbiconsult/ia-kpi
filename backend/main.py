from fastapi import FastAPI, HTTPException, Path, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
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
                perfil TEXT NOT NULL, -- admin_geral, admin_cliente, user
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
    conexao: ConexaoInput,  # ATENÇÃO: Só o tipo, SEM Body()
):
    # Autentica usuário (pelo email/senha do payload)
    user = get_current_user(conexao.email, conexao.senha)
    # Só admin geral ou admin_cliente da empresa podem alterar
    if user["perfil"] not in ["admin_geral", "admin_cliente"] or user["empresa_id"] != empresa_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")
    # Atualiza conexão
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

# --- DEMAIS ENDPOINTS EXEMPLO ABAIXO ---

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
