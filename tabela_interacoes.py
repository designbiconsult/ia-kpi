import sqlite3
import os

# Garante que a pasta exista
os.makedirs("data", exist_ok=True)

# Caminho do banco
db_path = "data/database.db"

# Conecta ao banco
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Cria a tabela
cursor.execute("""
CREATE TABLE IF NOT EXISTS interacoes_usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    pergunta TEXT NOT NULL,
    pergunta_refinada TEXT,
    resposta_ia TEXT,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("✅ Tabela interacoes_usuario criada com sucesso.")
