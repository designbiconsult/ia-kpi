import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()

# Exclui todos os usuários, exceto admin_geral (remova a cláusula WHERE se quiser apagar todos!)
cur.execute("DELETE FROM usuarios WHERE perfil != 'admin_geral' OR perfil IS NULL")

# Exclui todas as tabelas sincronizadas (se a tabela existir)
try:
    cur.execute("DELETE FROM tabelas_sincronizadas")
except Exception as e:
    print("Tabela 'tabelas_sincronizadas' não encontrada ou vazia:", e)

conn.commit()
conn.close()
print("Usuários e tabelas sincronizadas removidos!")
