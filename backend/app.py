from flask import Flask, jsonify
from flask import request, jsonify
from flask_cors import CORS
import pandas as pd
from binance.client import Client
from datetime import datetime, timedelta, timezone
import time
import requests
import zipfile
import io
import csv
import logging
from db import (
    create_table,
    salve_or_replace,
    symbolo_saved,
    symbolo_saved_sec,
    salve_or_replace_sec,
    symbolo_saved_sec,
    create_table_sec,
    create_table_timeframe_global,
    get_timeframe_global,
    save_trend_clarifications,
    create_table_trend_clarifications,
    clear_table_trend_clarifications,
    save_trend_clarifications_key,
    clear_table_trend_clarifications_key,
    create_table_trend_clarifications_key,
    important_points,
    important_points_key,
    init_db,
    save_klines,
    conectar,
    Delete_all_Klines,
    get_data_klines,
    get_trend_clarifications,
    Delete_all_Klines_sec,
    save_klines_sec,
    create_table_trend_clarifications_sec,
    get_trend_clarifications_sec,
    get_data_klines_sec,
    init_db_sec,
    clear_table_trend_clarifications_sec,
    save_trend_clarifications_sec,
    get_trend_clarifications_key,
    get_date_simulation,
    get_date_simulation_sec,
    init_db_rsi,
    save_rsi,
    get_date_rsi,
    init_db_prices,
    save_current_price,
    delete_current_price,
    get_current_price,
)
from indicators.atr import calcular_atr_movel, suavizar_atr
from indicators.rsi import get_rsi

client = Client()
app = Flask(__name__)
CORS(app)


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    app.run(debug=True)

create_table()
create_table_sec()
create_table_trend_clarifications()
clear_table_trend_clarifications()
create_table_trend_clarifications_sec()
create_table_trend_clarifications_key()
clear_table_trend_clarifications_key()
init_db()
init_db_sec()
init_db_rsi()
init_db_prices()


# --------------------------------------------------------
# Função para formatar os dados brutos da API da Binance
# --------------------------------------------------------
def formatar_dados_brutos(dados_brutos):
    dados_formatados = []

    for k in dados_brutos:
        dado = {
            "Tempo": datetime.fromtimestamp(k[0] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
            "Abertura": float(k[1]),
            "Maximo": float(k[2]),
            "Minimo": float(k[3]),
            "Fechamento": float(k[4]),
            "Volume": float(k[5]),
        }
        dados_formatados.append(dado)

    return dados_formatados


# --------------------------------
# Função para calcular RSI INICIO
# --------------------------------
@app.route("/api/rsi", methods=["GET"])
def api_rsi():
    symbol = request.args.get("symbol", "BTCUSDT")
    modo = request.args.get("modo", "")
    offset = request.args.get("offset", type=int)
    limit = request.args.get("limit", type=int)
    period = request.args.get("period", default=14, type=int)

    data = get_rsi(symbol, modo=modo, offset=offset, limit=limit, period=period)

    save_rsi(data)
    return jsonify(data)


# --------------------------------
# Função simular rsi
# --------------------------------
@app.route("/api/simulate_amrsi", methods=["GET"])
def simulate_amrsi():
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 10))

    amrsi = get_date_rsi()

    if not amrsi:
        return jsonify([])

    amrsi_fatiado = amrsi[offset : offset + limit]

    dados = [
        {
            "time": m[0],
            "amrsi": m[1],
        }
        for m in amrsi_fatiado
    ]

    return jsonify(dados)


# --------------------------------
# Função para calcular RSI FIM
# --------------------------------


# ==========================================================================
#                      Inicio ativo primário
# ==========================================================================
# ----------------------------------------
# 🔍 1️⃣ Consultar o último símbolo salvo
# ----------------------------------------
@app.route("/api/last_symbol", methods=["GET"])
def get_last_symbol():
    symbol = symbolo_saved()
    if symbol:
        return jsonify({"symbol": symbol}), 200
    else:
        return jsonify({"message": "Nenhum símbolo salvo"}), 404


# --------------------------------------------------------
# 1️⃣ Endpoint para mudar tempo grafico (em todos graficos)
# --------------------------------------------------------
@app.route("/api/timeframe", methods=["GET", "POST"])
def filter_time():
    if request.method == "POST":
        data = request.get_json() or request.form
        time = data.get("time", "").strip()

        if not time:
            return jsonify({"erro": "Parâmetro 'symbol' é obrigatório"}), 400

        create_table_timeframe_global(time)
        return jsonify({"mensagem": "Timeframe salvo com sucesso", "time": time}), 200

    elif request.method == "GET":
        # Retorna o tempo atual salvo
        time = get_timeframe_global()
        return jsonify({"time": time}), 200


# ----------------------------------------------------------------------
# 1️⃣ Função para atualizar o klines salvos para simular primeiro ativo
# ----------------------------------------------------------------------
@app.route("/api/update_klines", methods=["GET", "POST"])
def update_klines():
    symbol = str(request.args.get("symbol", "")).strip().upper()
    date_start = request.args.get("date_start", "").strip()
    date_end = request.args.get("date_end", "").strip()
    days = request.args.get("days", "").strip()

    if not symbol:
        return jsonify({"erro": "Parâmetro 'symbol' é obrigatório"}), 400

    days = int(days) if days.isdigit() else None

    salve_or_replace(symbol)
    timeFrame = get_timeframe_global().lower()

    try:
        download_and_save_klines(
            symbol,
            intervalo=timeFrame,
            date_start=date_start,
            date_end=date_end,
            days=days,
        )
        return jsonify({"mensagem": f"Dados de {symbol} atualizados com sucesso!"})
    except Exception as e:
        print(f"❌ Erro ao baixar/salvar klines: {str(e)}")
        return jsonify({"erro": str(e)}), 500


# --------------------------------------------------
# 📊 1️⃣  Baixar múltiplos anos do ativo primario
# --------------------------------------------------
def download_historical_klines(
    symbol, intervalo, start_year, end_year, date_start=None, date_end=None
):
    all_klines = []
    base_url = "https://data.binance.vision/data/spot/monthly/klines"

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            file_name = f"{symbol}-{intervalo}-{year}-{month:02d}.zip"
            url = f"{base_url}/{symbol}/{intervalo}/{file_name}"

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        csv_name = file_name.replace(".zip", ".csv")
                        with z.open(csv_name) as f:
                            reader = csv.reader(io.TextIOWrapper(f))
                            next(reader, None)  # Pula cabeçalho, se houver
                            klines = [row for row in reader if row]
                            all_klines.extend(klines)
                else:
                    print(f"Arquivo não encontrado: {url}")
            except Exception as e:
                print(f"Erro ao baixar {url}: {e}")
                continue

    # Filtrar por datas, se fornecidas
    if date_start and date_end:
        start_ms = int(
            datetime.strptime(date_start, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .timestamp()
            * 1000
        )
        end_ms = int(
            datetime.strptime(date_end, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .timestamp()
            * 1000
        )
        all_klines = [k for k in all_klines if start_ms <= int(k[0]) <= end_ms]

    # Formatar para o mesmo formato da API (11 colunas)
    klines_formatados = [tuple(k[:11]) for k in all_klines if k]
    return klines_formatados


# --------------------------------------------------
# 📊 1️⃣  Guarda no banco de dados do ativo primario
# --------------------------------------------------
def download_and_save_klines(
    symbol, intervalo, date_start=None, date_end=None, days=None, clean_before=True
):
    if clean_before:
        Delete_all_Klines()

    all_klines = []

    # Definir período
    if date_start and date_end:
        start_dt = datetime.strptime(date_start, "%Y-%m-%d")
        end_dt = datetime.strptime(date_end, "%Y-%m-%d")
        start_ms = int(start_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
        end_ms = int(end_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)

        # Se período for longo (> 1 ano), usar dados históricos
        if (end_dt - start_dt).days > 365:
            start_year = start_dt.year
            end_year = end_dt.year
            all_klines = download_historical_klines(
                symbol, intervalo, start_year, end_year, date_start, date_end
            )
            # Complementar com API para dados após o último arquivo mensal
            last_kline_ms = int(all_klines[-1][0]) if all_klines else start_ms
            if last_kline_ms < end_ms:
                while last_kline_ms < end_ms:
                    params = {
                        "symbol": symbol,
                        "interval": intervalo,
                        "startTime": last_kline_ms + 1,
                        "limit": 1000,  # Limite padrão da API é 1000
                    }
                    if end_ms:
                        params["endTime"] = end_ms

                    batch = client.get_klines(**params)
                    if not batch:
                        break
                    all_klines.extend(batch)
                    last_kline_ms = batch[-1][0]
                    time.sleep(0.3)  # Evitar rate limit
        else:
            # Período curto, usar apenas API
            while True:
                params = {
                    "symbol": symbol,
                    "interval": intervalo,
                    "startTime": start_ms,
                    "limit": 1000,
                }
                if end_ms:
                    params["endTime"] = end_ms

                batch = client.get_klines(**params)
                if not batch:
                    break
                all_klines.extend(batch)
                if end_ms and batch[-1][0] >= end_ms:
                    break
                start_ms = batch[-1][0] + 1
                time.sleep(0.3)
    elif days:
        # Lógica para days (usar API)
        start_ms = int(
            (datetime.now(timezone.utc) - timedelta(days=int(days))).timestamp() * 1000
        )
        end_ms = None
        while True:
            params = {
                "symbol": symbol,
                "interval": intervalo,
                "startTime": start_ms,
                "limit": 1000,
            }
            batch = client.get_klines(**params)
            if not batch:
                break
            all_klines.extend(batch)
            start_ms = batch[-1][0] + 1
            time.sleep(0.3)
    else:
        raise ValueError("Você deve passar dias ou date_start/date_end")

    # Formatar e salvar
    klines_formatados = [tuple(k[:11]) for k in all_klines]
    conn = conectar()
    save_klines(
        conn,
        symbol,
        intervalo,
        klines_formatados,
        days=days,
        days_start=date_start,
        days_end=date_end,
    )
    conn.close()


# ============================SIMULAR inicio============================
# ----------------------------------------------------------------
# 📊 1️⃣ Pega no banco de dados do ativo para simulação primário.
# ----------------------------------------------------------------
@app.route("/api/simulate_price_atr", methods=["GET"])
def simulate_price_atr():
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 10))

    movimentos = get_trend_clarifications()

    if not movimentos:
        return jsonify([])  # Nada para simular

    movimentos_fatiados = movimentos[offset : offset + limit]

    dados = [
        {
            "closeTime": m[0],
            "closePrice": m[1],
            "tipo": m[2],
            "atr": m[3],
        }
        for m in movimentos_fatiados
    ]
    return jsonify(dados)


# ---------------------------------------------------------------------------
# 📊 1️⃣  Pega os dados completos para validar entrada no frontend simulação.
# ---------------------------------------------------------------------------
@app.route("/api/simulate_current_price", methods=["GET"])
def simulate_current_price():
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 10))

    price = get_current_price()

    if not price:
        return jsonify([])

    price_slice = price[offset : offset + limit]

    dados = [
        {
            "time": m[0],
            "close": m[1],
        }
        for m in price_slice
    ]
    return jsonify(dados)


# -------------------------------------------
# 📊 1️⃣  Pega as datas ou dias da simulação.
# -------------------------------------------
@app.route("/api/get_date/simulation", methods=["GET"])
def get_date_simalation():
    date_simulation = get_date_simulation()
    if date_simulation:
        days, days_start, days_end = date_simulation
        return (
            jsonify({"days": days, "days_start": days_start, "days_end": days_end}),
            200,
        )
    else:
        return jsonify({"message": "Nenhum símbolo salvo"}), 404


# ===============================SIMULAR FIM================================
# ==========================================================================
#                          Fim ativo primário
# ==========================================================================


# ==========================================================================
#                          Inicio ativo secundário
# ==========================================================================
# ------------------------------------------------------------
# 🔍 2️⃣ Consultar o último símbolo salvo do ativo secundário
# ------------------------------------------------------------
@app.route("/api/last_symbol_second", methods=["GET"])
def get_last_symbol_sec():
    symbol = symbolo_saved_sec()
    if symbol:
        return jsonify({"symbol": symbol}), 200
    else:
        return jsonify({"message": "Nenhum símbolo salvo"}), 404


# --------------------------------------------------------------------
# 2️⃣ Função para atualizar os klines salvos para simular segundo ativo.
# --------------------------------------------------------------------
@app.route("/api/update_klines_sec", methods=["GET", "POST"])
def update_klines_sec():
    symbol = request.args.get("symbol", "").strip().upper()
    date_start = request.args.get("date_start", "").strip()
    date_end = request.args.get("date_end", "").strip()
    days = request.args.get("days", "").strip()

    if not symbol:
        return jsonify({"erro": "Parâmetro 'symbol' é obrigatório"}), 400

    days = int(days) if days.isdigit() else None

    salve_or_replace_sec(symbol)  # salva no banco o símbolo atual
    timeFrame = get_timeframe_global().lower()

    try:
        download_and_save_klines_sec(
            symbol,
            intervalo=timeFrame,
            date_start=date_start,
            date_end=date_end,
            days=days,
        )
        return jsonify({"mensagem": f"Dados de {symbol} atualizados com sucesso!"})
    except Exception as e:
        print(f"❌ Erro ao baixar/salvar klines: {str(e)}")
        return jsonify({"erro": str(e)}), 500


# --------------------------------------------------
# 📊 2️⃣   Baixar múltiplos anos do ativo Secundario
# --------------------------------------------------
def download_historical_klines_sec(
    symbol, intervalo, start_year, end_year, date_start=None, date_end=None
):
    all_klines = []
    base_url = "https://data.binance.vision/data/spot/monthly/klines"

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            file_name = f"{symbol}-{intervalo}-{year}-{month:02d}.zip"
            url = f"{base_url}/{symbol}/{intervalo}/{file_name}"

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        csv_name = file_name.replace(".zip", ".csv")
                        with z.open(csv_name) as f:
                            reader = csv.reader(io.TextIOWrapper(f))
                            next(reader, None)  # Pula cabeçalho, se houver
                            klines = [row for row in reader if row]
                            all_klines.extend(klines)
                else:
                    print(f"Arquivo não encontrado: {url}")
            except Exception as e:
                print(f"Erro ao baixar {url}: {e}")
                continue

    # Filtrar por datas, se fornecidas
    if date_start and date_end:
        start_ms = int(
            datetime.strptime(date_start, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .timestamp()
            * 1000
        )
        end_ms = int(
            datetime.strptime(date_end, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .timestamp()
            * 1000
        )
        all_klines = [k for k in all_klines if start_ms <= int(k[0]) <= end_ms]

    # Formatar para o mesmo formato da API (11 colunas)
    klines_formatados = [tuple(k[:11]) for k in all_klines if k]
    return klines_formatados


# ----------------------------------------------------------
# 📊2️⃣  Guarda no banco de dados dados do ativo secundário
# -----------------------------------------------------------
def download_and_save_klines_sec(
    symbol, intervalo, date_start=None, date_end=None, days=None, clean_before=True
):
    if clean_before:
        Delete_all_Klines_sec()

    all_klines = []

    # Definir período
    if date_start and date_end:
        start_dt = datetime.strptime(date_start, "%Y-%m-%d")
        end_dt = datetime.strptime(date_end, "%Y-%m-%d")
        start_ms = int(start_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
        end_ms = int(end_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)

        # Se período for longo (> 1 ano), usar dados históricos
        if (end_dt - start_dt).days > 365:
            start_year = start_dt.year
            end_year = end_dt.year
            all_klines = download_historical_klines_sec(
                symbol, intervalo, start_year, end_year, date_start, date_end
            )
            # Complementar com API para dados após o último arquivo mensal
            last_kline_ms = int(all_klines[-1][0]) if all_klines else start_ms
            if last_kline_ms < end_ms:
                while last_kline_ms < end_ms:
                    params = {
                        "symbol": symbol,
                        "interval": intervalo,
                        "startTime": last_kline_ms + 1,
                        "limit": 1000,  # Limite padrão da API é 1000, não 1500
                    }
                    if end_ms:
                        params["endTime"] = end_ms

                    batch = client.get_klines(**params)
                    if not batch:
                        break
                    all_klines.extend(batch)
                    last_kline_ms = batch[-1][0]
                    time.sleep(0.3)  # Evitar rate limit
        else:
            # Período curto, usar apenas API
            while True:
                params = {
                    "symbol": symbol,
                    "interval": intervalo,
                    "startTime": start_ms,
                    "limit": 1000,
                }
                if end_ms:
                    params["endTime"] = end_ms

                batch = client.get_klines(**params)
                if not batch:
                    break
                all_klines.extend(batch)
                if end_ms and batch[-1][0] >= end_ms:
                    break
                start_ms = batch[-1][0] + 1
                time.sleep(0.3)
    elif days:
        # Lógica para days (usar API)
        start_ms = int(
            (datetime.now(timezone.utc) - timedelta(days=int(days))).timestamp() * 1000
        )
        end_ms = None
        while True:
            params = {
                "symbol": symbol,
                "interval": intervalo,
                "startTime": start_ms,
                "limit": 1000,
            }
            batch = client.get_klines(**params)
            if not batch:
                break
            all_klines.extend(batch)
            start_ms = batch[-1][0] + 1
            time.sleep(0.3)
    else:
        raise ValueError("Você deve passar dias ou date_start/date_end")

    # Formatar e salvar
    klines_formatados = [tuple(k[:11]) for k in all_klines]
    conn = conectar()
    save_klines_sec(
        conn,
        symbol,
        intervalo,
        klines_formatados,
        days=days,
        days_start=date_start,
        days_end=date_end,
    )
    conn.close()


# ===============================SIMULAR inicio================================
# -----------------------------------------------------------------------------
# 📊 2️⃣ pega no banco de dados dados do ativo para simular o ativo secundário
# -----------------------------------------------------------------------------
@app.route("/api/simulate_price_atr_sec", methods=["GET"])
def simulate_price_atr_sec():
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 10))

    movimentos = get_trend_clarifications_sec()

    if not movimentos:
        return jsonify([])  # Nada para simular

    movimentos_fatiados = movimentos[offset : offset + limit]

    dados = [
        {
            "closeTime": m[0],
            "closePrice": m[1],
            "tipo": m[2],
        }
        for m in movimentos_fatiados
    ]

    return jsonify(dados)


# -------------------------------------------
# 📊 2️⃣  Pega as datas ou dias da simulação.
# -------------------------------------------
@app.route("/api/get_date/simulation_sec", methods=["GET"])
def get_date_simalation_sec():
    date_simulation = get_date_simulation_sec()
    if date_simulation:
        days, days_start, days_end = date_simulation
        return (
            jsonify({"days": days, "days_start": days_start, "days_end": days_end}),
            200,
        )
    else:
        return jsonify({"message": "Nenhum símbolo salvo"}), 404


# ===============================SIMULAR FIM================================


# ==========================================================================
#                          Fim ativo secundário
# ==========================================================================


# ==========================================================================
#                          Inicio ativo Chave
# ==========================================================================
# --------------------------------------------------------------------
# 📊 3 pega no banco de dados dados do ativo para simular ativo chave
# --------------------------------------------------------------------
@app.route("/api/simulate_price_atr_key", methods=["GET"])
def simulate_price_atr_key():
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 10))

    movimentos = get_trend_clarifications_key()

    if not movimentos:
        return jsonify([])  # Nada para simular

    movimentos_fatiados = movimentos[offset : offset + limit]

    dados = [
        {
            "closeTime": m[0],
            "closePrice": m[1],
            "tipo": m[2],
        }
        for m in movimentos_fatiados
    ]

    return jsonify(dados)


# ==========================================================================
#                          Inicie a classificação
# ==========================================================================
# ------------------------------
# 1️⃣ Endpoint do ativo Primeiro
# ------------------------------
@app.route("/api/filter_price_atr", methods=["GET", "POST"])
def filter_price_atr():
    symbol = request.args.get("symbol", "").strip().upper()
    modo = request.args.get("modo", "").strip().lower()
    if not symbol:
        return jsonify({"erro": "Parâmetro 'symbol' é obrigatório"}), 400

    salve_or_replace(symbol)

    #  Recupera do banco (só pra confirmar ou usar daqui pra frente)
    symbol_primary = symbolo_saved()

    #  Busca os klines na Binance
    time = get_timeframe_global()
    try:
        if modo == "simulation":
            # 🔁 Limpa os dados antigos da tabela antes de salvar os novos
            clear_table_trend_clarifications()
            # 🔁 Pega os dados do banco
            dados_brutos = get_data_klines(symbol_primary, time)
            dados = formatar_dados_brutos(dados_brutos)
            delete_current_price()
        else:
            clear_table_trend_clarifications()
            # 🔁 Pega os dados em tempo real da Binance
            dados_brutos = client.get_klines(
                symbol=symbol_primary, interval=time, limit=1500
            )
            dados = formatar_dados_brutos(dados_brutos)
            delete_current_price()

    except Exception as e:
        print(f"❌ Erro Binance: {str(e)}")
        return jsonify({"erro": str(e)}), 500

    # Formata os dados e extrai preços de fechamento e tempos
    dados = formatar_dados_brutos(dados_brutos)
    closes = [item["Fechamento"] for item in dados]
    timestamps = [item["Tempo"] for item in dados]

    # Calcula o ATR suavizado
    atrs = calcular_atr_movel(dados, periodo=14)
    atr_suave = suavizar_atr(atrs, periodo=180)

    if not atr_suave:
        return jsonify({"erro": "ATR não pôde ser calculado."}), 400

    verify_time_multiply = 3

    # Define os limites com base no ATR
    atr_ultima_suave = atr_suave[-1]["ATR_Suavizado"]
    atr_mult = atr_ultima_suave * verify_time_multiply

    # Aredonda os valores
    round_atr = round(atr_mult, 2)
    confir = round_atr / 2
    confir_round = round(confir, 2)

    limite = round_atr
    confirmar = confir_round

    # Inicializa variáveis de controle
    cont = 0
    movimentos = []
    estado = "inicio"
    topo = closes[0]
    fundo = closes[0]
    ponto_referencia = closes[0]
    ponto_inicial = closes[0]
    tendencia_atual = None
    ultimo_pivot_alta = None
    ultimo_pivot_baixa = None
    ultimo_pivot_reacao_sec_alta = None
    ultimo_pivot_reacao_sec_baixa = None
    ultimo_pivot_rally_alta = None
    ultimo_pivot_rally_baixa = None
    ultimo_pivot_rally_alta_temp = None
    ultimo_pivot_rally_baixa_temp = None
    ultimo_pivot_reacao_sec_alta_temp = None
    ultimo_pivot_reacao_sec_baixa_temp = None
    prices_to_insert = []

    # Primeiro ponto é sempre um Rally Natural Inicial
    movimentos.append(
        {
            "closeTime": timestamps[0],
            "closePrice": ponto_referencia,
            "tipo": "Rally Natural (inicial)",
            "limite": limite,
        }
    )

    for i in range(1, len(closes)):
        preco = closes[i]
        tempo = timestamps[i]
        variacao = preco - ponto_referencia
        movimento_adicionado = False  # Controle para evitar duplicação
        cont += 1
        price = preco

        # salva preço atual
        prices_to_insert.append((tempo, preco))

        # === ESTADO INICIAL ===
        # Detecta início de tendência
        if estado == "inicio":
            if not movimento_adicionado and preco > ponto_referencia + limite:
                # Inicia tendência de alta
                estado = "tendencia_alta"
                tendencia_atual = "Alta"
                ultimo_pivot_alta = preco
                topo = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Tendência Alta",
                        "limite": limite,
                    }
                )
                movimento_adicionado = True

            elif not movimento_adicionado and preco < ponto_referencia - limite:
                # Inicia tendência de baixa
                estado = "tendencia_baixa"
                tendencia_atual = "Baixa"
                ultimo_pivot_baixa = preco
                fundo = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Tendência Baixa",
                        "limite": limite,
                    }
                )
                movimento_adicionado = True

        # === TENDÊNCIA DE ALTA ===
        elif not movimento_adicionado and estado == "tendencia_alta":
            if preco > topo:
                # Continua tendência de alta
                topo = preco
                ultimo_pivot_alta = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Tendência Alta (topo)",
                        "limite": limite,
                    }
                )
                movimento_adicionado = True
            elif not movimento_adicionado and preco < topo - limite:
                # Transição para reação natural (correção)
                estado = "reacao_natural"
                fundo = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Reação Natural (Alta)",
                        "limite": limite,
                    }
                )
                movimento_adicionado = True

        # === TENDÊNCIA DE BAIXA ===
        elif not movimento_adicionado and estado == "tendencia_baixa":
            if preco < fundo:
                # Continua tendência de baixa
                fundo = preco
                ultimo_pivot_baixa = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Tendência Baixa (fundo)",
                        "limite": limite,
                    }
                )
                movimento_adicionado = True
            elif not movimento_adicionado and preco > fundo + limite:
                # Transição para reação natural (correção)
                estado = "reacao_natural"
                topo = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Reação Natural (Baixa)",
                        "limite": limite,
                    }
                )
                movimento_adicionado = True

        # === REAÇÃO NATURAL ===            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        elif estado == "reacao_natural":
            if tendencia_atual == "Alta":
                # Vindo de tendência de alta
                if not movimento_adicionado and preco < fundo:
                    # Continuação da reação
                    fundo = preco
                    ultimo_pivot_rally_alta_temp = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação Natural (fundo)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_alta
                ):
                    # Rally Natural (recuperacao)
                    estado = "rally_natural"
                    topo = preco
                    ultimo_pivot_rally_alta = ultimo_pivot_rally_alta_temp
                    ultimo_pivot_rally_baixa = None
                    ponto_inicial = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (Alta)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ponto_inicial is not None
                    and preco < ponto_inicial - confirmar
                ):
                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_inicial = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):

                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (Reversão)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and preco < ultimo_pivot_baixa - confirmar
                ):

                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

            elif tendencia_atual == "Baixa":
                # Vindo de tendência baixa
                if not movimento_adicionado and preco > topo:
                    # Continuação da reação
                    topo = preco
                    ultimo_pivot_rally_baixa_temp = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação Natural (topo)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_baixa
                ):
                    # Rally Natural (respiro de baixa)
                    estado = "rally_natural"
                    fundo = preco
                    ultimo_pivot_rally_baixa = ultimo_pivot_rally_baixa_temp
                    ultimo_pivot_rally_alta = None
                    ponto_inicial = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (Baixa)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and preco < ultimo_pivot_baixa - confirmar
                ):
                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ponto_inicial is not None
                    and preco > ponto_inicial + confirmar
                ):
                    # Reversão para tendência de alta
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_inicial = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (Reversão)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

        # === RALLY NATURAL ===
        elif estado == "rally_natural":
            if tendencia_atual == "Alta":
                # Vindo de tendência alta
                if (
                    not movimento_adicionado
                    and preco > topo
                    and preco < ultimo_pivot_alta
                ):
                    # Continuação do rally
                    topo = preco
                    ultimo_pivot_reacao_sec_alta_temp = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (topo)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    # Retomada da tendência de alta
                    estado = "tendencia_alta"
                    ultimo_pivot_alta = preco
                    tendencia_atual = "Alta"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_rally_alta
                ):
                    estado = "reacao_secundaria"
                    fundo = preco
                    ultimo_pivot_reacao_sec_alta = ultimo_pivot_reacao_sec_alta_temp
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Alta)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
            elif tendencia_atual == "Baixa":
                # Vindo de tendência baixa
                if (
                    not movimento_adicionado
                    and preco < fundo
                    and preco > ultimo_pivot_baixa
                ):
                    # Continuação do rally
                    fundo = preco
                    ponto_referencia = preco
                    ultimo_pivot_reacao_sec_baixa_temp = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (fundo)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado and preco < ultimo_pivot_baixa - confirmar
                ):
                    # Retomada da tendência de baixa
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    # Reversão para tendência de alta
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_rally_baixa
                ):
                    estado = "reacao_secundaria"
                    topo = preco
                    ultimo_pivot_reacao_sec_baixa = ultimo_pivot_reacao_sec_baixa_temp
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Baixa)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

        # ======== Reação secundária ===========
        elif estado == "reacao_secundaria":
            if tendencia_atual == "Alta":
                if not movimento_adicionado and preco < fundo:
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Fundo)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_alta is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_reacao_sec_alta
                ):
                    # rally secundário
                    estado = "rally_secundario"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundário (Alta)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_alta is not None
                    and preco > fundo + limite
                    and preco > ultimo_pivot_reacao_sec_alta
                    and preco < ultimo_pivot_alta
                ):
                    #  volta ao rally
                    estado = "rally_natural"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (retorno)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta",
                            "limite": limite,
                        }
                    )
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    ultimo_pivot_baixa = preco
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    ultimo_pivot_baixa = preco
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

            elif tendencia_atual == "Baixa":
                # vindo de tendência de baixa
                if not movimento_adicionado and preco > topo:
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (topo)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_reacao_sec_baixa
                ):
                    #  volta ao rally
                    estado = "rally_secundario"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundário (Baixa)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco < topo - limite
                    and preco < ultimo_pivot_reacao_sec_baixa
                    and preco > ultimo_pivot_baixa
                ):
                    #  volta ao rally
                    estado = "rally_natural"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (retorno)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and ultimo_pivot_baixa
                    and preco < ultimo_pivot_baixa - confirmar
                ):
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    ultimo_pivot_baixa = preco
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa",
                            "limite": limite,
                        }
                    )
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

            # ======== Reação secundária ===========
        elif estado == "rally_secundario":
            if tendencia_atual == "Alta":
                if not movimento_adicionado and preco > topo:
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundária (Topo)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_reacao_sec_alta
                ):
                    estado = "reacao_secundaria"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Alta)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                    # retorno do rally secundario para reacao
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_alta is not None
                    and preco > ultimo_pivot_reacao_sec_alta + confirmar
                    and preco < ultimo_pivot_alta
                ):
                    estado = "rally_natural"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (retorno)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_rally_alta
                ):
                    estado = "reacao_secundaria"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

            elif tendencia_atual == "Baixa":
                # vindo de tendência de baixa
                if not movimento_adicionado and preco < fundo:
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundária (Fundo)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_reacao_sec_baixa
                ):
                    estado = "reacao_secundaria"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Baixa)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                    # retorno do rally secundario para reacao
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco < ultimo_pivot_reacao_sec_baixa - confirmar
                    and preco > ultimo_pivot_baixa
                ):
                    estado = "rally_natural"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (retorno)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco > ultimo_pivot_baixa
                    and preco < ultimo_pivot_reacao_sec_baixa - confirmar
                ):
                    # volta Rally natural
                    estado = "rally_natural"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (Baixa)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_rally_baixa
                ):
                    estado = "reacao_secundaria"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

    # Cria lista de tuplas para bulk insert
    movimentos_para_salvar = []

    for p in movimentos:
        date = p["closeTime"]
        price = p["closePrice"]
        type = p["tipo"]
        atr = p["limite"]

        movimentos_para_salvar.append((date, price, type, atr))

    # Salva todos os dados de uma vez
    save_trend_clarifications(movimentos_para_salvar)
    # salvar os precos
    if prices_to_insert:
        save_current_price(prices_to_insert)

    return jsonify(movimentos)


# -----------------------------------------------------
# 2️⃣ Endpoint para pegar dados secundários da binance.
# -----------------------------------------------------
@app.route("/api/filter_price_atr_second", methods=["GET", "POST"])
def filter_price_atr_second():
    symbol = request.args.get("symbol").strip().upper()
    modo = request.args.get("modo", "").strip().lower()

    if not symbol:
        return jsonify({"erro": "Parâmetro 'symbol' é obrigatório"}), 400

    # Apaga o que tinha e salva só o novo
    salve_or_replace_sec(symbol)

    # Recupera do banco (só pra confirmar ou usar daqui pra frente)
    symbol_second = symbolo_saved_sec()

    # Busca os klines na Binance
    klines = get_timeframe_global()

    if not klines:
        return (
            jsonify({"erro": "Intervalo de tempo não encontrado no banco de dados"}),
            500,
        )

    try:
        if modo == "simulation":
            # 🔁 Limpa os dados antigos da tabela antes de salvar os novos
            clear_table_trend_clarifications_sec()
            # 🔁 Pega os dados do banco
            dados_brutos = get_data_klines_sec(symbol_second, klines)
            dados = formatar_dados_brutos(dados_brutos)

        else:
            clear_table_trend_clarifications_sec()
            # 🔁 Pega os dados em tempo real da Binance
            dados_brutos = client.get_klines(
                symbol=symbol_second, interval=klines, limit=1500
            )

    except Exception as e:
        print(f"❌ Erro Binance: {str(e)}")
        return jsonify({"erro": str(e)}), 500

    # Formata os dados e extrai preços de fechamento e temposs
    dados = formatar_dados_brutos(dados_brutos)
    closes = [item["Fechamento"] for item in dados]
    timestamps = [item["Tempo"] for item in dados]

    # Calcula o ATR suavizado
    atrs = calcular_atr_movel(dados, periodo=14)
    atr_suave = suavizar_atr(atrs, periodo=180)

    if not atr_suave:
        return jsonify({"erro": "ATR não pôde ser calculado."}), 400

    if klines == "15m":
        verify_time_multiply = 5
    else:
        verify_time_multiply = 4

    # Define os limites com base no ATR
    atr_ultima_suave = atr_suave[-1]["ATR_Suavizado"]
    atr_mult = atr_ultima_suave * verify_time_multiply

    # Aredonda os valores
    round_atr = round(atr_mult, 2)
    confir = round_atr / 2
    confir_round = round(confir, 2)

    limite = round_atr
    confirmar = confir_round

    # Inicializa variáveis de controle
    cont = 0
    movimentos = []
    estado = "inicio"
    topo = closes[0]
    fundo = closes[0]
    ponto_referencia = closes[0]
    ponto_inicial = closes[0]
    tendencia_atual = None
    ultimo_pivot_alta = None
    ultimo_pivot_baixa = None
    ultimo_pivot_reacao_sec_alta = None
    ultimo_pivot_reacao_sec_baixa = None
    ultimo_pivot_rally_alta = None
    ultimo_pivot_rally_baixa = None
    ultimo_pivot_rally_alta_temp = None
    ultimo_pivot_rally_baixa_temp = None
    ultimo_pivot_reacao_sec_alta_temp = None
    ultimo_pivot_reacao_sec_baixa_temp = None

    # Primeiro ponto é sempre um Rally Natural Inicial
    movimentos.append(
        {
            "closeTime": timestamps[0],
            "closePrice": ponto_referencia,
            "tipo": "Rally Natural (inicial)",
        }
    )

    for i in range(1, len(closes)):
        preco = closes[i]
        tempo = timestamps[i]
        variacao = preco - ponto_referencia
        movimento_adicionado = False  # Controle para evitar duplicação
        cont += 1

        # === ESTADO INICIAL ===
        # Detecta início de tendência
        if estado == "inicio":
            if not movimento_adicionado and preco > ponto_referencia + limite:
                # Inicia tendência de alta
                estado = "tendencia_alta"
                tendencia_atual = "Alta"
                ultimo_pivot_alta = preco
                topo = preco
                ponto_referencia = preco
                movimentos.append(
                    {"closeTime": tempo, "closePrice": preco, "tipo": "Tendência Alta"}
                )
                movimento_adicionado = True

            elif not movimento_adicionado and preco < ponto_referencia - limite:
                # Inicia tendência de baixa
                estado = "tendencia_baixa"
                tendencia_atual = "Baixa"
                ultimo_pivot_baixa = preco
                fundo = preco
                ponto_referencia = preco
                movimentos.append(
                    {"closeTime": tempo, "closePrice": preco, "tipo": "Tendência Baixa"}
                )
                movimento_adicionado = True

        # === TENDÊNCIA DE ALTA ===
        elif not movimento_adicionado and estado == "tendencia_alta":
            if preco > topo:
                # Continua tendência de alta
                topo = preco
                ultimo_pivot_alta = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Tendência Alta (topo)",
                    }
                )
                movimento_adicionado = True
            elif not movimento_adicionado and preco < topo - limite:
                # Transição para reação natural (correção)
                estado = "reacao_natural"
                fundo = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Reação Natural (Alta)",
                    }
                )
                movimento_adicionado = True

        # === TENDÊNCIA DE BAIXA ===
        elif not movimento_adicionado and estado == "tendencia_baixa":
            if preco < fundo:
                # Continua tendência de baixa
                fundo = preco
                ultimo_pivot_baixa = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Tendência Baixa (fundo)",
                    }
                )
                movimento_adicionado = True
            elif not movimento_adicionado and preco > fundo + limite:
                # Transição para reação natural (correção)
                estado = "reacao_natural"
                topo = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Reação Natural (Baixa)",
                    }
                )
                movimento_adicionado = True

        # === REAÇÃO NATURAL ===
        elif estado == "reacao_natural":
            if tendencia_atual == "Alta":
                # Vindo de tendência de alta
                if not movimento_adicionado and preco < fundo:
                    # Continuação da reação
                    fundo = preco
                    ultimo_pivot_rally_alta_temp = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação Natural (fundo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_alta
                ):
                    # Rally Natural (recuperacao)
                    estado = "rally_natural"
                    topo = preco
                    ultimo_pivot_rally_alta = ultimo_pivot_rally_alta_temp
                    ultimo_pivot_rally_baixa = None
                    ponto_inicial = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (Alta)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ponto_inicial is not None
                    and preco < ponto_inicial - confirmar
                ):
                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_inicial = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):

                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and preco < ultimo_pivot_baixa - confirmar
                ):

                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True

            elif tendencia_atual == "Baixa":
                # Vindo de tendência baixa
                if not movimento_adicionado and preco > topo:
                    # Continuação da reação
                    topo = preco
                    ultimo_pivot_rally_baixa_temp = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação Natural (topo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_baixa
                ):
                    # Rally Natural (respiro de baixa)
                    estado = "rally_natural"
                    fundo = preco
                    ultimo_pivot_rally_baixa = ultimo_pivot_rally_baixa_temp
                    ultimo_pivot_rally_alta = None
                    ponto_inicial = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (Baixa)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and preco < ultimo_pivot_baixa - confirmar
                ):
                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ponto_inicial is not None
                    and preco > ponto_inicial + confirmar
                ):
                    # Reversão para tendência de alta
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_inicial = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (reversão)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (reversão)",
                        }
                    )
                    movimento_adicionado = True

        # === RALLY NATURAL ===
        elif estado == "rally_natural":
            if tendencia_atual == "Alta":
                # Vindo de tendência alta
                if (
                    not movimento_adicionado
                    and preco > topo
                    and preco < ultimo_pivot_alta
                ):
                    # Continuação do rally
                    topo = preco
                    ultimo_pivot_reacao_sec_alta_temp = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (topo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    # Retomada da tendência de alta
                    estado = "tendencia_alta"
                    ultimo_pivot_alta = preco
                    tendencia_atual = "Alta"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (retomada)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_rally_alta
                ):
                    estado = "reacao_secundaria"
                    fundo = preco
                    ultimo_pivot_reacao_sec_alta = ultimo_pivot_reacao_sec_alta_temp
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Alta)",
                        }
                    )
                    movimento_adicionado = True
            elif tendencia_atual == "Baixa":
                # Vindo de tendência baixa
                if (
                    not movimento_adicionado
                    and preco < fundo
                    and preco > ultimo_pivot_baixa
                ):
                    # Continuação do rally
                    fundo = preco
                    ponto_referencia = preco
                    ultimo_pivot_reacao_sec_baixa_temp = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (fundo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado and preco < ultimo_pivot_baixa - confirmar
                ):
                    # Retomada da tendência de baixa
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (retomada)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    # Reversão para tendência de alta
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (reversão)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_rally_baixa
                ):
                    estado = "reacao_secundaria"
                    topo = preco
                    ultimo_pivot_reacao_sec_baixa = ultimo_pivot_reacao_sec_baixa_temp
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Baixa)",
                        }
                    )
                    movimento_adicionado = True

        # ======== Reação secundária ===========
        elif estado == "reacao_secundaria":
            if tendencia_atual == "Alta":
                if not movimento_adicionado and preco < fundo:
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Fundo)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_alta is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_reacao_sec_alta
                ):
                    # rally secundário
                    estado = "rally_secundario"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundário (Alta)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_alta is not None
                    and preco > fundo + limite
                    and preco > ultimo_pivot_reacao_sec_alta
                    and preco < ultimo_pivot_alta
                ):
                    #  volta ao rally
                    estado = "rally_natural"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (retorno)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (retorno)",
                        }
                    )
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    ultimo_pivot_baixa = preco
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True

            elif tendencia_atual == "Baixa":
                # vindo de tendência de baixa
                if not movimento_adicionado and preco > topo:
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (topo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_reacao_sec_baixa
                ):
                    #  volta ao rally
                    estado = "rally_secundario"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundário (Baixa)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco < topo - limite
                    and preco < ultimo_pivot_reacao_sec_baixa
                    and preco > ultimo_pivot_baixa
                ):
                    #  volta ao rally
                    estado = "rally_natural"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (retorno)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and ultimo_pivot_baixa
                    and preco < ultimo_pivot_baixa - confirmar
                ):
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    ultimo_pivot_baixa = preco
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (retomada)",
                        }
                    )
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (reversão)",
                        }
                    )
                    movimento_adicionado = True

            # ======== Reação secundária ===========
        elif estado == "rally_secundario":
            if tendencia_atual == "Alta":
                if not movimento_adicionado and preco > topo:
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundária (Topo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_reacao_sec_alta
                ):
                    estado = "reacao_secundaria"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Alta)",
                        }
                    )
                    movimento_adicionado = True
                    # retorno do rally secundario para reacao
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_alta is not None
                    and preco > ultimo_pivot_reacao_sec_alta + confirmar
                    and preco < ultimo_pivot_alta
                ):
                    estado = "rally_natural"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (retorno)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_rally_alta
                ):
                    estado = "reacao_secundaria"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True

            elif tendencia_atual == "Baixa":
                # vindo de tendência de baixa
                if not movimento_adicionado and preco < fundo:
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundária (Fundo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_reacao_sec_baixa
                ):
                    estado = "reacao_secundaria"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Baixa)",
                        }
                    )
                    movimento_adicionado = True
                    # retorno do rally secundario para reacao
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco < ultimo_pivot_reacao_sec_baixa - confirmar
                    and preco > ultimo_pivot_baixa
                ):
                    estado = "rally_natural"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (retorno)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco > ultimo_pivot_baixa
                    and preco < ultimo_pivot_reacao_sec_baixa - confirmar
                ):
                    # volta Rally natural
                    estado = "rally_natural"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (Baixa)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_rally_baixa
                ):
                    estado = "reacao_secundaria"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (reversão)",
                        }
                    )
                    movimento_adicionado = True

    # Cria lista de tuplas para bulk insert
    movimentos_para_salvar = []

    for p in movimentos:
        date = p["closeTime"]
        price = p["closePrice"]
        type = p["tipo"]

        # logger.info(
        #    f"Hora: {p['closeTime']} | Preço: {p['closePrice']} | Tipo: {p['tipo']}"
        # )

        movimentos_para_salvar.append((date, price, type))

    # Salva todos os dados de uma vez
    save_trend_clarifications_sec(movimentos_para_salvar)

    return jsonify(movimentos)


# ------------------------------------------------
# 2️⃣ Endpoint para pegar dados chaves da binance.
# ------------------------------------------------
@app.route("/api/filter_price_key", methods=["GET", "POST"])
def filter_price_key():
    modo = request.args.get("modo", "").strip().lower()
    symbol_primary = request.args.get("symbol") or symbolo_saved()
    symbol_second = request.args.get("symbol_sec") or symbolo_saved_sec()
    if not symbol_primary or not symbol_second:
        return jsonify({"erro": "Símbolos primário ou secundário não encontrados"}), 400

    time_frame = get_timeframe_global()

    if not time_frame:
        return (
            jsonify({"erro": "Intervalo de tempo não encontrado no banco de dados"}),
            500,
        )

    try:
        if modo == "simulation":
            # 🔁 Pega os dados do banco
            dados_pri_bruto = get_data_klines(symbol_primary, time_frame)
            dados_pri = formatar_dados_brutos(dados_pri_bruto)

            dados_sec_bruto = get_data_klines_sec(symbol_second, time_frame)
            dados_sec = formatar_dados_brutos(dados_sec_bruto)
        else:
            dados_pri_bruto = client.get_klines(
                symbol=symbol_primary,
                interval=time_frame,
                limit=1500,
            )
            dados_sec_bruto = client.get_klines(
                symbol=symbol_second,
                interval=time_frame,
                limit=1500,
            )
    except Exception as e:
        return jsonify({"erro": f"Falha ao obter dados da Binance: {str(e)}"}), 500

    # Formata os dados para extrair valores numéricos
    dados_pri = formatar_dados_brutos(dados_pri_bruto)
    dados_sec = formatar_dados_brutos(dados_sec_bruto)

    qtd_candles = min(len(dados_pri), len(dados_sec))
    movimentos = []

    fechamento_pri = dados_pri[0]["Fechamento"]
    fechamento_sec = dados_sec[0]["Fechamento"]

    # Garantir que nenhum dos valores seja zero
    if fechamento_pri == 0 or fechamento_sec == 0:
        raise ValueError("Fechamento inválido: zero encontrado.")

    # Calcula a proporção padronizada
    pd = max(fechamento_pri, fechamento_sec) / min(fechamento_pri, fechamento_sec)

    for i in range(qtd_candles):
        timestamp = dados_pri[i]["Tempo"]
        fechamento_a = dados_pri[i]["Fechamento"]
        fechamento_b = dados_sec[i]["Fechamento"]

        max_fech = max(fechamento_a, fechamento_b)
        min_fech = min(fechamento_a, fechamento_b)

        # Garante que nenhum é zero
        if min_fech == 0:
            continue
        pd = max_fech / min_fech
        # Ajusta somente o valor maior
        if fechamento_a > fechamento_b:
            fechamento_a_ajustado = fechamento_a / pd
            fechamento_b_ajustado = fechamento_b
        else:
            fechamento_a_ajustado = fechamento_a
            fechamento_b_ajustado = fechamento_b / pd

        soma = fechamento_a_ajustado + fechamento_b_ajustado

        movimentos.append(
            {
                "closeTime": timestamp,
                "closePrice": soma,
                "tipo": "Soma",
                "Tempo": timestamp,
                "Maximo": (
                    dados_pri[i]["Maximo"] / pd + dados_sec[i]["Maximo"]
                    if fechamento_a > fechamento_b
                    else dados_pri[i]["Maximo"] + dados_sec[i]["Maximo"] / pd
                ),
                "Minimo": (
                    dados_pri[i]["Minimo"] / pd + dados_sec[i]["Minimo"]
                    if fechamento_a > fechamento_b
                    else dados_pri[i]["Minimo"] + dados_sec[i]["Minimo"] / pd
                ),
                "Fechamento": soma,
            }
        )
    dados = movimentos
    closes = [item["closePrice"] for item in dados]
    timestamps = [item["closeTime"] for item in dados]

    # Calcula o ATR suavizado
    atrs = calcular_atr_movel(dados, periodo=14)
    atr_suave = suavizar_atr(atrs, periodo=180)

    if not atr_suave:
        return jsonify({"erro": "ATR não pôde ser calculado."}), 400

    if time_frame == "15m":
        verify_time_multiply = 5
    else:
        verify_time_multiply = 4

    # Define os limites com base no ATR
    atr_ultima_suave = atr_suave[-1]["ATR_Suavizado"]
    atr_mult = atr_ultima_suave * verify_time_multiply

    # Aredonda os valores
    round_atr = round(atr_mult, 2)
    confir = round_atr / 2
    confir_round = round(confir, 2)

    limite = round_atr
    confirmar = confir_round

    # === Inicialização dos estados ===
    movimentos = []
    estado = "inicio"
    topo = fundo = ponto_referencia = closes[0]
    tendencia_atual = None

    movimentos.append(
        {
            "closeTime": timestamps[0],
            "closePrice": ponto_referencia,
            "tipo": "Rally Natural (inicial)",
        }
    )

    # Inicializa variáveis de controle
    cont = 0
    movimentos = []
    estado = "inicio"
    topo = closes[0]
    fundo = closes[0]
    ponto_referencia = closes[0]
    ponto_inicial = closes[0]
    tendencia_atual = None
    ultimo_pivot_alta = None
    ultimo_pivot_baixa = None
    ultimo_pivot_reacao_sec_alta = None
    ultimo_pivot_reacao_sec_baixa = None
    ultimo_pivot_rally_alta = None
    ultimo_pivot_rally_baixa = None
    ultimo_pivot_rally_alta_temp = None
    ultimo_pivot_rally_baixa_temp = None
    ultimo_pivot_reacao_sec_alta_temp = None
    ultimo_pivot_reacao_sec_baixa_temp = None

    # Primeiro ponto é sempre um Rally Natural Inicial
    movimentos.append(
        {
            "closeTime": timestamps[0],
            "closePrice": ponto_referencia,
            "tipo": "Rally Natural (inicial)",
        }
    )

    for i in range(1, len(closes)):
        preco = closes[i]
        tempo = timestamps[i]
        variacao = preco - ponto_referencia
        movimento_adicionado = False  # Controle para evitar duplicação
        cont += 1

        # === ESTADO INICIAL ===
        # Detecta início de tendência
        if estado == "inicio":
            if not movimento_adicionado and preco > ponto_referencia + limite:
                # Inicia tendência de alta
                estado = "tendencia_alta"
                tendencia_atual = "Alta"
                ultimo_pivot_alta = preco
                topo = preco
                ponto_referencia = preco
                movimentos.append(
                    {"closeTime": tempo, "closePrice": preco, "tipo": "Tendência Alta"}
                )
                movimento_adicionado = True

            elif not movimento_adicionado and preco < ponto_referencia - limite:
                # Inicia tendência de baixa
                estado = "tendencia_baixa"
                tendencia_atual = "Baixa"
                ultimo_pivot_baixa = preco
                fundo = preco
                ponto_referencia = preco
                movimentos.append(
                    {"closeTime": tempo, "closePrice": preco, "tipo": "Tendência Baixa"}
                )
                movimento_adicionado = True

        # === TENDÊNCIA DE ALTA ===
        elif not movimento_adicionado and estado == "tendencia_alta":
            if preco > topo:
                # Continua tendência de alta
                topo = preco
                ultimo_pivot_alta = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Tendência Alta (topo)",
                    }
                )
                movimento_adicionado = True
            elif not movimento_adicionado and preco < topo - limite:
                # Transição para reação natural (correção)
                estado = "reacao_natural"
                fundo = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Reação Natural (Alta)",
                    }
                )
                movimento_adicionado = True

        # === TENDÊNCIA DE BAIXA ===
        elif not movimento_adicionado and estado == "tendencia_baixa":
            if preco < fundo:
                # Continua tendência de baixa
                fundo = preco
                ultimo_pivot_baixa = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Tendência Baixa (fundo)",
                    }
                )
                movimento_adicionado = True
            elif not movimento_adicionado and preco > fundo + limite:
                # Transição para reação natural (correção)
                estado = "reacao_natural"
                topo = preco
                ponto_referencia = preco
                movimentos.append(
                    {
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Reação Natural (Baixa)",
                    }
                )
                movimento_adicionado = True

        # === REAÇÃO NATURAL ===
        elif estado == "reacao_natural":
            if tendencia_atual == "Alta":
                # Vindo de tendência de alta
                if not movimento_adicionado and preco < fundo:
                    # Continuação da reação
                    fundo = preco
                    ultimo_pivot_rally_alta_temp = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação Natural (fundo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_alta
                ):
                    # Rally Natural (recuperacao)
                    estado = "rally_natural"
                    topo = preco
                    ultimo_pivot_rally_alta = ultimo_pivot_rally_alta_temp
                    ultimo_pivot_rally_baixa = None
                    ponto_inicial = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (Alta)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ponto_inicial is not None
                    and preco < ponto_inicial - confirmar
                ):
                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_inicial = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):

                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and preco < ultimo_pivot_baixa - confirmar
                ):

                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True

            elif tendencia_atual == "Baixa":
                # Vindo de tendência baixa
                if not movimento_adicionado and preco > topo:
                    # Continuação da reação
                    topo = preco
                    ultimo_pivot_rally_baixa_temp = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação Natural (topo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_baixa
                ):
                    # Rally Natural (respiro de baixa)
                    estado = "rally_natural"
                    fundo = preco
                    ultimo_pivot_rally_baixa = ultimo_pivot_rally_baixa_temp
                    ultimo_pivot_rally_alta = None
                    ponto_inicial = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (Baixa)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and preco < ultimo_pivot_baixa - confirmar
                ):
                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ponto_inicial is not None
                    and preco > ponto_inicial + confirmar
                ):
                    # Reversão para tendência de alta
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_inicial = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (reversão)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (reversão)",
                        }
                    )
                    movimento_adicionado = True

        # === RALLY NATURAL ===
        elif estado == "rally_natural":
            if tendencia_atual == "Alta":
                # Vindo de tendência alta
                if (
                    not movimento_adicionado
                    and preco > topo
                    and preco < ultimo_pivot_alta
                ):
                    # Continuação do rally
                    topo = preco
                    ultimo_pivot_reacao_sec_alta_temp = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (topo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    # Retomada da tendência de alta
                    estado = "tendencia_alta"
                    ultimo_pivot_alta = preco
                    tendencia_atual = "Alta"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (retomada)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_rally_alta
                ):
                    estado = "reacao_secundaria"
                    fundo = preco
                    ultimo_pivot_reacao_sec_alta = ultimo_pivot_reacao_sec_alta_temp
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Alta)",
                        }
                    )
                    movimento_adicionado = True
            elif tendencia_atual == "Baixa":
                # Vindo de tendência baixa
                if (
                    not movimento_adicionado
                    and preco < fundo
                    and preco > ultimo_pivot_baixa
                ):
                    # Continuação do rally
                    fundo = preco
                    ponto_referencia = preco
                    ultimo_pivot_reacao_sec_baixa_temp = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (fundo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado and preco < ultimo_pivot_baixa - confirmar
                ):
                    # Retomada da tendência de baixa
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (retomada)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    # Reversão para tendência de alta
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (reversão)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_rally_baixa
                ):
                    estado = "reacao_secundaria"
                    topo = preco
                    ultimo_pivot_reacao_sec_baixa = ultimo_pivot_reacao_sec_baixa_temp
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Baixa)",
                        }
                    )
                    movimento_adicionado = True

        # ======== Reação secundária ===========
        elif estado == "reacao_secundaria":
            if tendencia_atual == "Alta":
                if not movimento_adicionado and preco < fundo:
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Fundo)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_alta is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_reacao_sec_alta
                ):
                    # rally secundário
                    estado = "rally_secundario"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundário (Alta)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_alta is not None
                    and preco > fundo + limite
                    and preco > ultimo_pivot_reacao_sec_alta
                    and preco < ultimo_pivot_alta
                ):
                    #  volta ao rally
                    estado = "rally_natural"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (retorno)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (retorno)",
                        }
                    )
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    ultimo_pivot_baixa = preco
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    ultimo_pivot_baixa = preco
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True

            elif tendencia_atual == "Baixa":
                # vindo de tendência de baixa
                if not movimento_adicionado and preco > topo:
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (topo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_reacao_sec_baixa
                ):
                    #  volta ao rally
                    estado = "rally_secundario"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundário (Baixa)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco < topo - limite
                    and preco < ultimo_pivot_reacao_sec_baixa
                    and preco > ultimo_pivot_baixa
                ):
                    #  volta ao rally
                    estado = "rally_natural"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (retorno)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and ultimo_pivot_baixa
                    and preco < ultimo_pivot_baixa - confirmar
                ):
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    ultimo_pivot_baixa = preco
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (retomada)",
                        }
                    )
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (reversão)",
                        }
                    )
                    movimento_adicionado = True

            # ======== Reação secundária ===========
        elif estado == "rally_secundario":
            if tendencia_atual == "Alta":
                if not movimento_adicionado and preco > topo:
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundária (Topo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_reacao_sec_alta
                ):
                    estado = "reacao_secundaria"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Alta)",
                        }
                    )
                    movimento_adicionado = True
                    # retorno do rally secundario para reacao
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_alta is not None
                    and preco > ultimo_pivot_reacao_sec_alta + confirmar
                    and preco < ultimo_pivot_alta
                ):
                    estado = "rally_natural"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (retorno)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < topo - limite
                    and preco > ultimo_pivot_rally_alta
                ):
                    estado = "reacao_secundaria"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True

            elif tendencia_atual == "Baixa":
                # vindo de tendência de baixa
                if not movimento_adicionado and preco < fundo:
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundária (Fundo)",
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_reacao_sec_baixa
                ):
                    estado = "reacao_secundaria"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Baixa)",
                        }
                    )
                    movimento_adicionado = True
                    # retorno do rally secundario para reacao
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco < ultimo_pivot_reacao_sec_baixa - confirmar
                    and preco > ultimo_pivot_baixa
                ):
                    estado = "rally_natural"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (retorno)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco > ultimo_pivot_baixa
                    and preco < ultimo_pivot_reacao_sec_baixa - confirmar
                ):
                    # volta Rally natural
                    estado = "rally_natural"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally Natural (Baixa)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco > fundo + limite
                    and preco < ultimo_pivot_rally_baixa
                ):
                    estado = "reacao_secundaria"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (retomada)",
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    estado = "tendencia_alta"
                    tendencia_atual = "Alta"
                    topo = preco
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (reversão)",
                        }
                    )
                    movimento_adicionado = True

    logger.info("\n=== MOVIMENTOS CLASSIFICADOS ===")
    # Cria lista de tuplas para bulk insert
    movimentos_para_salvar = []

    for p in movimentos:
        date = p["closeTime"]
        price = p["closePrice"]
        type = p["tipo"]

        movimentos_para_salvar.append((date, price, type))
    logger.info("=================================\n")
    # Salva todos os dados de uma vez
    save_trend_clarifications_key(movimentos_para_salvar)

    return jsonify(movimentos)


# ==========================================================================
#                          Fim da classificação
# ==========================================================================


# -----------------------------------------------
# Função para retornar os pontos importantes.
# -----------------------------------------------
@app.route("/api/trend_clarifications", methods=["GET"])
def pivot_points():
    if request.method == "GET":
        points = important_points()
        return jsonify(points)


# --------------------------------------------------
# Função para retornar os pontos importantes chaves.
# --------------------------------------------------
@app.route("/api/trend_clarifications_key", methods=["GET"])
def pivot_points_key():
    if request.method == "GET":
        points = important_points_key()
        return jsonify(points)


@app.route("/")
def home():
    return "API ATR está rodando com sucesso!"
