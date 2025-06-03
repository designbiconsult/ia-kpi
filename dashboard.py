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

# Criação da tabela de usuários
with sqlite3.connect(DB_PATH, timeout=10) as conn:
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            host TEXT,
            porta TEXT,
            usuario_banco TEXT,
            senha_banco TEXT,
            schema TEXT,
            intervalo_sync INTEGER DEFAULT 60,
            ultimo_sync TEXT
        )
    ''')
    conn.commit()

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

def localizar_coluna(sqlite_path, palavras_chave, preferencia_tipo=None):
    """
    Busca na estrutura_dinamica a primeira coluna que bate com as palavras-chave na descrição ou nome.
    Retorna (tabela, coluna), ou (None, None) se não achar.
    """
    try:
        query = "SELECT tabela, coluna, tipo, descricao FROM estrutura_dinamica"
        df = pd.read_sql(query, sqlite3.connect(sqlite_path))
        for kw in palavras_chave:
            df_filtrado = df[df['descricao'].str.contains(kw, case=False, na=False) | 
                             df['coluna'].str.contains(kw, case=False, na=False)]
            if preferencia_tipo:
                df_filtrado = df_filtrado[df_filtrado['tipo'].str.lower() == preferencia_tipo.lower()]
            if not df_filtrado.empty:
                row = df_filtrado.iloc[0]
                return row['tabela'], row['coluna']
        return None, None
    except Exception as e:
        return None, None

def get_valor_query(sqlite_path, query, fallback="-"):
    try:
        with sqlite3.connect(sqlite_path, timeout=10) as conn:
            df = pd.read_sql(query, conn)
            if not df.empty:
                return df.iloc[0, 0]
            return fallback
    except:
        return fallback

def carregar_indicadores_financeiro(sqlite_path):
    st.subheader("📊 Indicadores Financeiros")
    col1, col2, col3 = st.columns(3)
    if st.session_state["ja_sincronizou"]:
        # Saldos em caixa
        tb_caixa, col_caixa = localizar_coluna(sqlite_path, ["caixa", "cash", "saldo", "balance"], "REAL")
        saldo_caixa = get_valor_query(sqlite_path, f"SELECT SUM({col_caixa}) FROM {tb_caixa}" if tb_caixa and col_caixa else "", "-")

        # Receitas do mês
        tb_receita, col_receita = localizar_coluna(sqlite_path, ["receita", "recebimento", "income", "entrada"], "REAL")
        col_data_receita = localizar_coluna(sqlite_path, ["data", "competencia", "emissao", "entrada", "mes"], "TEXT")[1]
        receitas_mes = "-"
        if tb_receita and col_receita and col_data_receita:
            query = f"""
                SELECT SUM({col_receita}) FROM {tb_receita}
                WHERE strftime('%Y-%m', {col_data_receita}) = strftime('%Y-%m', date('now'))
            """
            receitas_mes = get_valor_query(sqlite_path, query, "-")

        # Despesas do mês
        tb_despesa, col_despesa = localizar_coluna(sqlite_path, ["despesa", "pagamento", "expense", "saida"], "REAL")
        col_data_despesa = localizar_coluna(sqlite_path, ["data", "competencia", "emissao", "pagamento", "mes"], "TEXT")[1]
        despesas_mes = "-"
        if tb_despesa and col_despesa and col_data_despesa:
            query = f"""
                SELECT SUM({col_despesa}) FROM {tb_despesa}
                WHERE strftime('%Y-%m', {col_data_despesa}) = strftime('%Y-%m', date('now'))
            """
            despesas_mes = get_valor_query(sqlite_path, query, "-")

        col1.metric("Saldo em Caixa", f"R$ {saldo_caixa:,}" if saldo_caixa != "-" and saldo_caixa is not None else "-")
        col2.metric("Receitas do Mês", f"R$ {receitas_mes:,}" if receitas_mes != "-" and receitas_mes is not None else "-")
        col3.metric("Despesas do Mês", f"R$ {despesas_mes:,}" if despesas_mes != "-" and despesas_mes is not None else "-")
    else:
        col1.metric("Saldo em Caixa", "-")
        col2.metric("Receitas do Mês", "-")
        col3.metric("Despesas do Mês", "-")
    st.info("Os indicadores financeiros são carregados dinamicamente da base sincronizada.")

def carregar_indicadores_comercial(sqlite_path):
    st.subheader("📊 Indicadores Comerciais")
    col1, col2, col3 = st.columns(3)
    if st.session_state["ja_sincronizou"]:
        # Vendas no mês
        tb_venda, col_venda = localizar_coluna(sqlite_path, ["venda", "sales", "total", "valor"], "REAL")
        col_data_venda = localizar_coluna(sqlite_path, ["data", "emissao", "pedido", "mes"], "TEXT")[1]
        vendas_mes = "-"
        if tb_venda and col_venda and col_data_venda:
            query = f"""
                SELECT SUM({col_venda}) FROM {tb_venda}
                WHERE strftime('%Y-%m', {col_data_venda}) = strftime('%Y-%m', date('now'))
            """
            vendas_mes = get_valor_query(sqlite_path, query, "-")

        # Clientes ativos no mês
        tb_cliente, col_cliente = localizar_coluna(sqlite_path, ["cliente", "customer", "id_cliente"], "INTEGER")
        col_data_cliente = localizar_coluna(sqlite_path, ["data", "emissao", "pedido", "mes"], "TEXT")[1]
        clientes_ativos = "-"
        if tb_venda and col_cliente and col_data_venda:
            query = f"""
                SELECT COUNT(DISTINCT {col_cliente}) FROM {tb_venda}
                WHERE strftime('%Y-%m', {col_data_venda}) = strftime('%Y-%m', date('now'))
            """
            clientes_ativos = get_valor_query(sqlite_path, query, "-")

        # Novos leads no mês
        tb_lead, col_lead = localizar_coluna(sqlite_path, ["lead", "prospec", "contato", "cadastro"], "INTEGER")
        col_data_lead = localizar_coluna(sqlite_path, ["data", "cadastro", "entrada", "mes"], "TEXT")[1]
        novos_leads = "-"
        if tb_lead and col_lead and col_data_lead:
            query = f"""
                SELECT COUNT(*) FROM {tb_lead}
                WHERE strftime('%Y-%m', {col_data_lead}) = strftime('%Y-%m', date('now'))
            """
            novos_leads = get_valor_query(sqlite_path, query, "-")

        col1.metric("Vendas no Mês", f"R$ {vendas_mes:,}" if vendas_mes != "-" and vendas_mes is not None else "-")
        col2.metric("Clientes Ativos", clientes_ativos if clientes_ativos != "-" else "-")
        col3.metric("Novos Leads", novos_leads if novos_leads != "-" else "-")
    else:
        col1.metric("Vendas no Mês", "-")
        col2.metric("Clientes Ativos", "-")
        col3.metric("Novos Leads", "-")
    st.info("Os indicadores comerciais são carregados dinamicamente da base sincronizada.")

def carregar_indicadores_producao(sqlite_path, data_inicio, data_fim):
    try:
        with sqlite3.connect(sqlite_path, timeout=10) as conn:
            try:
                total_modelos = pd.read_sql(f"""
                    SELECT COUNT(DISTINCT PROD.REFERENCIA_PRODUTO) AS total
                    FROM VW_CTO_ORDEM_PRODUCAO_ITEM ITEM
                    JOIN VW_CTO_PRODUTO PROD ON ITEM.CODIGO_INTERNO_PRODUTO = PROD.CODIGO_INTERNO_PRODUTO
                    WHERE ITEM.TIPO_MOVIMENTACAO = 'Produzida'
                      AND ITEM.DATA_MOVIMENTACAO BETWEEN '{data_inicio}' AND '{data_fim}'
                """, conn)["total"][0] or 0
            except:
                total_modelos = 0
            try:
                qtd_produzida = pd.read_sql(f"""
                    SELECT SUM(QTD_MOVIMENTACAO) as total
                    FROM VW_CTO_ORDEM_PRODUCAO_ITEM
                    WHERE TIPO_MOVIMENTACAO = 'Produzida'
                      AND DATA_MOVIMENTACAO BETWEEN '{data_inicio}' AND '{data_fim}'
                """, conn)["total"][0] or 0
            except:
                qtd_produzida = 0
            try:
                produto_top = pd.read_sql(f"""
                    SELECT PROD.DESCRICAO_PRODUTO, SUM(ITEM.QTD_MOVIMENTACAO) as total
                    FROM VW_CTO_ORDEM_PRODUCAO_ITEM ITEM
                    JOIN VW_CTO_PRODUTO PROD ON ITEM.CODIGO_INTERNO_PRODUTO = PROD.CODIGO_INTERNO_PRODUTO
                    WHERE ITEM.TIPO_MOVIMENTACAO = 'Produzida'
                      AND ITEM.DATA_MOVIMENTACAO BETWEEN '{data_inicio}' AND '{data_fim}'
                    GROUP BY PROD.DESCRICAO_PRODUTO
                    ORDER BY total DESC
                    LIMIT 1
                """, conn)
                nome_produto = produto_top["DESCRICAO_PRODUTO"][0] if not produto_top.empty else "Nenhum"
                qtd_produto = produto_top["total"][0] if not produto_top.empty else 0
            except:
                nome_produto = "Nenhum"
                qtd_produto = 0
            try:
                grafico_df = pd.read_sql(f"""
                    SELECT strftime('%Y-%m', DATA_MOVIMENTACAO) as mes, SUM(QTD_MOVIMENTACAO) as total
                    FROM VW_CTO_ORDEM_PRODUCAO_ITEM
                    WHERE TIPO_MOVIMENTACAO = 'Produzida'
                      AND DATA_MOVIMENTACAO BETWEEN '{data_inicio}' AND '{data_fim}'
                    GROUP BY mes
                    ORDER BY mes
                """, conn)
            except:
                grafico_df = pd.DataFrame({"mes":[], "total":[]})

        st.subheader("📊 Indicadores de Produção")
        col1, col2, col3 = st.columns(3)
        col1.metric("Modelos produzidos", total_modelos)
        col2.metric("Total produzido", int(qtd_produzida))
        col3.metric("Mais produzido", f"{nome_produto} ({int(qtd_produto)})")
        st.subheader("📈 Produção por mês no período")
        if not grafico_df.empty:
            fig, ax = plt.subplots()
            ax.bar(grafico_df["mes"], grafico_df["total"])
            ax.set_ylabel("Qtd Produzida")
            ax.set_xlabel("Mês")
            ax.set_title("Produção Mensal")
            st.pyplot(fig)
        else:
            st.info("Não há dados para o período.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar indicadores: {e}")

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

# SIDEBAR UNIVERSAL
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

# LOGIN
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

# CADASTRO
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
    # Botão voltar para login
    if st.button("⬅️ Voltar para Login"):
        st.session_state["pagina"] = "login"
        st.rerun()

# CONEXÃO BANCO
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

# DASHBOARD PRINCIPAL COM SETORES E BUSCA DINÂMICA NO SQLITE
elif st.session_state.get("logado") and st.session_state.get("pagina") == "dashboard":
    st.title(f"🎯 Bem-vindo, {st.session_state['usuario']['nome']}")
    usuario = st.session_state["usuario"]
    st.session_state["mysql_host"] = usuario["host"]
    st.session_state["mysql_port"] = usuario["porta"]
    st.session_state["mysql_user"] = usuario["usuario_banco"]
    st.session_state["mysql_password"] = usuario["senha_banco"]
    st.session_state["mysql_database"] = usuario["schema"]
    st.session_state["sqlite_path"] = f"data/cliente_{usuario['id']}.db"

    setores = ["Financeiro", "Comercial", "Produção"]
    if "setor_ativo" not in st.session_state:
        st.session_state["setor_ativo"] = setores[0]
    st.markdown("### Setores")
    cols = st.columns(len(setores))
    for i, setor in enumerate(setores):
        if cols[i].button(setor, key=f"btn_{setor}"):
            st.session_state["setor_ativo"] = setor

    setor = st.session_state["setor_ativo"]
    if setor == "Financeiro":
        carregar_indicadores_financeiro(st.session_state["sqlite_path"])
    elif setor == "Comercial":
        carregar_indicadores_comercial(st.session_state["sqlite_path"])
    elif setor == "Produção":
        st.subheader("Selecione o período para indicadores de produção")
        hoje = datetime.now().date()
        data_inicio = st.date_input("Data início", value=hoje.replace(day=1), key="dt_inicio_producao")
        data_fim = st.date_input("Data fim", value=hoje, key="dt_fim_producao")
        if data_fim < data_inicio:
            st.error("Data final deve ser igual ou posterior à data inicial.")
        else:
            carregar_indicadores_producao(st.session_state["sqlite_path"], data_inicio, data_fim)

    st.markdown("---")
    st.caption("Desenvolvido para visão de futuro.")

    with st.form("pergunta_form"):
        pergunta = st.text_input("Exemplo: Qual o produto mais produzido em abril de 2025?", key="pergunta_ia")
        submitted = st.form_submit_button("🧠 Consultar IA")
        if submitted and pergunta.strip():
            executar_pergunta(pergunta, st.session_state["sqlite_path"])
