from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List, Dict

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Em produção, restrinja!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "database.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

# MODELS Pydantic
class UsuarioIn(BaseModel):
    nome: str
    email: str
    senha: str

class LoginIn(BaseModel):
    email: str
    senha: str

class ConexaoIn(BaseModel):
    host: str
    porta: str
    usuario_banco: str
    senha_banco: str
    schema: str

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
                schema TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS relacionamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tabela_origem TEXT,
                coluna_origem TEXT,
                tabela_destino TEXT,
                coluna_destino TEXT,
                tipo_relacionamento TEXT  -- 1:1, 1:N, etc.
            )
        """)
        conn.commit()

@app.post("/usuarios")
def cadastrar_usuario(usuario: UsuarioIn):
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                (usuario.nome, usuario.email, usuario.senha)
            )
            conn.commit()
            return {"ok": True}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Email já cadastrado")

@app.post("/login")
def login(credentials: LoginIn):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
            (credentials.email, credentials.senha)
        )
        user = c.fetchone()
        if user:
            return {
                "id": user[0],
                "nome": user[1],
                "email": user[2],
                "host": user[4],
                "porta": user[5],
                "usuario_banco": user[6],
                "senha_banco": user[7],
                "schema": user[8]
            }
        else:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")

@app.put("/usuarios/{usuario_id}/conexao")
def atualizar_conexao(usuario_id: int, dados: ConexaoIn):
    with get_conn() as conn:
        conn.execute(
            "UPDATE usuarios SET host=?, porta=?, usuario_banco=?, senha_banco=?, schema=? WHERE id=?",
            (
                dados.host,
                dados.porta,
                dados.usuario_banco,
                dados.senha_banco,
                dados.schema,
                usuario_id
            )
        )
        conn.commit()
    return {"ok": True}

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

@app.get("/indicadores")
def indicadores(setor: str = Query(...)):
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