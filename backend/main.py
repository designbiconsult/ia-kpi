from fastapi import FastAPI, HTTPException, Depends, Body, Path
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from typing import List, Dict

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
                empresa_id INTEGER,
                perfil TEXT NOT NULL,
                ativo INTEGER DEFAULT 1,
                FOREIGN KEY (empresa_id) REFERENCES empresas(id)
            )
        """)
        conn.commit()
        # Cria admin_geral se não houver nenhum
        cur = conn.cursor()
        cur.execute("SELECT id FROM usuarios WHERE perfil='admin_geral'")
        if not cur.fetchone():
            conn.execute("""
                INSERT INTO usuarios (nome, email, senha, empresa_id, perfil, ativo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "Admin Geral", "admin@empresa.com", "123", None, "admin_geral", 1
            ))
            conn.commit()

# Autenticação simples
def get_current_user(email=Body(...), senha=Body(...)):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, nome, email, empresa_id, perfil, ativo FROM usuarios WHERE email=? AND senha=?", (email, senha))
        row = cur.fetchone()
        if not row or row[5] != 1:
            raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
        return {"id": row[0], "nome": row[1], "email": row[2], "empresa_id": row[3], "perfil": row[4]}

@app.post("/login")
def login(data: Dict = Body(...)):
    user = get_current_user(data["email"], data["senha"])
    return user

# Cadastro completo: empresa + primeiro usuário admin_cliente (NÃO precisa autenticação)
@app.post("/empresas/cadastro_completo")
def cadastrar_empresa_com_usuario(dados: Dict = Body(...)):
    with get_conn() as conn:
        cur = conn.cursor()
        # Cria empresa
        cur.execute("""
            INSERT INTO empresas (nome, tipo_banco, host, porta, usuario_banco, senha_banco, schema)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            dados["nome_empresa"], dados.get("tipo_banco"), dados.get("host"), dados.get("porta"),
            dados.get("usuario_banco"), dados.get("senha_banco"), dados.get("schema")
        ))
        empresa_id = cur.lastrowid
        # Cria usuário admin_cliente dessa empresa
        try:
            cur.execute("""
                INSERT INTO usuarios (nome, email, senha, empresa_id, perfil, ativo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dados["nome_usuario"], dados["email"], dados["senha"], empresa_id, "admin_cliente", 1
            ))
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="E-mail já cadastrado")
        conn.commit()
    return {"ok": True, "empresa_id": empresa_id}

# ----- Listar empresas (apenas admin_geral) -----
@app.get("/empresas")
def listar_empresas(user: dict = Depends(get_current_user)):
    if user["perfil"] != "admin_geral":
        raise HTTPException(status_code=403, detail="Acesso restrito (admin geral)")
    with get_conn() as conn:
        rows = conn.execute("SELECT id, nome, tipo_banco, host, porta, usuario_banco, schema FROM empresas").fetchall()
        return [
            dict(
                id=r[0], nome=r[1], tipo_banco=r[2], host=r[3], porta=r[4],
                usuario_banco=r[5], schema=r[6]
            ) for r in rows
        ]

# ----- Atualizar empresa (apenas admin_geral) -----
@app.put("/empresas/{empresa_id}")
def atualizar_empresa(
    empresa_id: int = Path(...),
    dados: Dict = Body(...),
    user: dict = Depends(get_current_user)
):
    if user["perfil"] != "admin_geral":
        raise HTTPException(status_code=403, detail="Acesso restrito (admin geral)")
    with get_conn() as conn:
        conn.execute("""
            UPDATE empresas SET
                nome = ?,
                tipo_banco = ?,
                host = ?,
                porta = ?,
                usuario_banco = ?,
                senha_banco = ?,
                schema = ?
            WHERE id = ?
        """, (
            dados["nome"], dados.get("tipo_banco"), dados.get("host"), dados.get("porta"),
            dados.get("usuario_banco"), dados.get("senha_banco"), dados.get("schema"),
            empresa_id
        ))
        conn.commit()
    return {"ok": True}

# ----- Cadastro de usuário (apenas autenticado admin_geral ou admin_cliente) -----
@app.post("/usuarios")
def cadastrar_usuario(dados: Dict = Body(...), user: dict = Depends(get_current_user)):
    if user["perfil"] not in ["admin_geral", "admin_cliente"]:
        raise HTTPException(status_code=403, detail="Acesso restrito")
    empresa_id = dados.get("empresa_id") or user["empresa_id"]
    if user["perfil"] == "admin_cliente" and empresa_id != user["empresa_id"]:
        raise HTTPException(status_code=403, detail="Só pode cadastrar usuário da sua empresa")
    with get_conn() as conn:
        try:
            conn.execute("""
                INSERT INTO usuarios (nome, email, senha, empresa_id, perfil)
                VALUES (?, ?, ?, ?, ?)
            """, (
                dados["nome"], dados["email"], dados["senha"], empresa_id, dados.get("perfil", "user")
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
    return {"ok": True}

# ----- Listar usuários (admin_geral vê todos, admin_cliente só da própria empresa) -----
@app.get("/usuarios")
def listar_usuarios(user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        if user["perfil"] == "admin_geral":
            rows = conn.execute("SELECT id, nome, email, empresa_id, perfil, ativo FROM usuarios").fetchall()
        else:
            rows = conn.execute("SELECT id, nome, email, empresa_id, perfil, ativo FROM usuarios WHERE empresa_id=?", (user["empresa_id"],)).fetchall()
        return [dict(id=r[0], nome=r[1], email=r[2], empresa_id=r[3], perfil=r[4], ativo=r[5]) for r in rows]

# ----- Dashboard administrativo básico -----
@app.get("/admin/dashboard")
def dashboard_admin(user: dict = Depends(get_current_user)):
    if user["perfil"] != "admin_geral":
        raise HTTPException(status_code=403, detail="Acesso restrito (admin geral)")
    with get_conn() as conn:
        empresas = conn.execute("SELECT COUNT(*) FROM empresas").fetchone()[0]
        usuarios = conn.execute("SELECT COUNT(*) FROM usuarios WHERE perfil != 'admin_geral'").fetchone()[0]
        ativos = conn.execute("SELECT COUNT(*) FROM usuarios WHERE ativo = 1 AND perfil != 'admin_geral'").fetchone()[0]
    return {
        "empresas": empresas,
        "usuarios": usuarios,
        "usuarios_ativos": ativos
    }

@app.post("/sincronismo")
def sincronizar(user: dict = Depends(get_current_user)):
    if user["perfil"] not in ["admin_geral", "admin_cliente"]:
        raise HTTPException(status_code=403, detail="Acesso restrito")
    # Aqui ficaria a lógica de sincronismo para o banco da empresa do user
    return {"ok": True, "empresa_id": user["empresa_id"]}

@app.get("/indicadores")
def consultar_indicadores(user: dict = Depends(get_current_user)):
    return {
        "empresa_id": user["empresa_id"],
        "indicadores": [
            {"nome": "Receitas", "valor": 10000},
            {"nome": "Despesas", "valor": 5000},
        ]
    }
