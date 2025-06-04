from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from models import (
    get_conn,
    criar_tabelas,
    autenticar_usuario,
    cadastrar_usuario,
    listar_tabelas,
    listar_colunas,
    listar_relacionamentos,
    criar_relacionamento,
    deletar_relacionamento,
    listar_indicadores,
    criar_indicador,
    listar_indicadores_por_usuario,
    sync_dados,
)
import uvicorn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    criar_tabelas()

# ---- Usuários ----

@app.post("/usuarios/login")
def login_usuario(body: Dict):
    email = body.get("email")
    senha = body.get("senha")
    user = autenticar_usuario(email, senha)
    if not user:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")
    return user

@app.post("/usuarios/cadastro")
def cadastro_usuario(body: Dict):
    nome = body.get("nome")
    email = body.get("email")
    senha = body.get("senha")
    return cadastrar_usuario(nome, email, senha)

# ---- Sincronização ----

@app.post("/sync")
def sync(usuario_id: int):
    sync_dados(usuario_id)
    return {"ok": True}

# ---- Tabelas e Colunas ----

@app.get("/tabelas")
def get_tabelas():
    return listar_tabelas()

@app.get("/colunas/{tabela}")
def get_colunas(tabela: str):
    return listar_colunas(tabela)

# ---- Relacionamentos ----

@app.get("/relacionamentos")
def get_rels():
    return listar_relacionamentos()

@app.post("/relacionamentos")
def post_rel(rel: Dict):
    criar_relacionamento(rel)
    return {"ok": True}

@app.delete("/relacionamentos/{rel_id}")
def del_rel(rel_id: int):
    deletar_relacionamento(rel_id)
    return {"ok": True}

# ---- Indicadores ----

@app.get("/indicadores/{usuario_id}/{setor}")
def get_indicadores(usuario_id: int, setor: str):
    return listar_indicadores_por_usuario(usuario_id, setor)

@app.post("/indicadores/{usuario_id}/{setor}")
def post_indicador(usuario_id: int, setor: str, nome: str, mapeamento: str):
    criar_indicador(usuario_id, setor, nome, mapeamento)
    return {"ok": True}

# ---- Pergunta IA ----

@app.post("/pergunta_ia")
def pergunta_ia(request: Request, usuario_id: int, pergunta: str):
    # Aqui você pode plugar o handler do LLM/IA local (chamando uma função ou script externo)
    # Exemplo placeholder:
    resposta = f"IA respondeu (placeholder): '{pergunta}'"
    return {"resposta": resposta}

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
