from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from typing import List, Dict, Optional
import pymysql
import datetime
import re

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Ajuste se for publicar
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
                tipo_relacionamento TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tabelas_sincronizadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                nome_tabela TEXT,
                ultima_sincronizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(usuario_id, nome_tabela)
            )
        """)
        conn.commit()

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
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
            (credentials["email"], credentials["senha"])
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

@app.get("/usuarios/{id}")
def get_usuario(id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, nome, email, host, porta, usuario_banco, senha_banco, schema FROM usuarios WHERE id=?",
            (id,)
        ).fetchone()
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

@app.put("/usuarios/{id}/conexao")
def atualizar_conexao(id: int, dados: dict):
    with get_conn() as conn:
        conn.execute(
            "UPDATE usuarios SET host=?, porta=?, usuario_banco=?, senha_banco=?, schema=? WHERE id=?",
            (
                dados.get("host"),
                dados.get("porta"),
                dados.get("usuario_banco"),
                dados.get("senha_banco"),
                dados.get("schema"),
                id
            )
        )
        conn.commit()
    return {"ok": True}

@app.get("/tabelas", response_model=List[str])
def listar_tabelas():
    with get_conn() as conn:
        tabelas = conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')").fetchall()
        return [t[0] for t in tabelas if t[0] not in ['relacionamentos', 'usuarios', 'sqlite_sequence', 'tabelas_sincronizadas']]

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

# ====== NOVO BLOCO DE SINCRONISMO ======

def get_user_mysql_config(usuario_id: int):
    with get_conn() as conn:
        user = conn.execute("SELECT host, porta, usuario_banco, senha_banco, schema FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    host, porta, usuario_banco, senha_banco, schema = user
    if not all([host, porta, usuario_banco, senha_banco, schema]):
        raise HTTPException(status_code=400, detail="Conexão não configurada")
    return host, int(porta), usuario_banco, senha_banco, schema

@app.get("/sincronismo/tabelas")
def listar_tabelas_sincronismo(usuario_id: int = Query(...)):
    with get_conn() as conn:
        res1 = conn.execute("SELECT nome_tabela FROM tabelas_sincronizadas WHERE usuario_id=?", (usuario_id,))
        sincronizadas = [r[0] for r in res1.fetchall()]
    host, porta, usuario_banco, senha_banco, schema = get_user_mysql_config(usuario_id)
    try:
        conn_mysql = pymysql.connect(
            host=host, port=porta, user=usuario_banco, password=senha_banco,
            database=schema, charset='utf8mb4'
        )
        with conn_mysql.cursor() as cur:
            cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = %s""", (schema,))
            resultado_tabelas = [row[0] for row in cur.fetchall()]
            cur.execute("""SELECT table_name FROM information_schema.views WHERE table_schema = %s""", (schema,))
            resultado_views = [row[0] for row in cur.fetchall()]
        conn_mysql.close()
        novas_tabelas = [t for t in (resultado_tabelas + resultado_views) if t not in sincronizadas]
        return {
            "sincronizadas": sincronizadas,
            "novas": novas_tabelas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar MySQL: {str(e)}")

def copy_table_from_mysql_to_sqlite(mysql_conn, sqlite_conn, tabela):
    # Copia estrutura e dados da tabela do MySQL para o SQLite
    with mysql_conn.cursor() as cur:
        cur.execute(f"SHOW CREATE TABLE `{tabela}`")
        create_table_sql = cur.fetchone()[1]

        # Adaptar para SQLite:
        # 1. Substituir ` por "
        create_table_sql = create_table_sql.replace('`', '"')

        # 2. Remove linhas/fragmentos não suportados pelo SQLite
        lines = create_table_sql.splitlines()
        new_lines = []
        for line in lines:
            if any(word in line.upper() for word in ["ENGINE", "CHARSET", "COLLATE", "KEY ", "CONSTRAINT", "AUTO_INCREMENT", "COMMENT", "ZEROFILL"]):
                continue
            line = line.replace("NOT NULL", "")
            line = line.replace("DEFAULT NULL", "")
            line = line.replace("unsigned", "")
            new_lines.append(line)
        create_table_sql = "\n".join(new_lines)

        # Remove vírgula final antes do parêntese (ajuste crítico)
        create_table_sql = re.sub(r',\s*\)', ')', create_table_sql)
        # Remove espaços duplicados
        create_table_sql = re.sub(r'\s+', ' ', create_table_sql)

        # Garante finalização correta
        if not create_table_sql.strip().endswith(");"):
            create_table_sql = create_table_sql.strip()
            if create_table_sql.endswith(")"):
                create_table_sql += ";"
            else:
                create_table_sql += ");"

        # Executa no SQLite
        sqlite_conn.execute(f'DROP TABLE IF EXISTS "{tabela}"')
        try:
            sqlite_conn.execute(create_table_sql)
        except Exception as e:
            print("CREATE TABLE final:", create_table_sql)
            raise e
        sqlite_conn.commit()

        # Copiar dados
        cur.execute(f"SELECT * FROM `{tabela}`")
        rows = cur.fetchall()
        if rows:
            col_names = [desc[0] for desc in cur.description]
            placeholders = ','.join(['?' for _ in col_names])
            sqlite_conn.executemany(
                f'INSERT INTO "{tabela}" ({",".join(col_names)}) VALUES ({placeholders})',
                rows
            )
            sqlite_conn.commit()

@app.post("/sincronismo/sincronizar-novas")
def sincronizar_novas(
    usuario_id: int = Body(...),
    tabelas: List[str] = Body(...)
):
    host, porta, usuario_banco, senha_banco, schema = get_user_mysql_config(usuario_id)
    try:
        conn_mysql = pymysql.connect(
            host=host, port=porta, user=usuario_banco, password=senha_banco,
            database=schema, charset='utf8mb4'
        )
        with get_conn() as sqlite_conn:
            for tabela in tabelas:
                copy_table_from_mysql_to_sqlite(conn_mysql, sqlite_conn, tabela)
                sqlite_conn.execute("""
                    INSERT OR IGNORE INTO tabelas_sincronizadas (usuario_id, nome_tabela)
                    VALUES (?, ?)
                """, (usuario_id, tabela))
            sqlite_conn.commit()
        conn_mysql.close()
        return {"ok": True}
    except Exception as e:
        print("Erro detalhado ao sincronizar:", str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao sincronizar: {str(e)}")

@app.post("/sincronismo/atualizar")
def atualizar_sincronizadas(
    usuario_id: int = Body(...),
    tabelas: List[str] = Body(...)
):
    host, porta, usuario_banco, senha_banco, schema = get_user_mysql_config(usuario_id)
    try:
        conn_mysql = pymysql.connect(
            host=host, port=porta, user=usuario_banco, password=senha_banco,
            database=schema, charset='utf8mb4'
        )
        with get_conn() as sqlite_conn:
            for tabela in tabelas:
                copy_table_from_mysql_to_sqlite(conn_mysql, sqlite_conn, tabela)
                sqlite_conn.execute("""
                    UPDATE tabelas_sincronizadas
                    SET ultima_sincronizacao = CURRENT_TIMESTAMP
                    WHERE usuario_id=? AND nome_tabela=?
                """, (usuario_id, tabela))
            sqlite_conn.commit()
        conn_mysql.close()
        return {"ok": True}
    except Exception as e:
        print("Erro detalhado ao atualizar:", str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {str(e)}")

# ====== FIM DO BLOCO DE SINCRONISMO ======

@app.get("/tabelas-remotas", response_model=List[str])
def tabelas_remotas(usuario_id: int = Query(...)):
    host, porta, usuario_banco, senha_banco, schema = get_user_mysql_config(usuario_id)
    try:
        conn_mysql = pymysql.connect(
            host=host, port=porta, user=usuario_banco, password=senha_banco,
            database=schema, charset='utf8mb4'
        )
        with conn_mysql.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = %s
            """, (schema,))
            resultado_tabelas = [row[0] for row in cur.fetchall()]
            cur.execute("""
                SELECT table_name FROM information_schema.views
                WHERE table_schema = %s
            """, (schema,))
            resultado_views = [row[0] for row in cur.fetchall()]
        conn_mysql.close()
        return resultado_tabelas + resultado_views
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar MySQL: {str(e)}")
    
@app.get("/debug-usuario/{usuario_id}")
def debug_usuario(usuario_id: int):
    with get_conn() as conn:
        user = conn.execute("SELECT host, porta, usuario_banco, senha_banco, schema FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
        return {"user": user}

@app.get("/indicadores")
def indicadores(setor: str = Query(...)):
    # Exemplo simples - ajuste para trazer dos dados do usuário se necessário
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
