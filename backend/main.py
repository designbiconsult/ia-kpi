from fastapi import FastAPI, HTTPException, Path, Body, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from pydantic import BaseModel
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

# Inicializa tabelas se não existem
@app.on_event("startup")
def init_db():
    with get_conn() as conn:
        # Tabela de empresas
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
        # Tabela de usuários
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

# Pydantic para conexão
class ConexaoInput(BaseModel):
    tipo_banco: str
    host: str
    porta: str
    usuario_banco: str
    senha_banco: str
    schema: str
    email: str
    senha: str

# Pydantic para cadastro de empresa e admin inicial
class EmpresaCadastroInput(BaseModel):
    nome_empresa: str
    nome_usuario: str
    email: str
    senha: str

# --- AUTENTICAÇÃO ---
def get_current_user(email: str = Body(...), senha: str = Body(...)):
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

# --- CADASTRO DE EMPRESA + USUÁRIO ADMIN CLIENTE ---
@app.post("/empresas/cadastro_completo")
def cadastrar_empresa(input: EmpresaCadastroInput):
    with get_conn() as conn:
        # Cria empresa
        c = conn.cursor()
        c.execute("INSERT INTO empresas (nome) VALUES (?)", (input.nome_empresa,))
        empresa_id = c.lastrowid
        # Cria usuário admin_cliente
        try:
            c.execute("""
                INSERT INTO usuarios (nome, email, senha, perfil, empresa_id)
                VALUES (?, ?, ?, ?, ?)
            """, (input.nome_usuario, input.email, input.senha, "admin_cliente", empresa_id))
            conn.commit()
            return {"ok": True, "empresa_id": empresa_id}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Email já cadastrado.")

# --- CADASTRO USUÁRIO ADMIN GERAL (manual: primeiro usuário) ---
@app.post("/usuarios/admin_geral")
def criar_admin_geral(nome: str = Body(...), email: str = Body(...), senha: str = Body(...)):
    with get_conn() as conn:
        try:
            conn.execute("""
                INSERT INTO usuarios (nome, email, senha, perfil)
                VALUES (?, ?, ?, 'admin_geral')
            """, (nome, email, senha))
            conn.commit()
            return {"ok": True}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Email já cadastrado.")

# --- LOGIN ---
@app.post("/login")
def login(email: str = Body(...), senha: str = Body(...)):
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
                "senha": senha  # Apenas para manter no frontend temporariamente!
            }
        else:
            raise HTTPException(status_code=401, detail="Credenciais inválidas.")

# --- CADASTRO DE USUÁRIOS (clientes criam mais usuários depois) ---
@app.post("/usuarios")
def cadastrar_usuario(
    nome: str = Body(...),
    email: str = Body(...),
    senha: str = Body(...),
    perfil: str = Body(...),
    empresa_id: int = Body(...)
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

# --- BUSCA DADOS DA EMPRESA (incluindo dados de conexão) ---
@app.get("/empresas/{empresa_id}")
def dados_empresa(
    empresa_id: int = Path(...),
    email: str = Query(...),
    senha: str = Query(...)
):
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

# --- ATUALIZA DADOS DE CONEXÃO ---
@app.put("/empresas/{empresa_id}/conexao")
def atualizar_conexao(
    empresa_id: int = Path(...),
    conexao: ConexaoInput = Body(...),
    user: dict = Depends(get_current_user)
):
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
            body.tipo_banco, body.host, body.porta,
            body.usuario_banco, body.senha_banco, body.schema,
            empresa_id
        ))
        conn.commit()
    return {"ok": True}

# --- EXEMPLO DE INDICADORES ---
@app.get("/indicadores")
def indicadores(setor: str = Query(...)):
    # Exemplo fictício
    if setor.lower() == "financeiro":
        return {
            "Receitas do mês": 100000,
            "Despesas do mês": 50000,
            "Saldo em Caixa": 50000
        }
    elif setor.lower() == "comercial":
        return {
            "Pedidos fechados": 120,
            "Clientes novos": 15,
            "Ticket médio": 800
        }
    elif setor.lower() == "producao":
        return {
            "Peças produzidas": 6000,
            "Horas trabalhadas": 900,
            "Modelos diferentes": 25
        }
    else:
        return {}

# --- ADMIN: LISTA TODAS AS EMPRESAS E USUÁRIOS ---
@app.get("/admin/empresas")
def listar_empresas(
    email: str = Query(...),
    senha: str = Query(...)
):
    user = get_current_user(email=email, senha=senha)
    if user["perfil"] != "admin_geral":
        raise HTTPException(status_code=403, detail="Acesso negado.")
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, nome, tipo_banco, host, porta, usuario_banco, schema FROM empresas
        """).fetchall()
        return [
            {
                "id": r[0], "nome": r[1], "tipo_banco": r[2], "host": r[3],
                "porta": r[4], "usuario_banco": r[5], "schema": r[6]
            }
            for r in rows
        ]

@app.get("/admin/usuarios")
def listar_usuarios(
    email: str = Query(...),
    senha: str = Query(...)
):
    user = get_current_user(email=email, senha=senha)
    if user["perfil"] != "admin_geral":
        raise HTTPException(status_code=403, detail="Acesso negado.")
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, nome, email, perfil, empresa_id FROM usuarios
        """).fetchall()
        return [
            {
                "id": r[0], "nome": r[1], "email": r[2],
                "perfil": r[3], "empresa_id": r[4]
            }
            for r in rows
        ]
