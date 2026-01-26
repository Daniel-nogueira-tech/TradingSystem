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


# ===================
# salva time frame global
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


# ====================================================================================
# Cria banco de dados para armazenar as classificações de tendência de ativo primario.
# ====================================================================================
# Criação única da tabela (roda uma vez no setup ou no início)
def create_table_trend_clarifications():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trend_clarifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date INT NOT NULL,
            price REAL NOT NULL,
            type TEXT NOT NULL,
            atr REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# Limpa todos os dados (opcional, se for sobrescrever)
def clear_table_trend_clarifications():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trend_clarifications")
    conn.commit()
    conn.close()


# Salva os dados classificados
def save_trend_clarifications(movimentos):
    conn = conectar()
    cursor = conn.cursor()

    cursor.executemany(
        """
        INSERT INTO trend_clarifications (date, price, type, atr )
        VALUES (?, ?, ?, ?)
        """,
        movimentos,
    )

    conn.commit()
    conn.close()


# Pega dados salvos para simular
def get_trend_clarifications():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, price, type, atr FROM trend_clarifications ORDER BY date ASC"
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


# ==============================================
# pegar os pontos importantes classificados
################################################
# variável global

ultimo_resultado = None


def important_points():
    global ultimo_resultado

    conn = conectar()
    cursor = conn.cursor()

    # Buscar a última tendência
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

    # Buscar a última Rally Natural
    cursor.execute(
        """SELECT date, price, type
        FROM trend_clarifications
        WHERE type LIKE 'Rally Natural%'
        ORDER BY date DESC
        LIMIT 1
        """
    )
    rally = cursor.fetchone()

    # Buscar a última Reação Natural antes da Rally Natural
    reaction = None
    if rally:
        cursor.execute(
            """
            SELECT date, price, type
            FROM trend_clarifications
            WHERE type LIKE 'Reação Natural (fundo)'
              AND date <= ?
            ORDER BY date DESC
            LIMIT 1
            """,
            (rally[0],),
        )
        reaction = cursor.fetchone()

    # Reação secundária
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

    # Rally secundária
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

    conn.close()

    result = {}

    if trend:
        result["Tendência"] = {"date": trend[0], "price": trend[1], "type": trend[2]}

    if rally:
        result["Rally Natural"] = {
            "date": rally[0],
            "price": rally[1],
            "type": rally[2],
        }

    if reaction:
        result["Reação Natural"] = {
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

    # Só atualiza se encontrou algo
    if result:
        ultimo_resultado = result

    return (
        ultimo_resultado
        if ultimo_resultado
        else {"mensagem": "Nenhum ponto encontrado"}
    )


# ============================================================
# salva dados da binance no banco para simular ativo primario
##############################################################
def init_db():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS klines (
            symbol TEXT,
            days INTEGER,
            days_start TEXT,
            days_end TEXT,
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


# insere os klines no banco
def save_klines(
    conn, symbol, intervalo, klines, days=None, days_start=None, days_end=None
):
    cursor = conn.cursor()

    if days is not None:
        days_start = None
        days_end = None
    else:
        days = None

    dados_completos = [
        (symbol, days, days_start, days_end, intervalo, *k) for k in klines
    ]

    cursor.executemany(
        """
        INSERT OR REPLACE INTO klines (
            symbol, days, days_start, days_end, intervalo,
            open_time, open, high, low, close, volume,
            close_time, quote_asset_volume, number_of_trades,
            taker_buy_base_asset_volume, taker_buy_quote_asset_volume
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        dados_completos,
    )
    conn.commit()


# deleta os dados
def Delete_all_Klines():
    print("🗑️ Deletando todos os registros da tabela klines...")
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM klines")
        conn.commit()
    except Exception as e:
        print(f"❌ Erro ao deletar klines: {e}")
        raise
    finally:
        conn.close()


# pega os dados do banco para classificação
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


def get_date_simulation():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT days, days_start, days_end
        FROM klines 
        ORDER BY open_time DESC
        LIMIT 1
        """
    )
    result = cursor.fetchone()
    conn.close()
    return result


# cria tabela para precos
def init_db_prices():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS current_price(
            time TEXT PRIMARY KEY,
            close REAL
        )"""
    )
    conn.commit()
    conn.close()


# salva preço atual
def save_current_price(prices):
    conn = conectar()
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT OR REPLACE INTO current_price (time, close) VALUES (?, ?)",
        prices,
    )
    conn.commit()
    conn.close()


# delete preço atual
def delete_current_price():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM current_price")
    conn.commit()
    conn.close()


# pega os preço completos
def get_current_price():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT time,close FROM current_price ORDER BY time ASC")
    dados = cursor.fetchall()
    conn.close()
    return dados


# --------------------------------
# Função para criar banco e salvar RSI
# --------------------------------
def init_db_rsi():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS amrsi (
            time TEXT PRIMARY KEY,
            amrsi REAL
        )
        """
    )
    conn.commit()
    conn.close()


def save_rsi(data):
    """
    amrsi: lista de tuplas [(time, amrsi), ...]
    """
    conn = conectar()
    cursor = conn.cursor()

    # Se você quer sobrescrever tudo:
    cursor.execute("DELETE FROM amrsi")

    # transforma em lista de tuplas (time, amrsi)
    amrsi = [
        (d["time"], d["rsi_ma"] if d.get("rsi_ma") is not None else d.get("rsi"))
        for d in data
    ]

    # Inserção em massa
    cursor.executemany(
        "INSERT INTO amrsi(time, amrsi) VALUES (?, ?)",
        amrsi,
    )

    conn.commit()
    conn.close()


# Pega dados de Simulação para retornar ao frontend
def get_data_rsi():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT time, amrsi
        FROM amrsi
        ORDER BY time ASC
        """
    )
    result = cursor.fetchall()
    conn.close()
    return result


# -------------------------------------------------------------------
# Função para criar banco e salvar vppr (Volume Price Pressure Ratio)
# -------------------------------------------------------------------
def ini_db_vppr():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
         CREATE TABLE IF NOT EXISTS vppr (
         time TEXt PRIMARY KEY,
         vppr REAL,
         vppr_ema REAL
        )
        """
    )
    conn.commit()
    conn.close()


# salva dados do indicador vppr (Volume Price Pressure Ratio) no banco
def save_vppr(data):
    """
    vppr: lista de tuplas [(time,vppr,vppr_ema), ...]
    """
    conn = conectar()
    cursor = conn.cursor()

    # para sobrescrever tudo:
    cursor.execute("DELETE FROM vppr")

    # transforma em lista de tuplas (time,vppr)
    vppr = [(d["time"], d["vppr"], d["vppr_ema"]) for d in data]

    # Inserção em massa
    cursor.executemany(
        "INSERT INTO vppr(time,vppr,vppr_ema) VALUES (?,?,?)",
        vppr,
    )

    conn.commit()
    conn.close()


# pega os dados do vppr (Volume Price Pressure Ratio)
def get_data_vppr():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT time,vppr,vppr_ema
        FROM vppr
        ORDER BY time ASC
        """
    )
    result = cursor.fetchall()
    conn.close()
    return result
