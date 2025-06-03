from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from typing import List, Dict

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

@app.on_event("startup")
def init_db():
    with get_conn() as conn:
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

@app.get("/tabelas", response_model=List[str])
def listar_tabelas():
    with get_conn() as conn:
        tabelas = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return [t[0] for t in tabelas if t[0] != 'relacionamentos']

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
