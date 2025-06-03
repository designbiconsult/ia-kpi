import streamlit as st
import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from app.query_handler import executar_pergunta
from sync.sync_db import sync_mysql_to_sqlite, obter_lista_tabelas_views_remotas

DB_PATH = "data/database.db"
os.makedirs("data", exist_ok=True)
st.set_page_config(page_title="IA KPI", layout="wide", initial_sidebar_state="expanded")

#########################
# BANCO: CRIAÇÕES FIXAS #
#########################

def garantir_tabela_indicador_mapeamento(path):
    with sqlite3.connect(path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS indicador_mapeamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                setor TEXT,
                indicador TEXT,
                tabela TEXT,
                coluna_valor TEXT,
                coluna_data TEXT,
                coluna_tipo TEXT,
                valores_entrada TEXT,
                valores_saida TEXT,
                coluna_filtro TEXT,
                valor_filtro TEXT,
                formula_sql TEXT
            )
        ''')
        conn.commit()

def garantir_tabela_relacionamentos(path):
    with sqlite3.connect(path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS relacionamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tabela_origem TEXT,
                coluna_origem TEXT,
                tabela_destino TEXT,
                coluna_destino TEXT,
                tipo_relacionamento TEXT, -- 1:1, 1:N, N:1, N:N
                ativo INTEGER DEFAULT 1
            )
        ''')
        conn.commit()

garantir_tabela_indicador_mapeamento(DB_PATH)
garantir_tabela_relacionamentos(DB_PATH)

###############################
# AUTENTICAÇÃO E SESSION BASE #
###############################

if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "login"
if "ja_sincronizou" not in st.session_state:
    st.session_state["ja_sincronizou"] = False
if "tabelas_marcadas" not in st.session_state:
    st.session_state["tabelas_marcadas"] = {}

def autenticar(email, senha):
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
        return c.fetchone()

def atualizar_usuario_campo(id_usuario, campo, valor):
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        c = conn.cursor()
        c.execute(f"UPDATE usuarios SET {campo} = ? WHERE id = ?", (valor, id_usuario))
        conn.commit()

###############################
# RELACIONAMENTOS AUTOMÁTICOS #
###############################

def detectar_relacionamentos_automaticos(sqlite_path):
    with sqlite3.connect(sqlite_path) as conn:
        tabelas = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)["name"].tolist()
        sugestoes = []
        for i, tabela1 in enumerate(tabelas):
            colunas1 = pd.read_sql(f"PRAGMA table_info({tabela1})", conn)[["name", "type"]]
            for tabela2 in tabelas[i+1:]:
                colunas2 = pd.read_sql(f"PRAGMA table_info({tabela2})", conn)[["name", "type"]]
                colunas_comuns = pd.merge(colunas1, colunas2, on=["name", "type"])
                for _, row in colunas_comuns.iterrows():
                    col = row["name"]
                    # Amostra para sugerir join real
                    df1 = pd.read_sql(f"SELECT DISTINCT {col} FROM {tabela1} LIMIT 10", conn)
                    df2 = pd.read_sql(f"SELECT DISTINCT {col} FROM {tabela2} LIMIT 10", conn)
                    inter = set(df1[col]) & set(df2[col])
                    if not df1.empty and not df2.empty and len(inter) > 0:
                        # Sugere tipo (padrão: N:N, pode ajustar no painel)
                        sugestoes.append({
                            "tabela_origem": tabela1,
                            "coluna_origem": col,
                            "tabela_destino": tabela2,
                            "coluna_destino": col,
                            "tipo_relacionamento": "N:N" # default, admin pode trocar!
                        })
    return sugestoes

def aprovar_relacionamentos(sqlite_path):
    garantir_tabela_relacionamentos(sqlite_path)
    st.subheader("Relacionamentos sugeridos entre tabelas (estilo Power BI)")
    sugestoes = detectar_relacionamentos_automaticos(sqlite_path)
    with sqlite3.connect(sqlite_path) as conn:
        existentes = pd.read_sql("SELECT * FROM relacionamentos WHERE ativo=1", conn)
    for i, s in enumerate(sugestoes):
        ja_existe = (
            (existentes['tabela_origem'] == s['tabela_origem']) & 
            (existentes['coluna_origem'] == s['coluna_origem']) &
            (existentes['tabela_destino'] == s['tabela_destino']) &
            (existentes['coluna_destino'] == s['coluna_destino'])
        ).any()
        if ja_existe:
            st.success(f"Relacionamento já ativo: {s['tabela_origem']}.{s['coluna_origem']} ↔ {s['tabela_destino']}.{s['coluna_destino']}")
            continue
        with st.form(f"form_rel_{i}"):
            st.write(f"Relacionamento sugerido: {s['tabela_origem']}.{s['coluna_origem']} ↔ {s['tabela_destino']}.{s['coluna_destino']}")
            tipo = st.selectbox("Tipo do relacionamento", ["1:1", "1:N", "N:1", "N:N"], index=3, key=f"tipo_rel_{i}")
            aprovar = st.form_submit_button("Aprovar relacionamento")
            if aprovar:
                with sqlite3.connect(sqlite_path) as conn:
                    conn.execute('''
                        INSERT INTO relacionamentos (tabela_origem, coluna_origem, tabela_destino, coluna_destino, tipo_relacionamento, ativo)
                        VALUES (?, ?, ?, ?, ?, 1)
                    ''', (s['tabela_origem'], s['coluna_origem'], s['tabela_destino'], s['coluna_destino'], tipo))
                    conn.commit()
                st.success("Relacionamento aprovado e salvo!")
                st.experimental_rerun()

def montar_relacionamentos_prompt(sqlite_path):
    with sqlite3.connect(sqlite_path) as conn:
        rels = pd.read_sql("SELECT * FROM relacionamentos WHERE ativo=1", conn)
    if rels.empty:
        return ""
    prompt = "\nRelacionamentos disponíveis:\n"
    for _, r in rels.iterrows():
        prompt += f"- {r['tabela_origem']}.{r['coluna_origem']} {r['tipo_relacionamento']} {r['tabela_destino']}.{r['coluna_destino']}\n"
    return prompt

###############################
# INDICADORES E WIZARD        #
###############################

def wizard_mapeamento_indicadores(usuario_id, setor, indicador, sqlite_path, DB_PATH):
    garantir_tabela_indicador_mapeamento(sqlite_path)
    st.info(f"Configuração do indicador: {setor} - {indicador}")
    with sqlite3.connect(sqlite_path) as conn:
        tabelas = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)["name"].tolist()
    tabela = st.selectbox("Tabela:", tabelas, key=f"tb_{setor}_{indicador}")

    colunas = []
    if tabela:
        with sqlite3.connect(sqlite_path) as conn:
            colunas = pd.read_sql(f"PRAGMA table_info({tabela})", conn)["name"].tolist()

    coluna_valor = st.selectbox("Coluna de valor:", colunas, key=f"col_val_{setor}_{indicador}")
    coluna_data = st.selectbox("Coluna de data:", colunas, key=f"col_dt_{setor}_{indicador}")

    coluna_tipo = ""
    valores_entrada = ""
    valores_saida = ""
    formula_sql = ""
    if indicador == "Saldo em Caixa":
        coluna_tipo = st.selectbox("Coluna do tipo de movimento (entrada/saída):", colunas, key=f"col_tipo_{setor}_{indicador}")
        valores_entrada = st.text_input("Valores de ENTRADA (separados por vírgula, ex: RECEBER,ENTRADA):", key=f"val_entrada_{setor}_{indicador}")
        valores_saida = st.text_input("Valores de SAÍDA (separados por vírgula, ex: PAGAR,SAÍDA):", key=f"val_saida_{setor}_{indicador}")
        coluna_filtro = st.selectbox("Coluna de filtro (opcional, ex: BANCO, COFRE):", ["Nenhum"] + colunas, key=f"col_filt_{setor}_{indicador}")
        valor_filtro = ""
        if coluna_filtro != "Nenhum":
            valor_filtro = st.text_input("Valor do filtro (opcional, ex: BANCO1):", key=f"val_filt_{setor}_{indicador}")
        formula_sql = ""
    else:
        coluna_tipo = st.selectbox("Coluna do tipo de movimento (opcional):", ["Nenhum"] + colunas, key=f"col_tipo_{setor}_{indicador}")
        valores_entrada = st.text_input("Valores para considerar (opcional, ex: RECEBER):", key=f"val_entrada_{setor}_{indicador}")
        valores_saida = ""
        coluna_filtro = st.selectbox("Coluna de filtro (opcional):", ["Nenhum"] + colunas, key=f"col_filt_{setor}_{indicador}")
        valor_filtro = ""
        if coluna_filtro != "Nenhum":
            valor_filtro = st.text_input("Valor do filtro (opcional):", key=f"val_filt_{setor}_{indicador}")
        formula_sql = ""

    if st.button("Salvar indicador", key=f"save_{setor}_{indicador}"):
        garantir_tabela_indicador_mapeamento(sqlite_path)
        with sqlite3.connect(sqlite_path) as conn:
            conn.execute(
                "INSERT INTO indicador_mapeamento (usuario_id, setor, indicador, tabela, coluna_valor, coluna_data, coluna_tipo, valores_entrada, valores_saida, coluna_filtro, valor_filtro, formula_sql) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (usuario_id, setor, indicador, tabela, coluna_valor, coluna_data,
                 coluna_tipo if coluna_tipo != "Nenhum" else None,
                 valores_entrada, valores_saida,
                 coluna_filtro if coluna_filtro != "Nenhum" else None, valor_filtro or None,
                 formula_sql)
            )
            conn.commit()
        st.success("Indicador configurado!")
        st.experimental_rerun()

def carregar_indicador_configurado(usuario_id, setor, indicador, periodo, sqlite_path, DB_PATH):
    garantir_tabela_indicador_mapeamento(sqlite_path)
    with sqlite3.connect(sqlite_path) as conn:
        row = conn.execute(
            "SELECT tabela, coluna_valor, coluna_data, coluna_tipo, valores_entrada, valores_saida, coluna_filtro, valor_filtro, formula_sql FROM indicador_mapeamento WHERE usuario_id=? AND setor=? AND indicador=?",
            (usuario_id, setor, indicador)
        ).fetchone()
    if not row:
        st.warning(f"Mapeamento não encontrado para {setor} - {indicador}. Preencha o mapeamento abaixo para continuar.")
        st.markdown("---")
        wizard_mapeamento_indicadores(usuario_id, setor, indicador, sqlite_path, DB_PATH)
        st.stop()
        return "-"
    tabela, col_valor, col_data, col_tipo, vals_entrada, vals_saida, col_filtro, val_filtro, formula_sql = row
    if formula_sql:
        sql = formula_sql
    elif indicador == "Saldo em Caixa":
        condicoes = [f"strftime('%Y-%m', {col_data}) <= '{periodo}'"]
        if col_filtro and val_filtro:
            condicoes.append(f"{col_filtro} = '{val_filtro}'")
        entrada_list = [v.strip() for v in (vals_entrada or "").split(",") if v.strip()]
        saida_list = [v.strip() for v in (vals_saida or "").split(",") if v.strip()]
        cases = []
        if entrada_list:
            entries = ", ".join([f"'{v}'" for v in entrada_list])
            cases.append(f"WHEN {col_tipo} IN ({entries}) THEN {col_valor}")
        if saida_list:
            exits = ", ".join([f"'{v}'" for v in saida_list])
            cases.append(f"WHEN {col_tipo} IN ({exits}) THEN -1*{col_valor}")
        cases.append("ELSE 0")
        sql = f"""
            SELECT SUM(CASE
                {' '.join(cases)}
            END) as saldo
            FROM {tabela}
            WHERE {' AND '.join(condicoes)}
        """
    else:
        condicoes = [f"strftime('%Y-%m', {col_data}) = '{periodo}'"]
        if col_tipo and vals_entrada:
            entradas = ", ".join([f"'{v.strip()}'" for v in vals_entrada.split(",") if v.strip()])
            condicoes.append(f"{col_tipo} IN ({entradas})")
        if col_filtro and val_filtro:
            condicoes.append(f"{col_filtro} = '{val_filtro}'")
        sql = f"SELECT SUM({col_valor}) FROM {tabela} WHERE {' AND '.join(condicoes)}"
    try:
        with sqlite3.connect(sqlite_path) as conn:
            df = pd.read_sql(sql, conn)
            if not df.empty:
                return df.iloc[0, 0] or 0
            return 0
    except Exception as e:
        st.error(f"Erro ao buscar indicador: {e}")
        return "-"

def exibir_indicadores_basicos(usuario_id, setor, indicadores, sqlite_path, DB_PATH):
    garantir_tabela_indicador_mapeamento(sqlite_path)
    periodo = datetime.now().strftime('%Y-%m')
    colunas = st.columns(len(indicadores))
    for i, indicador in enumerate(indicadores):
        valor = carregar_indicador_configurado(usuario_id, setor, indicador, periodo, sqlite_path, DB_PATH)
        colunas[i].metric(indicador, valor)

def excluir_tabelas_sqlite(sqlite_path, tabelas_excluir):
    try:
        with sqlite3.connect(sqlite_path, timeout=10) as conn:
            c = conn.cursor()
            for tabela in tabelas_excluir:
                c.execute(f"DROP TABLE IF EXISTS `{tabela}`")
            conn.commit()
        st.success(f"Tabela(s) excluída(s) com sucesso: {', '.join(tabelas_excluir)}")
    except Exception as e:
        st.error(f"Erro ao excluir tabela(s): {e}")

###################################
# INTERFACE                       #
###################################

if st.session_state.get("logado"):
    with st.sidebar:
        st.markdown("---")
        if st.button("⚙️ Configurar conexão"):
            st.session_state["pagina"] = "conexao"
            st.rerun()
        if st.button("Sair"):
            st.session_state["logado"] = False
            st.session_state["pagina"] = "login"
            st.session_state["ja_sincronizou"] = False
            st.rerun()
        st.markdown("---")
        if st.button("🔗 Configurar relacionamentos (admin)"):
            st.session_state["pagina"] = "relacionamentos"
            st.rerun()
        st.subheader("Excluir tabelas locais:")
        sqlite_path = st.session_state.get("sqlite_path", None)
        if sqlite_path and os.path.exists(sqlite_path):
            with sqlite3.connect(sqlite_path) as conn:
                tabelas = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)["name"].tolist()
            if tabelas:
                tabelas_excluir = []
                for tb in tabelas:
                    if st.checkbox(f"Excluir '{tb}'", key=f"excluir_{tb}"):
                        tabelas_excluir.append(tb)
                if st.button("Excluir selecionadas"):
                    if tabelas_excluir:
                        excluir_tabelas_sqlite(sqlite_path, tabelas_excluir)
                        st.experimental_rerun()
                    else:
                        st.info("Nenhuma tabela marcada para exclusão.")
            else:
                st.info("Nenhuma tabela para excluir.")
        else:
            st.info("Banco local ainda não sincronizado.")

if st.session_state["pagina"] == "login" and not st.session_state["logado"]:
    st.title("🔐 Login IA KPI")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        usuario = autenticar(email, senha)
        if usuario:
            st.session_state["logado"] = True
            st.session_state["usuario"] = {
                "id": usuario[0],
                "nome": usuario[1],
                "email": usuario[2],
                "host": usuario[4],
                "porta": usuario[5],
                "usuario_banco": usuario[6],
                "senha_banco": usuario[7],
                "schema": usuario[8],
                "intervalo_sync": usuario[9] or 60,
                "ultimo_sync": usuario[10]
            }
            st.session_state["mysql_host"] = usuario[4]
            st.session_state["mysql_port"] = usuario[5]
            st.session_state["mysql_user"] = usuario[6]
            st.session_state["mysql_password"] = usuario[7]
            st.session_state["mysql_database"] = usuario[8]
            st.session_state["sqlite_path"] = f"data/cliente_{usuario[0]}.db"
            garantir_tabela_indicador_mapeamento(st.session_state["sqlite_path"])
            garantir_tabela_relacionamentos(st.session_state["sqlite_path"])
            st.session_state["pagina"] = "dashboard"
            st.session_state["ja_sincronizou"] = False
            st.rerun()
        else:
            st.error("Credenciais inválidas.")
    st.markdown("---")
    st.markdown("Ainda não possui cadastro?")
    if st.button("👉 Cadastre-se aqui"):
        st.session_state["pagina"] = "cadastro"
        st.rerun()

elif st.session_state["pagina"] == "cadastro" and not st.session_state["logado"]:
    st.title("📊 Cadastro de Cliente IA KPI")
    with st.form("cadastro_form"):
        nome = st.text_input("Nome completo")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Cadastrar")
        if submitted:
            if not (nome and email and senha):
                st.error("Preencha todos os campos.")
            else:
                with sqlite3.connect(DB_PATH, timeout=10) as conn:
                    c = conn.cursor()
                    try:
                        c.execute(
                            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                            (nome, email, senha)
                        )
                        conn.commit()
                        st.success("Cadastro realizado com sucesso! Faça login para continuar.")
                        st.session_state["pagina"] = "login"
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Este email já está cadastrado.")
    if st.button("⬅️ Voltar para Login"):
        st.session_state["pagina"] = "login"
        st.rerun()

elif st.session_state.get("pagina") == "relacionamentos":
    st.title("🔗 Aprovar relacionamentos entre tabelas (admin)")
    aprovar_relacionamentos(st.session_state["sqlite_path"])
    st.markdown("---")
    if st.button("⬅️ Voltar"):
        st.session_state["pagina"] = "dashboard"
        st.rerun()

elif st.session_state.get("pagina") == "conexao":
    st.title("⚙️ Configuração da conexão com o banco")
    usuario = st.session_state["usuario"]
    with st.form("form_conexao_edit"):
        host = st.text_input("Host do banco", value=usuario.get("host") or "")
        porta = st.text_input("Porta", value=usuario.get("porta") or "3306")
        usuario_banco = st.text_input("Usuário do banco", value=usuario.get("usuario_banco") or "")
        senha_banco = st.text_input("Senha", value=usuario.get("senha_banco") or "", type="password")
        schema = st.text_input("Schema", value=usuario.get("schema") or "")
        intervalo_sync = st.selectbox("Intervalo de sincronização (min):", [5,10,15,30,60,120,240,1440], index=4)
        submitted = st.form_submit_button("Salvar conexão")
        if submitted:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                c = conn.cursor()
                c.execute(
                    "UPDATE usuarios SET host = ?, porta = ?, usuario_banco = ?, senha_banco = ?, schema = ?, intervalo_sync = ? WHERE id = ?",
                    (host, porta, usuario_banco, senha_banco, schema, intervalo_sync, usuario["id"])
                )
                conn.commit()
            st.session_state["usuario"].update({
                "host": host,
                "porta": porta,
                "usuario_banco": usuario_banco,
                "senha_banco": senha_banco,
                "schema": schema,
                "intervalo_sync": intervalo_sync
            })
            st.session_state["mysql_host"] = host
            st.session_state["mysql_port"] = porta
            st.session_state["mysql_user"] = usuario_banco
            st.session_state["mysql_password"] = senha_banco
            st.session_state["mysql_database"] = schema
            st.session_state["sqlite_path"] = f"data/cliente_{usuario['id']}.db"
            st.session_state["ja_sincronizou"] = False
            st.success("Conexão salva com sucesso!")
            st.session_state["pagina"] = "dashboard"
            st.rerun()
    if st.button("⬅️ Voltar para Dashboard"):
        st.session_state["pagina"] = "dashboard"
        st.rerun()

elif st.session_state.get("pagina") == "dashboard_sync":
    usuario = st.session_state["usuario"]
    id_usuario = usuario["id"]
    sqlite_path = st.session_state["sqlite_path"]
    tabelas_disponiveis = obter_lista_tabelas_views_remotas()
    st.title("Sincronizar tabelas/views do banco")
    if not st.session_state["tabelas_marcadas"] or set(st.session_state["tabelas_marcadas"].keys()) != set(tabelas_disponiveis):
        st.session_state["tabelas_marcadas"] = {tb: False for tb in tabelas_disponiveis}
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Selecionar todas"):
            for tb in tabelas_disponiveis:
                st.session_state["tabelas_marcadas"][tb] = True
    with col2:
        if st.button("Desmarcar todas"):
            for tb in tabelas_disponiveis:
                st.session_state["tabelas_marcadas"][tb] = False
    for tb in tabelas_disponiveis:
        st.session_state["tabelas_marcadas"][tb] = st.checkbox(
            tb,
            value=st.session_state["tabelas_marcadas"][tb],
            key=f"chk_{tb}"
        )
    tabelas_sync = [tb for tb, marcado in st.session_state["tabelas_marcadas"].items() if marcado]
    bcol1, bcol2 = st.columns([1,1])
    with bcol1:
        if st.button("Confirmar e sincronizar"):
            if tabelas_sync:
                sync_mysql_to_sqlite(tabelas_sync)
                novo_sync = datetime.now().isoformat()
                atualizar_usuario_campo(id_usuario, "ultimo_sync", novo_sync)
                st.session_state["usuario"]["ultimo_sync"] = novo_sync
                st.success("Dados atualizados automaticamente!")
                st.session_state["ja_sincronizou"] = True
                st.session_state["pagina"] = "dashboard"
                st.rerun()
            else:
                st.warning("Selecione ao menos uma tabela.")
    with bcol2:
        if st.button("Pular sincronização"):
            st.session_state["ja_sincronizou"] = True
            st.session_state["pagina"] = "dashboard"
            st.rerun()
    st.stop()

elif st.session_state.get("logado") and st.session_state.get("pagina") == "dashboard":
    st.title(f"🎯 Bem-vindo, {st.session_state['usuario']['nome']}")
    usuario = st.session_state["usuario"]
    usuario_id = usuario["id"]
    st.session_state["mysql_host"] = usuario["host"]
    st.session_state["mysql_port"] = usuario["porta"]
    st.session_state["mysql_user"] = usuario["usuario_banco"]
    st.session_state["mysql_password"] = usuario["senha_banco"]
    st.session_state["mysql_database"] = usuario["schema"]
    st.session_state["sqlite_path"] = f"data/cliente_{usuario['id']}.db"
    garantir_tabela_indicador_mapeamento(st.session_state["sqlite_path"])
    garantir_tabela_relacionamentos(st.session_state["sqlite_path"])
    if st.button("🔄 Sincronizar agora"):
        st.session_state["pagina"] = "dashboard_sync"
        st.rerun()
    setores = {
        "Financeiro": ["Receitas do mês", "Despesas do mês", "Saldo em Caixa"],
        "Comercial": ["Vendas no mês", "Clientes Ativos", "Novos Leads"],
        "Produção": ["Produção do mês", "Modelos produzidos", "Mais produzido"]
    }
    if "setor_ativo" not in st.session_state:
        st.session_state["setor_ativo"] = list(setores.keys())[0]
    cols = st.columns(len(setores))
    for i, setor in enumerate(setores):
        if cols[i].button(setor, key=f"btn_{setor}"):
            st.session_state["setor_ativo"] = setor
    setor = st.session_state["setor_ativo"]
    exibir_indicadores_basicos(usuario_id, setor, setores[setor], st.session_state["sqlite_path"], DB_PATH)
    st.markdown("---")
    st.caption("Desenvolvido para visão de futuro.")
    with st.form("pergunta_form"):
        pergunta = st.text_input("Exemplo: Qual o produto mais produzido em abril de 2025?", key="pergunta_ia")
        submitted = st.form_submit_button("🧠 Consultar IA")
        if submitted and pergunta.strip():
            executar_pergunta(pergunta, st.session_state["sqlite_path"])
