import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()
# Adiciona as colunas se ainda não existem
try:
    cur.execute("ALTER TABLE usuarios ADD COLUMN empresa_id INTEGER;")
except Exception as e:
    print("empresa_id:", e)
try:
    cur.execute("ALTER TABLE usuarios ADD COLUMN perfil TEXT;")
except Exception as e:
    print("perfil:", e)
try:
    cur.execute("ALTER TABLE usuarios ADD COLUMN ativo INTEGER DEFAULT 1;")
except Exception as e:
    print("ativo:", e)

# Atualiza seu usuário para admin_geral e ativo
cur.execute("UPDATE usuarios SET perfil='admin_geral', ativo=1 WHERE email='julian@designbi.com.br';")
conn.commit()
conn.close()
print("Banco de dados ajustado com sucesso!")
