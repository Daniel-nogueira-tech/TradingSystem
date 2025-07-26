import sqlite3, os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def conectar():
    return sqlite3.connect(DB_PATH)


# ============================
# 2️⃣ Primary
# ============================
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


# ============================
# 2️⃣ Secundary
# ============================


def create_table_sec():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS symbol_secundary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE
        )
    """
    )
    conn.commit()
    conn.close()


def salve_or_replace_sec(symbol):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM symbol_secundary")
    cursor.execute("INSERT INTO symbol_secundary (symbol) VALUES (?)", (symbol,))
    conn.commit()
    conn.close()


def symbolo_saved_sec():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol FROM symbol_secundary ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    if result:
        print(f"📦 Símbolo recuperado do banco: {result[0]}")
        return result[0]
    else:
        print("⚠️ Nenhum símbolo encontrado no banco.")
        return None


# ===================
# salva time frame
# ===================
def create_table_timeframe_global(time):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS timeframe_global (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            time TEXT NOT NULL
        )
    """
    )
    cursor.execute(
        """
        INSERT OR REPLACE INTO timeframe_global (id, time)
        VALUES (1, ?)
    """,
        (time,),
    )

    conn.commit()
    conn.close()


# pega os time no banco
def get_timeframe_global():
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT time FROM timeframe_global WHERE id = 1")
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"❌ Erro ao acessar o banco: {e}")
        return None
    finally:
        conn.close()
