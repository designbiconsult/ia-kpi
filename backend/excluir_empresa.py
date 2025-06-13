import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute("DELETE FROM empresas WHERE nome = ?", ("NOME_DA_EMPRESA",))
conn.commit()
conn.close()
print("Empresa removida!")
