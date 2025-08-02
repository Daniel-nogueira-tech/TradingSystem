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


# ===================
# Cria banco de dados para armazenar as classificações de tendência de ativo primario.
# ===================


def create_table_trend_clarifications():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trend_clarifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date INT NOT NULL,
            price REAL NOT NULL,
            type TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


# limpa os dados antigos
def clear_table_trend_clarifications():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trend_clarifications")
    conn.commit()
    conn.close()


def save_trend_clarifications(movimentos):
    conn = conectar()
    cursor = conn.cursor()

    # Cria a tabela, se não existir
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trend_clarifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date INT NOT NULL,
            price REAL NOT NULL,
            type TEXT NOT NULL
        )
    """
    )

    # Limpa os dados antigos
    cursor.execute("DELETE FROM trend_clarifications")

    # Inserção em massa (mais rápido)
    cursor.executemany(
        "INSERT INTO trend_clarifications (date, price, type) VALUES (?, ?, ?)",
        movimentos,
    )

    conn.commit()
    conn.close()


# ===================
# Cria banco de dados para armazenar as classificações de tendência de ativo chave.
# ===================


# cria tabela de classificações
def create_table_trend_clarifications_key():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trend_clarifications_key (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date INT NOT NULL,
            price REAL NOT NULL,
            type TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


# limpa os dados antigos
def clear_table_trend_clarifications_key():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trend_clarifications_key")
    conn.commit()
    conn.close()


def save_trend_clarifications_key(movimentos):
    conn = conectar()
    cursor = conn.cursor()

    # Cria a tabela, se não existir
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trend_clarifications_key (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date INT NOT NULL,
            price REAL NOT NULL,
            type TEXT NOT NULL
        )
    """
    )

    # Limpa os dados antigos
    cursor.execute("DELETE FROM trend_clarifications_key")

    # Inserção em massa (mais rápido)
    cursor.executemany(
        "INSERT INTO trend_clarifications_key (date, price, type) VALUES (?, ?, ?)",
        movimentos,
    )

    conn.commit()
    conn.close()


# ==============================================
# pegar os pontos importantes classificados
################################################
def important_points():
    conn = conectar()
    cursor = conn.cursor()

    # Buscar a última tendência (alta ou baixa)
    cursor.execute(
        """
        SELECT date, price, type 
        FROM trend_clarifications
        WHERE type LIKE 'Tendência Alta%' OR type LIKE 'Tendência Baixa%'
        ORDER BY date DESC 
        LIMIT 1
        """
    )
    trend = cursor.fetchone()

    # Buscar a última Rally Natural (Alta ou topo)
    cursor.execute(
        """SELECT date, price, type
        FROM trend_clarifications
        WHERE type LIKE 'Rally Natural%'
        ORDER BY date DESC
        LIMIT 1
        """
    )
    rally = cursor.fetchone()
    print("Rally encontrado:", rally)
    # Buscar a última Reação Natural (fundo) que ocorreu ANTES da Rally Natural
    reaction = None
    if rally:
        cursor.execute(
            """
            SELECT date, price, type
            FROM trend_clarifications
            WHERE type LIKE 'Reação Natural%'
              AND date <= ?
            ORDER BY date DESC
            LIMIT 1
            """,
            (rally[0],),
        )
        reaction = cursor.fetchone()

    # Buscar a última Reação secundária
    cursor.execute(
        """
     SELECT date, price, type
     FROM trend_clarifications
     WHERE type LIKE 'Reação secundária%'
     ORDER BY date DESC
     LIMIT 1
      """
    )
    secondary_reaction = cursor.fetchone()

    # Buscar a última Rally secundária
    cursor.execute(
        """
     SELECT date, price, type
     FROM trend_clarifications
     WHERE type LIKE 'Rally secundária%'
     ORDER BY date DESC
     LIMIT 1
      """
    )
    secondary_rally = cursor.fetchone()

    # fecha
    conn.close()

    result = {}

    if trend:
        result["Tendência"] = {"date": trend[0], "price": trend[1], "type": trend[2]}

    if reaction:
        result["Rally Natural"] = {
            "date": reaction[0],
            "price": reaction[1],
            "type": reaction[2],
        }
    if secondary_reaction:
        result["Reação secundária"] = {
            "date": secondary_reaction[0],
            "price": secondary_reaction[1],
            "type": secondary_reaction[2],
        }
    if secondary_rally:
        result["Rally secundária"] = {
            "date": secondary_rally[0],
            "price": secondary_rally[1],
            "type": secondary_rally[2],
        }

    return result if result else {"mensagem": "Nenhum ponto encontrado"}


# ======================================================
# pegar os pontos importantes classificados ativo chave
########################################################
def important_points_key():
    conn = conectar()
    cursor = conn.cursor()

    # Buscar a última tendência (alta ou baixa)
    cursor.execute(
        """
        SELECT date, price, type 
        FROM trend_clarifications_key
        WHERE type LIKE 'Tendência Alta%' OR type LIKE 'Tendência Baixa%'
        ORDER BY date DESC 
        LIMIT 1
        """
    )
    trend = cursor.fetchone()

    # Buscar a última Rally Natural (Alta ou topo)
    cursor.execute(
        """
        SELECT date, price, type
        FROM trend_clarifications_key
        WHERE type LIKE 'Rally Natural%'
        ORDER BY date DESC
        LIMIT 1
        """
    )
    rally = cursor.fetchone()
    # Buscar a última Reação Natural (fundo) que ocorreu ANTES da Rally Natural
    reaction = None
    if rally:
        cursor.execute(
            """
            SELECT date, price, type
            FROM trend_clarifications_key
            WHERE type LIKE 'Reação Natural%'
              AND date < ?
            ORDER BY date DESC
            LIMIT 1
            """,
            (rally[0],),
        )
        reaction = cursor.fetchone()

    #############################################

    # Buscar a última Reação secundária
    cursor.execute(
        """
     SELECT date, price, type
     FROM trend_clarifications_key
     WHERE type LIKE 'Reação secundária%'
     ORDER BY date DESC
     LIMIT 1
      """
    )
    secondary_reaction = cursor.fetchone()

    # Buscar a última Rally secundária
    cursor.execute(
        """
     SELECT date, price, type
     FROM trend_clarifications_key
     WHERE type LIKE 'Rally secundária%'
     ORDER BY date DESC
     LIMIT 1
      """
    )
    secondary_rally = cursor.fetchone()
    conn.close()

    # Monta o resultado
    result = {}

    if trend:
        result["Tendência"] = {"date": trend[0], "price": trend[1], "type": trend[2]}
    if reaction:
        result["Rally Natural"] = {
            "date": reaction[0],
            "price": reaction[1],
            "type": reaction[2],
        }
    if secondary_reaction:
        result["Reação secundária"] = {
            "date": secondary_reaction[0],
            "price": secondary_reaction[1],
            "type": secondary_reaction[2],
        }
    if secondary_rally:
        result["Rally secundária"] = {
            "date": secondary_rally[0],
            "price": secondary_rally[1],
            "type": secondary_rally[2],
        }

    return result if result else {"mensagem": "Nenhum ponto encontrado"}


# ======================================================
# salva dados da binance no banco
########################################################
def init_db():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS klines (
            symbol TEXT,
            intervalo TEXT,
            open_time INTEGER,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            close_time INTEGER,
            quote_asset_volume REAL,
            number_of_trades INTEGER,
            taker_buy_base_asset_volume REAL,
            taker_buy_quote_asset_volume REAL,
            PRIMARY KEY (symbol, intervalo, open_time)
        )
        """
    )
    conn.commit()
    conn.close()


def save_klines(conn, symbol, intervalo, klines):
    cursor = conn.cursor()

    dados_completos = [(symbol, intervalo, *k) for k in klines]

    cursor.executemany(
        """
        INSERT OR REPLACE INTO klines (
            symbol, intervalo, open_time, open, high, low, close, volume,
            close_time, quote_asset_volume, number_of_trades,
            taker_buy_base_asset_volume, taker_buy_quote_asset_volume
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        dados_completos,
    )
    conn.commit()


def Delete_all_Klines(symbol, intervalo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM klines WHERE symbol = ? AND intervalo = ?
        """,
        (symbol, intervalo),
    )
    conn.commit()
    conn.close()


def get_data_klines(symbol, intervalo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT open_time, open, high, low, close, volume
        FROM klines
        WHERE symbol = ? AND intervalo = ?
        ORDER BY open_time
        """,
        (symbol, intervalo),
    )
    resultados = cursor.fetchall()
    conn.close()
    return resultados
