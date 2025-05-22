import sqlite3
import os

# Caminho do banco
db_path = "data/database.db"

# Garante que a pasta existe
os.makedirs("data", exist_ok=True)

# Conecta ao banco
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Cria a tabela
cursor.execute("""
CREATE TABLE IF NOT EXISTS estrutura_dinamica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sistema_id TEXT NOT NULL,
    nome_tabela TEXT NOT NULL,
    nome_coluna TEXT NOT NULL,
    tipo_dado TEXT,
    valor_exemplo TEXT,
    descricao_gerada TEXT
)
""")

conn.commit()
conn.close()

print("✅ Tabela 'estrutura_dinamica' criada com sucesso!")
