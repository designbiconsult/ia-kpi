from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List, Dict, Optional

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "database.db"

# --- MODELOS PARA ENTRADA ---
class UsuarioIn(BaseModel):
    nome: str
    email: str
    senha: str

class UsuarioLogin(BaseModel):
    email: str
    senha: str

class RelacionamentoIn(BaseModel):
    tabela_origem: str
    coluna_origem: str
    tabela_destino: str
    coluna_destino: str
    tipo_relacionamento: str

# --- CONEXÃO ---
def get_conn():
    return sqlite3.connect(DB_PATH)

# --- STARTUP: Criação das tabelas necessárias ---
@app.on_event("startup")
def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                email TEXT UNIQUE,
                senha TEXT
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

# --- USUÁRIOS ---
@app.post("/usuarios")
def criar_usuario(usuario: UsuarioIn):
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                (usuario.nome, usuario.email, usuario.senha)
            )
            conn.commit()
            return {"ok": True, "usuario_id": cursor.lastrowid}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Email já cadastrado")

@app.post("/login")
def login(login: UsuarioLogin):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, email FROM usuarios WHERE email = ? AND senha = ?",
            (login.email, login.senha)
        )
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        return {"ok": True, "usuario": {"id": user[0], "nome": user[1], "email": user[2]}}

# --- TABELAS & COLUNAS ---
@app.get("/tabelas", response_model=List[str])
def listar_tabelas():
    with get_conn() as conn:
        tabelas = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return [t[0] for t in tabelas if t[0] not in ('relacionamentos', 'usuarios', 'sqlite_sequence')]

@app.get("/colunas/{tabela}", response_model=List[str])
def listar_colunas(tabela: str):
    with get_conn() as conn:
        cols = conn.execute(f"PRAGMA table_info({tabela})").fetchall()
        return [c[1] for c in cols]

# --- RELACIONAMENTOS ---
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
def criar_relacionamento(rel: RelacionamentoIn):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO relacionamentos (tabela_origem, coluna_origem, tabela_destino, coluna_destino, tipo_relacionamento) VALUES (?, ?, ?, ?, ?)",
            (rel.tabela_origem, rel.coluna_origem, rel.tabela_destino, rel.coluna_destino, rel.tipo_relacionamento)
        )
        conn.commit()
    return {"ok": True}

@app.delete("/relacionamentos/{rel_id}")
def deletar_relacionamento(rel_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM relacionamentos WHERE id=?", (rel_id,))
        conn.commit()
    return {"ok": True}

# --- INDICADORES POR SETOR ---
@app.get("/indicadores")
def listar_indicadores(setor: str = Query(...)):
    # Exemplo de lógica - adapte para buscar dados reais das tabelas sincronizadas
    if setor.lower() == "financeiro":
        # Exemplo estático - troque por consultas reais ao seu banco!
        return [
            {"nome": "Receitas do mês", "valor": 0},
            {"nome": "Despesas do mês", "valor": 0},
            {"nome": "Saldo em Caixa", "valor": 0}
        ]
    elif setor.lower() == "comercial":
        return [
            {"nome": "Vendas do mês", "valor": 0},
            {"nome": "Clientes novos", "valor": 0}
        ]
    # Adicione outros setores conforme necessidade
    return []

# --- HEALTHCHECK (opcional) ---
@app.get("/")
def root():
    return {"status": "ok", "msg": "API IA-KPI backend rodando."}
