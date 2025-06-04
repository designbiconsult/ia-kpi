from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List, Dict, Optional

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "database.db"

class UsuarioIn(BaseModel):
    nome: str
    email: str
    senha: str

class UsuarioLogin(BaseModel):
    email: str
    senha: str

class ConfigConexaoIn(BaseModel):
    usuario_id: int
    host: str
    porta: str
    usuario_banco: str
    senha_banco: str
    schema: str
    intervalo_sync: int

class ConfigConexaoOut(BaseModel):
    host: str
    porta: str
    usuario_banco: str
    senha_banco: str
    schema: str
    intervalo_sync: int

class RelacionamentoIn(BaseModel):
    tabela_origem: str
    coluna_origem: str
    tabela_destino: str
    coluna_destino: str
    tipo_relacionamento: str

def get_conn():
    return sqlite3.connect(DB_PATH)

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
            CREATE TABLE IF NOT EXISTS configuracao_conexao (
                usuario_id INTEGER PRIMARY KEY,
                host TEXT,
                porta TEXT,
                usuario_banco TEXT,
                senha_banco TEXT,
                schema TEXT,
                intervalo_sync INTEGER
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

# --- Configuração de Conexão ---
@app.post("/configuracao_conexao")
def salvar_configuracao_conexao(cfg: ConfigConexaoIn):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO configuracao_conexao (usuario_id, host, porta, usuario_banco, senha_banco, schema, intervalo_sync)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(usuario_id) DO UPDATE SET
                host=excluded.host,
                porta=excluded.porta,
                usuario_banco=excluded.usuario_banco,
                senha_banco=excluded.senha_banco,
                schema=excluded.schema,
                intervalo_sync=excluded.intervalo_sync
        """, (cfg.usuario_id, cfg.host, cfg.porta, cfg.usuario_banco, cfg.senha_banco, cfg.schema, cfg.intervalo_sync))
        conn.commit()
    return {"ok": True}

@app.get("/configuracao_conexao/{usuario_id}", response_model=ConfigConexaoOut)
def get_configuracao_conexao(usuario_id: int):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT host, porta, usuario_banco, senha_banco, schema, intervalo_sync FROM configuracao_conexao WHERE usuario_id=?", (usuario_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")
        return ConfigConexaoOut(
            host=row[0],
            porta=row[1],
            usuario_banco=row[2],
            senha_banco=row[3],
            schema=row[4],
            intervalo_sync=row[5]
        )

# --- Tabelas, Colunas e Relacionamentos ---
@app.get("/tabelas", response_model=List[str])
def listar_tabelas():
    with get_conn() as conn:
        tabelas = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return [t[0] for t in tabelas if t[0] not in ('relacionamentos', 'usuarios', 'configuracao_conexao', 'sqlite_sequence')]

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

@app.get("/indicadores")
def listar_indicadores(setor: str = Query(...)):
    if setor.lower() == "financeiro":
        return [
            {"nome": "Receitas do mês", "valor": 0},
            {"nome": "Despesas do mês", "valor": 0},
            {"nome": "Saldo em Caixa", "valor": 0}
        ]
    elif setor.lower() == "comercial":
        return [
            {"nome": "Vendas do mês", "valor": 0},
            {"nome": "Clientes novos", "valor": 0},
            {"nome": "Ticket médio", "valor": 0}
        ]
    elif setor.lower() == "producao":
        return [
            {"nome": "Peças produzidas", "valor": 0},
            {"nome": "Modelos diferentes", "valor": 0},
            {"nome": "Horas trabalhadas", "valor": 0}
        ]
    return []

@app.get("/")
def root():
    return {"status": "ok", "msg": "API IA-KPI backend rodando."}
