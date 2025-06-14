from fastapi import FastAPI, HTTPException, Query, Path, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from pydantic import BaseModel
import sqlite3
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

# ==== MODELOS Pydantic =====
class EmpresaInput(BaseModel):
    nome: str

class UsuarioInput(BaseModel):
    nome: str
    email: str
    senha: str
    perfil: str
    empresa_id: int

class ConexaoInput(BaseModel):
    tipo_banco: str
    host: str
    porta: str
    usuario_banco: str
    senha_banco: str
    schema: str

# ==== BANCO ====
def get_conn():
    return sqlite3.connect(DB_PATH)

@app.on_event("startup")
def init_db():
    with get_conn() as conn:
        # Empresas
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
        )""")
        # Usuários
        conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT UNIQUE,
            senha TEXT,
            perfil TEXT,
            empresa_id INTEGER,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id)
        )""")
        # Relacionamentos
        conn.execute("""
        CREATE TABLE IF NOT EXISTS relacionamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tabela_origem TEXT,
            coluna_origem TEXT,
            tabela_destino TEXT,
            coluna_destino TEXT,
            tipo_relacionamento TEXT,
            empresa_id INTEGER
        )""")
        # Tabelas sincronizadas
        conn.execute("""
        CREATE TABLE IF NOT EXISTS tabelas_sincronizadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            nome_tabela TEXT,
            ultima_sincronizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(empresa_id, nome_tabela)
        )""")
        conn.commit()

# ==== AUTENTICAÇÃO E DEPENDÊNCIA ====
def get_current_user(email: Optional[str] = None, senha: Optional[str] = None):
    if not email or not senha:
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, nome, perfil, empresa_id FROM usuarios WHERE email = ? AND senha = ?",
            (email, senha)
        )
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Credenciais inválidas.")
        return {"id": row[0], "nome": row[1], "perfil": row[2], "empresa_id": row[3], "email": email, "senha": senha}

# ==== ROTAS DE EMPRESA E USUÁRIO ====

@app.post("/empresas")
def cadastrar_empresa(dados: Dict):
    nome = dados.get("nome")
    usuario = dados.get("usuario")
    if not nome or not usuario:
        raise HTTPException(status_code=400, detail="Informe nome da empresa e dados do usuário inicial.")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO empresas (nome) VALUES (?)", (nome,))
        empresa_id = c.lastrowid
        c.execute(
            "INSERT INTO usuarios (nome, email, senha, perfil, empresa_id) VALUES (?, ?, ?, ?, ?)",
            (usuario['nome'], usuario['email'], usuario['senha'], "admin_cliente", empresa_id)
        )
        conn.commit()
    return {"ok": True}

@app.post("/usuarios")
def cadastrar_usuario(usuario: UsuarioInput):
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO usuarios (nome, email, senha, perfil, empresa_id) VALUES (?, ?, ?, ?, ?)",
                (usuario.nome, usuario.email, usuario.senha, usuario.perfil, usuario.empresa_id)
            )
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
        row = c.fetchone()
        if row:
            return {
                "id": row[0], "nome": row[1], "perfil": row[2], "empresa_id": row[3],
                "email": email, "senha": senha
            }
        else:
            raise HTTPException(status_code=401, detail="Credenciais inválidas.")

@app.get("/empresas/{empresa_id}")
def get_empresa(empresa_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, nome, tipo_banco, host, porta, usuario_banco, senha_banco, schema FROM empresas WHERE id=?",
            (empresa_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        return {
            "id": row[0], "nome": row[1], "tipo_banco": row[2], "host": row[3], "porta": row[4],
            "usuario_banco": row[5], "senha_banco": row[6], "schema": row[7]
        }

@app.put("/empresas/{empresa_id}/conexao")
def atualizar_conexao(
    empresa_id: int = Path(...),
    conexao: ConexaoInput = Body(...),
    email: str = Query(...),
    senha: str = Query(...)
):
    user = get_current_user(email, senha)
    if user["perfil"] != "admin_geral" and user["empresa_id"] != empresa_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")
    with get_conn() as conn:
        conn.execute("""
            UPDATE empresas SET
                tipo_banco = ?, host = ?, porta = ?, usuario_banco = ?,
                senha_banco = ?, schema = ?
            WHERE id = ?
        """, (
            conexao.tipo_banco, conexao.host, conexao.porta, conexao.usuario_banco,
            conexao.senha_banco, conexao.schema, empresa_id
        ))
        conn.commit()
    return {"ok": True}

# ==== SINCRONISMO DE TABELAS ====

def get_empresa_conexao(empresa_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT tipo_banco, host, porta, usuario_banco, senha_banco, schema FROM empresas WHERE id=?",
            (empresa_id,)
        ).fetchone()
    if not row or not all(row):
        raise HTTPException(status_code=400, detail="Conexão da empresa não configurada.")
    return {
        "tipo_banco": row[0], "host": row[1], "porta": int(row[2]),
        "usuario_banco": row[3], "senha_banco": row[4], "schema": row[5]
    }

@app.get("/sincronismo/tabelas")
def listar_tabelas_sincronismo(
    empresa_id: int = Query(...),
    email: str = Query(...),
    senha: str = Query(...)
):
    user = get_current_user(email, senha)
    if user["perfil"] != "admin_geral" and user["empresa_id"] != empresa_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")
    # Quais já estão sincronizadas?
    with get_conn() as conn:
        res1 = conn.execute("SELECT nome_tabela FROM tabelas_sincronizadas WHERE empresa_id=?", (empresa_id,))
        sincronizadas = [r[0] for r in res1.fetchall()]
    # Buscar do banco remoto
    info = get_empresa_conexao(empresa_id)
    if info["tipo_banco"] != "mysql":
        raise HTTPException(status_code=400, detail="Só MySQL suportado nessa versão.")
    try:
        conn_mysql = pymysql.connect(
            host=info["host"], port=info["porta"], user=info["usuario_banco"], password=info["senha_banco"],
            database=info["schema"], charset='utf8mb4'
        )
        with conn_mysql.cursor() as cur:
            cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = %s""", (info["schema"],))
            resultado_tabelas = [row[0] for row in cur.fetchall()]
            cur.execute("""SELECT table_name FROM information_schema.views WHERE table_schema = %s""", (info["schema"],))
            resultado_views = [row[0] for row in cur.fetchall()]
        conn_mysql.close()
        novas_tabelas = [t for t in (resultado_tabelas + resultado_views) if t not in sincronizadas]
        return {
            "sincronizadas": sincronizadas,
            "novas": novas_tabelas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar MySQL: {str(e)}")

# ==== DEMAIS ENDPOINTS (indicadores, relacionamentos, etc) ficam iguais e você pode seguir evoluindo ====

# Exemplo simples para dashboard:
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

# Você pode adicionar outros endpoints para sincronismo (inserir, atualizar, deletar), relacionamentos, etc.
