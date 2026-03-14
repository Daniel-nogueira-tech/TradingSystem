import sqlite3, os
import json

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def conectar():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=10,
        check_same_thread=False
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn





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
    print("🗑️ Deletando todos os registros da tabela trend_clarifications...")
    conn.commit()
    conn.close()
    
# Limpa todos os dados (opcional, se for sobrescrever)
def clear_table_amrsi():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM amrsi")
    print("🗑️ Deletando todos os registros da tabela amrsi")
    conn.commit()
    conn.close()
    
# Limpa todos os dados (opcional, se for sobrescrever)
def clear_table_vppr():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vppr")
    print("🗑️ Deletando todos os registros da tabela vppr")
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
#===================================================================================
#--------------------------------------
# Salva os dados completos para simular ativo primário
#--------------------------------------
def save_complete_data(candles):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS complete_data(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Tempo TEXT NOT NULL UNIQUE,
            Abertura REAL NOT NULL,
            Maximo REAL NOT NULL,
            Minimo REAL NOT NULL,
            Fechamento REAL NOT NULL,
            volume REAL NOT NULL
        )
        """
    )

    # Converte dicionários para tuplas na ordem correta
    dados = [
        (c["tempo"], c["open"], c["high"], c["low"], c["close"], c["volume"])
        for c in candles
    ]

    cursor.executemany("""
    INSERT INTO complete_data
    (Tempo, Abertura, Maximo, Minimo, Fechamento, volume)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(Tempo) DO UPDATE SET
    Abertura=excluded.Abertura,
    Maximo=excluded.Maximo,
    Minimo=excluded.Minimo,
    Fechamento=excluded.Fechamento,
    volume=excluded.volume
    """, dados)

    conn.commit()
    conn.close()

# Pega dados salvos compreto simular
def get_complete_data_candles_simulation(offset=0, limit=100):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT Tempo, Abertura, Maximo, Minimo, Fechamento, volume
        FROM complete_data
        ORDER BY Tempo ASC
        LIMIT ? OFFSET ?
        """,
        (limit, offset)
    )
    dados = cursor.fetchall()
    conn.close()
    return dados
# pega dados em tempo real
def get_complete_data_candles():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT Tempo, Abertura, Maximo, Minimo, Fechamento, volume
        FROM complete_data
        ORDER BY Tempo ASC
        """
    )
    dados = cursor.fetchall()
    conn.close()
    return dados   

# apaga os dados completos
def delete_complete_data():
    print("🗑️ Deletando todos os registros da tabela complete_data...")
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM complete_data")
        conn.commit()
    except Exception as e:
        print(f"❌ Erro ao deletar complete_data: {e}")
        raise
    finally:
        conn.close()

#============================================================

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

#-----------------------------------------------------------
# pega os dados do banco para simulação do ativo correlato
#-----------------------------------------------------------
def init_db_correlation():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS klines_Correlation (
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
def save_klines_correlation(
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
        INSERT OR REPLACE INTO klines_Correlation (
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
def Delete_all_Klines_correlation():
    print("🗑️ Deletando todos os registros da tabela klines_Correlation...")
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM klines_Correlation")
        conn.commit()
    except Exception as e:
        print(f"❌ Erro ao deletar klines: {e}")
        raise
    finally:
        conn.close()


# pega os dados do banco para classificação
def get_data_klines_correlation(symbol, intervalo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT open_time, open, high, low, close, volume
        FROM klines_Correlation
        WHERE symbol = ? AND intervalo = ?
        ORDER BY open_time
        """,
        (symbol, intervalo),
    )
    resultados = cursor.fetchall()
    conn.close()
    return resultados


# --------------------------------
# cria tabela para precos do atr
# --------------------------------
def init_db_atr():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS atr(
            Tempo TEXT PRIMARY KEY,
            atr_soft REAL
        )"""
    )
    conn.commit()
    conn.close()


# --------------------------------
# salva atr
# --------------------------------
def save_atr(atr_soft):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM atr")
    # transforma em lista de tuplas (time, atr)
    atr = [(d["Tempo"], d.get("atr_soft")) for d in atr_soft]

    # Inserção em massa
    cursor.executemany(
        """
        INSERT INTO atr(Tempo, atr_soft) 
        VALUES (?, ?)
        ON CONFLICT(Tempo) DO UPDATE SET
        atr_soft = excluded.atr_soft
        """,
        atr,
    )
    conn.commit()
    conn.close()


# --------------------------------
# Pega dados de atr
# --------------------------------
def get_atr_first_of_month():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT atr_soft
        FROM atr
        WHERE Tempo IN (
            SELECT MIN(Tempo)
            FROM atr
            GROUP BY strftime('%Y-%m', Tempo)
        )
        ORDER BY Tempo ASC
    """
    )

    result = cursor.fetchall()
    conn.close()
    return result


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


    # transforma em lista de tuplas (time, amrsi)
    amrsi = [
        (d["time"], d["rsi_ma"] if d.get("rsi_ma") is not None else d.get("rsi"))
        for d in data
    ]

    # Inserção em massa
    cursor.executemany(
        """
        INSERT INTO amrsi(time, amrsi)
        VALUES (?, ?)
        ON CONFLICT(time) DO UPDATE SET
        amrsi = excluded.amrsi
        """,
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

    # transforma em lista de tuplas (time,vppr)
    vppr = [(d["time"], d["vppr"], d["vppr_ema"]) for d in data]

    # Inserção em massa
    cursor.executemany(
       """
        INSERT INTO vppr(time, vppr, vppr_ema)
        VALUES (?, ?, ?)
        ON CONFLICT(time) DO UPDATE SET
        vppr = excluded.vppr,
        vppr_ema = excluded.vppr_ema
       """,
       vppr
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
# -------------------------------------------------------------------
# Função para salvar observações de mercado no banco de dados
# -------------------------------------------------------------------
def save_market_observations(symbol, notes):
    # 👉 injeta o símbolo em cada registro
    for candle in notes:
        candle["symbol"] = symbol

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_observations (
            symbol TEXT PRIMARY KEY,
            notes TEXT
        )
    """)

    notes_json = json.dumps(notes, ensure_ascii=False)

    cursor.execute(
        """
        INSERT OR REPLACE INTO market_observations (symbol, notes)
        VALUES (?, ?)
        """,
        (symbol, notes_json),
    )

    conn.commit()
    conn.close()
# Retorna a ultima linha por simbolo (observação mais recente)
def get_latest_market_by_symbol():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT symbol, notes
        FROM market_observations
    """)

    rows = cursor.fetchall()
    conn.close()

    result = []
    for symbol, notes in rows:
        data = json.loads(notes)
        # pega o último candle do JSON
        last = data[-1] if isinstance(data, list) and data else {}
        last["symbol"] = symbol
        result.append(last)
    return result

def get_all_symbols():
    """Retorna uma lista de todos os símbolos salvos"""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT symbol FROM market_observations")
    result = cursor.fetchall()
    conn.close()
    return [row[0] for row in result]

def remover_symbol(symbol):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
    """
      DELETE FROM market_observations 
      WHERE symbol = ?
    """,
    (symbol,)
    )

    conn.commit()
    conn.close()



#PEGA OS DADOS PARA GRÁFICOS DE OBSERVAÇÂO DE MERCADO
def get_complete_data_market_observations(symbol):
    """Retorna todos os registros (candles) do símbolo como array desserializado"""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT notes
        FROM market_observations  
        WHERE symbol = ?
        """,
        (symbol,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return []
    
    # Desserializa o JSON armazenado
    notes_data = json.loads(row[0])
    return notes_data 

#Pega todos os dados para calcular matriz de correlação
def get_all_market_observations_to_matrix():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT symbol, notes
        FROM market_observations
    """)

    rows = cursor.fetchall()
    conn.close()

    data = []

    for symbol, notes_json in rows:
        notes = json.loads(notes_json)
        data.append({
            "symbol": symbol,
            "notes": notes
        })
    return data

# PEGA SIMBOLOS COM CORRELAÇÃO
def get_symbols_with_correlation(symbolCorrelation):
    conn = conectar()
    cursor = conn.cursor()

    # Extrai símbolos únicos
    symbols = set()

    for item in symbolCorrelation:
        symbols.add(item["base_asset"])
        symbols.add(item["correlated_asset"])

    symbols = list(symbols)

    # Cria placeholders dinamicamente (?, ?, ?, ...)
    placeholders = ",".join(["?"] * len(symbols))

    query = f"""
        SELECT *
        FROM market_observations
        WHERE symbol IN ({placeholders})
    """

    cursor.execute(query, symbols)

    rows = cursor.fetchall()
    conn.close()
    return rows

# -------------------------------------------------------------------
# Função para salvar dados de backtest no banco de dados
# -------------------------------------------------------------------
def save_backtest_results(symbol, backtest_data):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backtest_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            time TEXT,
            type TEXT,
            buy REAL,
            stop REAL,
            average_price REAL,
            partial_price REAL,
            final_price REAL
        )
    """)

    for trade in backtest_data:
        cursor.execute("""
            INSERT INTO backtest_results (
                symbol,
                time,
                type,
                buy,
                stop,
                average_price,
                partial_price,
                final_price
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            trade.get("time"),
            trade.get("type"),
            trade.get("buy"),
            trade.get("stop"),
            trade.get("average_price"),
            trade.get("partial_price"),
            trade.get("final_price"),
        ))

    conn.commit()
    conn.close()

# Parciais 
def save_backtest_partials(trade_id, partials):
    conn = conectar()
    cursor = conn.cursor()  
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS backtest_partials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER,
        partial_time TEXT,
        partial_price REAL,
        partial_percent REAL,
        FOREIGN KEY (trade_id) REFERENCES backtest_trades(id)
    );
        """)
    for partial in partials:
        cursor.execute("""
            INSERT INTO backtest_partials (
                trade_id,
                partial_time,
                partial_price,
                partial_percent
            )
            VALUES (?, ?, ?, ?)
        """, (
            trade_id,
            partial.get("partial_time"),
            partial.get("partial_price"),
            partial.get("partial_percent"),
        ))

    conn.commit()
    conn.close()