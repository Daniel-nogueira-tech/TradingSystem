import sqlite3

# Cria um arquivo chamado "database.db" na pasta atual
conn = sqlite3.connect('database.db')

cursor = conn.cursor()

# Criação de uma tabela de exemplo
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
)
''')

conn.commit()
conn.close()

print("Banco de dados criado com sucesso.")
