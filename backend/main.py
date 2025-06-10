from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import pymysql
from typing import List, Dict

from models import (
    get_conn,
    buscar_usuario,
    salvar_conexao_usuario,
    listar_tabelas_sqlite,
    listar_colunas_sqlite,
    sync_tabelas_mysql_sqlite,
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Usuário: login/cadastro
@app.post("/usuarios")
def cadastrar_usuario(usuario: Dict):
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                (usuario['nome'], usuario['email'], usuario['senha'])
            )
            conn.commit()
            return {"ok": True}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Email já cadastrado")

@app.post("/login")
def login(credentials: dict = Body(...)):
    user = buscar_usuario(credentials.get("email"), credentials.get("senha"))
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return user

@app.get("/usuarios/{usuario_id}")
def get_usuario(usuario_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT id, nome, email, host, porta, usuario_banco, senha_banco, schema FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return {
            "id": row[0],
            "nome": row[1],
            "email": row[2],
            "host": row[3],
            "porta": row[4],
            "usuario_banco": row[5],
            "senha_banco": row[6],
            "schema": row[7]
        }

@app.put("/usuarios/{usuario_id}/conexao")
def atualizar_conexao(usuario_id: int, dados: dict = Body(...)):
    salvar_conexao_usuario(usuario_id, dados)
    return {"ok": True}

# ----- SINCRONISMO -----

def mysql_conn_from_user(user):
    try:
        conn = pymysql.connect(
            host=user["host"],
            port=int(user.get("porta") or 3306),
            user=user["usuario_banco"],
            password=user["senha_banco"],
            database=user["schema"],
            cursorclass=pymysql.cursors.DictCursor,
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao conectar no MySQL: {e}")

@app.get("/tabelas-remotas")
def tabelas_remotas(usuario_id: int = Query(...)):
    user = get_usuario(usuario_id)
    conn = mysql_conn_from_user(user)
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES;")
            tabelas = [list(row.values())[0] for row in cur.fetchall()]
        return tabelas
    finally:
        conn.close()

@app.post("/sincronizar")
def sincronizar(usuario_id: int = Body(...), tabelas: List[str] = Body(...)):
    user = get_usuario(usuario_id)
    conn_mysql = mysql_conn_from_user(user)
    try:
        sync_tabelas_mysql_sqlite(conn_mysql, tabelas, usuario_id)
        return {"ok": True}
    finally:
        conn_mysql.close()

# ------ SQLite local ------
@app.get("/tabelas", response_model=List[str])
def listar_tabelas_local():
    return listar_tabelas_sqlite()

@app.get("/colunas/{tabela}", response_model=List[str])
def listar_colunas_local(tabela: str):
    return listar_colunas_sqlite(tabela)
