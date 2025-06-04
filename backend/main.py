from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import sqlite3

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "database.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

# MODELS
class UsuarioModel(BaseModel):
    nome: str
    email: str
    senha: str

class ConexaoModel(BaseModel):
    host: str
    porta: str
    usuario_banco: str
    senha_banco: str
    schema: str
    intervalo_sync: int

class LoginModel(BaseModel):
    email: str
    senha: str

# INIT DB
@app.on_event("startup")
def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                email TEXT UNIQUE,
                senha TEXT,
                host TEXT,
                porta TEXT,
                usuario_banco TEXT,
                senha_banco TEXT,
                schema TEXT,
                intervalo_sync INTEGER DEFAULT 60
            )
        """)
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
        conn.commit()

# ROTAS USUÁRIOS
@app.post("/usuarios")
def criar_usuario(usuario: UsuarioModel):
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                (usuario.nome, usuario.email, usuario.senha)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
    return {"ok": True}

@app.post("/login")
def login(login: LoginModel):
    with get_conn() as conn:
        user = conn.execute(
            "SELECT id, nome, email, host, porta, usuario_banco, senha_banco, schema, intervalo_sync FROM usuarios WHERE email=? AND senha=?",
            (login.email, login.senha)
        ).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        return {
            "id": user[0],
            "nome": user[1],
            "email": user[2],
            "host": user[3],
            "porta": user[4],
            "usuario_banco": user[5],
            "senha_banco": user[6],
            "schema": user[7],
            "intervalo_sync": user[8]
        }

@app.put("/usuarios/{usuario_id}/conexao")
def atualizar_conexao(usuario_id: int, conexao: ConexaoModel):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            UPDATE usuarios
            SET host=?, porta=?, usuario_banco=?, senha_banco=?, schema=?, intervalo_sync=?
            WHERE id=?
            """,
            (
                conexao.host, conexao.porta, conexao.usuario_banco, conexao.senha_banco,
                conexao.schema, conexao.intervalo_sync, usuario_id
            )
        )
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        conn.commit()
    return {"ok": True}

# ROTAS RELACIONAMENTOS
@app.get("/tabelas", response_model=List[str])
def listar_tabelas():
    with get_conn() as conn:
        tabelas = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return [t[0] for t in tabelas if t[0] not in ['relacionamentos', 'usuarios', 'sqlite_sequence']]

@app.get("/colunas/{tabela}", response_model=List[str])
def listar_colunas(tabela: str):
    with get_conn() as conn:
        cols = conn.execute(f"PRAGMA table_info({tabela})").fetchall()
        return [c[1] for c in cols]

@app.get("/relacionamentos", response_model=List[Dict])
def get_relacionamentos():
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

@app.post("/relacionamentos")
def criar_relacionamento(rel: Dict):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO relacionamentos (tabela_origem, coluna_origem, tabela_destino, coluna_destino, tipo_relacionamento) VALUES (?, ?, ?, ?, ?)",
            (rel['tabela_origem'], rel['coluna_origem'], rel['tabela_destino'], rel['coluna_destino'], rel['tipo_relacionamento'])
        )
        conn.commit()
    return {"ok": True}

@app.delete("/relacionamentos/{rel_id}")
def deletar_relacionamento(rel_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM relacionamentos WHERE id=?", (rel_id,))
        conn.commit()
    return {"ok": True}
