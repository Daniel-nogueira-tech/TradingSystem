import sqlite3, os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def conectar():
    return sqlite3.connect(DB_PATH)


def create_table():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS symbol_primary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE
        )
    """
    )
    conn.commit()
    conn.close()


def salve_or_replace(symbol):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM symbol_primary")
    cursor.execute("INSERT INTO symbol_primary (symbol) VALUES (?)", (symbol,))
    conn.commit()
    conn.close()


def symbolo_saved():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol FROM symbol_primary ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    if result:
        print(f"📦 Símbolo recuperado do banco: {result[0]}")
        return result[0]
    else:
        print("⚠️ Nenhum símbolo encontrado no banco.")
        return None
