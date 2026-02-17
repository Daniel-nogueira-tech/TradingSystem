from flask import Flask, jsonify,request, jsonify
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
import time
from db import (
    create_table,
    salve_or_replace,
    symbolo_saved,
    create_table_timeframe_global,
    get_timeframe_global,
    save_trend_clarifications,
    create_table_trend_clarifications,
    clear_table_trend_clarifications,
    important_points,
    init_db,
    save_klines,
    conectar,
    Delete_all_Klines,
    get_data_klines,
    get_trend_clarifications,
    get_date_simulation,
    init_db_rsi,
    save_rsi,
    get_data_rsi,
    ini_db_vppr,
    save_vppr,
    get_data_vppr,
    init_db_atr,
    get_atr_first_of_month,
    save_market_observations,
    get_latest_market_by_symbol,
    clear_table_amrsi,
    clear_table_vppr,
    remover_symbol,
    get_all_symbols,
    get_complete_data_market_observations
)
from indicators.atr import calculate_moving_atr, smooth_atr
from indicators.rsi import get_rsi
from operation.operation import operation
from indicators.vppr import get_vppr
from klines.klines import get_klines_extended, format_raw_data
from klines.Market_observation import get_klines_observation, format_raw_data
from price_variation.price_variation import add_price_variation


client = Client()
app = Flask(__name__)
CORS(app)


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


create_table()
create_table_trend_clarifications()
init_db()
init_db_rsi()
ini_db_vppr()
init_db_atr()



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
    limit = int(request.args.get("limit", 100))

    amrsi = get_data_rsi()

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
# Função simular RSI FIM
# --------------------------------


# ---------------------------------------------------------------
# Função para calcular vppr (Volume Price Pressure Ratio) INICIO
# ---------------------------------------------------------------
@app.route("/api/vppr", methods=["GET"])
def api_vppr():
    symbol = request.args.get("symbol", "BTCUSDT")
    modo = request.args.get("modo", "")
    offset = request.args.get("offset", type=int)
    limit = request.args.get("limit", type=int)

    data = get_vppr(
        symbol,
        modo=modo,
        offset=offset,
        limit=limit,
    )

    save_vppr(data)
    return jsonify(data)


# ---------------------------------------------------------------
# Função para calcular vppr (Volume Price Pressure Ratio) FIM
# ---------------------------------------------------------------


# ---------------------------------------------------------
# Função simular vppr (Volume Price Pressure Ratio) INICIO
# ---------------------------------------------------------


@app.route("/api/simulate_vppr", methods=["GET"])
def simulate_vppr():
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 100))

    vppr = get_data_vppr()

    if not vppr:
        # dados realmente não existem
        return jsonify([])

    vppr_fatiado = vppr[offset : offset + limit]

    dados = [
        {
            "time": m[0],
            "vppr": m[1],
            "vppr_ema": m[2],
        }
        for m in vppr_fatiado
    ]
    return jsonify(dados)


# ---------------------------------------------------------
# Função simular vppr (Volume Price Pressure Ratio) FIM
# ---------------------------------------------------------


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
        clear_table_trend_clarifications()
        clear_table_vppr()
        clear_table_amrsi()

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
    limit = int(request.args.get("limit", 100))

    movements = get_trend_clarifications()

    if not movements:
        return jsonify([])  # Nada para simular

    sliced_movements =movements[offset : offset + limit]

    data = [
        {
            "closeTime": m[0],
            "closePrice": m[1],
            "tipo": m[2],
            "atr": m[3],
        }
        for m in sliced_movements
    ]
    return jsonify(data)


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
            raw_data = get_data_klines(symbol_primary, time)
            data = format_raw_data(raw_data)

        else:
            clear_table_trend_clarifications()
            # 🔁 Pega os dados em tempo real da Binance
            raw_data = get_klines_extended(
                symbol=symbol_primary, interval=time, total=2160
            )
            data = format_raw_data(raw_data)

    except Exception as e:
        print(f"❌ Erro Binance: {str(e)}")
        return jsonify({"erro": str(e)}), 500

    # Formata os dados e extrai preços de fechamento e tempos
    data = format_raw_data(raw_data)
    closes = [item["Fechamento"] for item in data]
    timestamps = [item["Tempo"] for item in data]

    # Calcula o ATR suavizado
    atrs = calculate_moving_atr(data)
    atr_suave = smooth_atr(atrs)

    if not atr_suave:
        return jsonify({"erro": "ATR não pôde ser calculado."}), 400

    if time == "1d":
        verify_time_multiply = 3
    else:
        verify_time_multiply = 5

    # Define os limites com base no ATR
    atr_ultima_suave = get_atr_first_of_month()[-1][0]

    atr_mult = atr_ultima_suave * verify_time_multiply

    # Aredonda os valores
    round_atr = round(atr_mult, 2)
    confir = round_atr / 2
    confir_round = round(confir, 2)

    limit = round_atr
    confirmar = confir_round

    # Inicializa variáveis de controle
    cont = 0
    movements = []
    state = "inicio"
    top = closes[0]
    bottom = closes[0]
    reference_point = closes[0]
    starting_point = closes[0]
    current_trend = None

    # pivos de tendencia
    last_pivot_high = None
    last_pivot_down = None

    # pivos de reação natural secundária
    last_pivot_reaction_sec_high = None
    last_pivot_reaction_sec_low = None
    last_pivot_reaction_sec_high_temp = None
    last_pivot_reaction_sec_low_temp = None

    # pivos de rally natural
    last_pivot_rally_high = None
    last_pivot_rally_low = None
    last_pivot_rally_high_temp = None
    last_pivot_rally_low_temp = None
    
    # pivos de reação secundária dentro do rally natural
    last_pivot_rally_sec_low = None
    last_pivot_rally_sec_low_temp = None
    last_pivot_rally_sec_high = None
    last_pivot_rally_sec_high_temp = None



    # Primeiro ponto é sempre um Rally Natural Inicial
    movements.append(
        {
            "closeTime": timestamps[0],
            "closePrice": reference_point,
            "tipo": "Rally Natural (inicial)",
            "limite": limit,
        }
    )

    for i in range(1, len(closes)):
        price = closes[i]
        tempo = timestamps[i]
        added_movement = False  # Controle para evitar duplicação
        cont += 1
        price = price
        # === ESTADO INICIAL ===
        # Detecta início de tendência
        if state == "inicio":
            if not added_movement and price > reference_point + limit:
                # Inicia tendência de alta
                state = "tendencia_alta"
                current_trend = "Alta"
                last_pivot_high = price
                top = price
                reference_point = price
                movements.append(
                    {
                        "closeTime": tempo,
                        "closePrice": price,
                        "tipo": "Tendência Alta (compra)",
                        "limite": limit,
                    }
                )
                added_movement = True

            elif not added_movement and price < reference_point - limit:
                # Inicia tendência de baixa
                state = "tendencia_baixa"
                current_trend = "Baixa"
                last_pivot_down = price
                bottom = price
                reference_point = price
                movements.append(
                    {
                        "closeTime": tempo,
                        "closePrice": price,
                        "tipo": "Tendência Baixa (venda)",
                        "limite": limit,
                    }
                )
                added_movement = True

        # === TENDÊNCIA DE ALTA ===
        elif not added_movement and state == "tendencia_alta":
            if price > top:
                # Continua tendência de alta
                top = price
                last_pivot_high = price
                reference_point = price
                movements.append(
                    {
                        "closeTime": tempo,
                        "closePrice": price,
                        "tipo": "Tendência Alta (topo)",
                        "limite": limit,
                    }
                )
                added_movement = True
            elif not added_movement and price < top - limit:
                # Transição para reação natural (correção)
                state = "reacao_natural"
                last_pivot_rally_high_temp = price
                bottom = price
                reference_point = price
                movements.append(
                    {
                        "closeTime": tempo,
                        "closePrice": price,
                        "tipo": "Reação Natural (Alta)",
                        "limite": limit,
                    }
                )
                added_movement = True

        # === TENDÊNCIA DE BAIXA ===
        elif not added_movement and state == "tendencia_baixa":
            if price < bottom:
                # Continua tendência de baixa
                bottom = price
                last_pivot_down = price
                reference_point = price
                movements.append(
                    {
                        "closeTime": tempo,
                        "closePrice": price,
                        "tipo": "Tendência Baixa (fundo)",
                        "limite": limit,
                    }
                )
                added_movement = True
            elif not added_movement and price > bottom + limit:
                # Transição para reação natural (correção)
                state = "reacao_natural"
                top = price
                last_pivot_rally_low_temp = price
                reference_point = price
                movements.append(
                    {
                        "closeTime": tempo,
                        "closePrice": price,
                        "tipo": "Reação Natural (Baixa)",
                        "limite": limit,
                    }
                )
                added_movement = True

        # === REAÇÃO NATURAL ===
        elif state == "reacao_natural":
            if current_trend == "Alta":
                # Vindo de tendência de alta
                if not added_movement and price < bottom:
                    # Continuação da reação
                    bottom = price
                    last_pivot_rally_high_temp = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação Natural (fundo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > bottom + limit
                    and price < last_pivot_high
                ):
                    # Rally Natural (recuperacao)
                    state = "rally_natural"
                    top = price
                    last_pivot_rally_high = last_pivot_rally_high_temp
                    last_pivot_rally_low = None
                    starting_point = None
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (Alta)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > last_pivot_high + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    last_pivot_high = price
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and starting_point is not None
                    and price < starting_point - confirmar
                ):
                    # Reversão para tendência de baixa
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    bottom = price
                    last_pivot_down = price
                    starting_point = None
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_rally_high is not None
                    and price < last_pivot_rally_high - confirmar
                ):

                    # Reversão para tendência de baixa
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_down is not None
                    and price < last_pivot_down - confirmar
                ):

                    # Reversão para tendência de baixa
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

            elif current_trend == "Baixa":
                # Vindo de tendência baixa
                if not added_movement and price > top:
                    # Continuação da reação
                    top = price
                    last_pivot_rally_low_temp = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação Natural (topo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_down is not None
                    and price < top - limit
                    and price > last_pivot_down
                ):
                    # Rally Natural (respiro de baixa)
                    state = "rally_natural"
                    bottom = price
                    last_pivot_rally_low = last_pivot_rally_low_temp
                    last_pivot_rally_high = None
                    starting_point = None
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (Baixa)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_down is not None
                    and price < last_pivot_down - confirmar
                ):
                    # Reversão para tendência de baixa
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and starting_point is not None
                    and price > starting_point + confirmar
                ):
                    # Reversão para tendência de alta
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    top = price
                    last_pivot_high = price
                    starting_point = None
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_rally_low is not None
                    and price > last_pivot_rally_low + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    top = price
                    last_pivot_high = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > last_pivot_high + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    top = price
                    last_pivot_high = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

        # === RALLY NATURAL ===
        elif state == "rally_natural":
            if current_trend == "Alta":
                # Vindo de tendência alta
                if (
                    not added_movement
                    and price > top
                    and price < last_pivot_high
                ):
                    # Continuação do rally
                    top = price
                    last_pivot_reaction_sec_high_temp = price
                    last_pivot_rally_sec_high = last_pivot_rally_sec_high_temp
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (topo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > last_pivot_high + confirmar
                ):
                    # Retomada da tendência de alta
                    state = "tendencia_alta"
                    last_pivot_high = price
                    current_trend = "Alta"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_rally_high is not None
                    and price < top - limit
                    and price > last_pivot_rally_high
                ):
                    state = "reacao_secundaria"
                    bottom = price
                    last_pivot_reaction_sec_high = last_pivot_reaction_sec_high_temp
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária (Alta)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_rally_high is not None
                    and price < last_pivot_rally_high - confirmar
                ):
                    state = "tendencia_baixa"
                    bottom = price
                    current_trend = "Baixa"
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                added_movement = True

            elif current_trend == "Baixa":
                # Vindo de tendência baixa
                if (
                    not added_movement
                    and price < bottom
                    and price > last_pivot_down
                ):
                    # Continuação do rally
                    bottom = price
                    reference_point = price
                    last_pivot_reaction_sec_low_temp = price
                    last_pivot_rally_sec_low = last_pivot_rally_sec_low_temp
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (fundo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement and price < last_pivot_down - confirmar
                ):
                    # Retomada da tendência de baixa
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_rally_low is not None
                    and price > bottom + limit
                    and price < last_pivot_rally_low
                ):
                    state = "reacao_secundaria"
                    top = price
                    last_pivot_reaction_sec_low = last_pivot_reaction_sec_low_temp
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_rally_low is not None
                    and price > last_pivot_rally_low + confirmar
                ):
                    state = "tendencia_alta"
                    top = price
                    current_trend = "Alta"
                    last_pivot_high = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                added_movement = True

        # ======== Reação secundária ===========
        elif state == "reacao_secundaria":
            if current_trend == "Alta":
                if not added_movement and price < bottom:
                    last_pivot_rally_sec_high_temp = bottom
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária (Fundo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_reaction_sec_high is not None
                    and price > bottom + limit
                    and price < last_pivot_reaction_sec_high
                ):
                    # rally secundário
                    state = "rally_secundario"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally secundário (Alta)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_reaction_sec_high is not None
                    and price > bottom + limit
                    and price > last_pivot_reaction_sec_high + confirmar
                    and price < last_pivot_high
                ):
                    #  volta ao rally
                    state = "rally_natural"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (retorno)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > last_pivot_high + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    last_pivot_high = price
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                elif (
                    not added_movement
                    and last_pivot_rally_high is not None
                    and price < last_pivot_rally_high - confirmar
                ):
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    last_pivot_down = price
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_rally_sec_high is not None
                    and price < last_pivot_rally_sec_high - confirmar
                ):
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    last_pivot_down = price
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

            elif current_trend == "Baixa":
                # vindo de tendência de baixa
                if not added_movement and price > top:
                    top = price
                    last_pivot_rally_sec_low_temp = top
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária (topo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price < top - limit
                    and price > last_pivot_reaction_sec_low
                ):
                    #  volta ao rally
                    state = "rally_secundario"
                    bottom = price
                    current_trend = "Baixa"
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally secundário (Baixa)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price < top - limit
                    and price < last_pivot_reaction_sec_low - confirmar
                    and price > last_pivot_down
                ):
                    #  volta ao rally
                    state = "rally_natural"
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (retorno)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_down is not None
                    and last_pivot_down
                    and price < last_pivot_down - confirmar
                ):
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    last_pivot_down = price
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_rally_low is not None
                    and price > last_pivot_rally_low + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    last_pivot_high = price
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_rally_sec_low is not None
                    and price > last_pivot_rally_sec_low + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    last_pivot_high = price
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                    

            # ======== Reação secundária ===========
        elif state == "rally_secundario":
            if current_trend == "Alta":
                if not added_movement and price > top:
                    top = price
                    reference_point = price
                    last_pivot_rally_sec_high = last_pivot_rally_sec_high_temp
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally secundário (Topo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price < top - limit
                    and price > last_pivot_reaction_sec_high
                ):
                    state = "reacao_secundaria"
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                    # retorno do rally secundario para reacao
                elif (
                    not added_movement
                    and last_pivot_reaction_sec_high is not None
                    and price > last_pivot_reaction_sec_high + confirmar
                    and price < last_pivot_high
                ):
                    state = "rally_natural"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (retorno)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > last_pivot_high + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    last_pivot_high = price
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_rally_high is not None
                    and price < top - limit
                    and price > last_pivot_rally_high
                ):
                    state = "reacao_secundaria"
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_rally_high is not None
                    and price < last_pivot_rally_high - confirmar
                ):
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > last_pivot_high + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

            elif current_trend == "Baixa":
                # vindo de tendência de baixa
                if not added_movement and price < bottom:
                    bottom = price
                    last_pivot_rally_sec_low = last_pivot_rally_sec_low_temp
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally secundário (Fundo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price > bottom + limit
                    and price < last_pivot_reaction_sec_low
                ):
                    state = "reacao_secundaria"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária (Baixa)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                    # retorno do rally secundario para reacao
                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price < last_pivot_reaction_sec_low - confirmar
                    and price > last_pivot_down
                ):
                    state = "rally_natural"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (retorno)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price > last_pivot_down
                    and price < last_pivot_reaction_sec_low - confirmar
                ):
                    # volta Rally natural
                    state = "rally_natural"
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (Baixa)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price > bottom + limit
                    and price < last_pivot_rally_low
                ):
                    state = "reacao_secundaria"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                # reverse trendUp
                elif (
                    not added_movement
                    and last_pivot_rally_low is not None
                    and price > last_pivot_rally_low + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    top = price
                    last_pivot_high = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_down is not None
                    and price < last_pivot_down - confirmar
                ):
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

    # Cria lista de tuplas para bulk insert
    movements_to_save = []
    operation(movements)

    for p in movements:
        date = p["closeTime"]
        price = p["closePrice"]
        type = p["tipo"]
        atr = p["limite"]

        movements_to_save.append((date, price, type, atr))

    # Salva todos os dados de uma vez
    save_trend_clarifications(movements_to_save)

    return jsonify(movements)


# -----------------------------------------------
# Função para retornar os pontos importantes.
# -----------------------------------------------
@app.route("/api/trend_clarifications", methods=["GET"])
def pivot_points():
    if request.method == "GET":
        points = important_points()
        return jsonify(points)

#======================================================
# função para retornar dados de observação do mercado
#======================================================
@app.route("/api/market_observation", methods=["POST"])
def market_observation():
    data = request.get_json() or {}

    symbol = data.get("symbol", "").strip().upper()
    total = data.get("total", 2000)

    if not symbol:
        return jsonify({"error": "Símbolo é obrigatório."}), 400

    time = get_timeframe_global()
    raw_data = get_klines_observation(symbol=symbol, interval=time, total=total)
    data = format_raw_data(raw_data)

# 👉 adiciona variação de preço
    formatted_data = add_price_variation(data)
    
    # Salva as observações de mercado no banco de dados
    save_market_observations(symbol, formatted_data)  
    return jsonify(formatted_data)



# pega os dados de observação de mercado mais recentes para um símbolo específico
@app.route("/api/latest_market_observation", methods=["GET"])
def latest_market_observation():
     market_observation = get_latest_market_by_symbol()
     return jsonify(market_observation)

@app.route("/api/remove_symbol_market_observation",methods=["POST"])
def delete_symbol_market_observation():
    data = request.get_json()

    if not data or "symbol" not in data:
       return jsonify({"error": "Symbol não enviado"}), 400

    symbol = data["symbol"]
    remover_symbol(symbol)

    return jsonify({"message": f"{symbol} removido com sucesso"})


@app.route("/api/update_market_observations", methods=["GET"])
def update_market_observations():
    """
    Atualiza observações de mercado para TODOS os símbolos salvos.
    Busca dados recentes da Binance e atualiza o banco em background.
    """
    try:
        symbols = get_all_symbols()
        
        if not symbols:
            return jsonify({
                "message": "Nenhum símbolo salvo para atualizar",
                "updated_symbols": []
            }), 200
        
        time = get_timeframe_global()
        updated_data = []
        
        for symbol in symbols:
            try:
                # Validação básica do símbolo
                if not symbol or not isinstance(symbol, str):
                    updated_data.append({
                        "symbol": symbol,
                        "status": "erro",
                        "error": "Símbolo inválido"
                    })
                    continue
                
                symbol_clean = symbol.strip().upper()
                
                # Busca os dados mais recentes da Binance
                raw_data = get_klines_observation(symbol=symbol_clean, interval=time, total=2000)
                data = format_raw_data(raw_data)
                
                # Adiciona variação de preço
                formatted_data = add_price_variation(data)
                
                # Salva as observações no banco
                save_market_observations(symbol_clean, formatted_data)
                
                updated_data.append({
                    "symbol": symbol_clean,
                    "status": "atualizado",
                    "total_candles": len(formatted_data)
                })
                
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Erro ao atualizar {symbol}: {error_msg}")
                updated_data.append({
                    "symbol": symbol,
                    "status": "erro",
                    "error": error_msg
                })
        
        return jsonify({
            "message": f"{sum(1 for x in updated_data if x['status'] == 'atualizado')} de {len(symbols)} símbolo(s) atualizado(s)",
            "updated_symbols": updated_data
        }), 200
        
    except Exception as e:
        print(f"❌ Erro geral em update_market_observations: {str(e)}")
        return jsonify({"error": f"Erro ao atualizar observações: {str(e)}"}), 500

@app.route("/api/get_market_observation", methods=["POST"])
def get_market_observation():
    data = request.get_json()

    if not data or "symbol" not in data:
        return jsonify({"error": "Symbol não enviado"}), 400

    symbol = data["symbol"]

    result = get_complete_data_market_observations(symbol)


    return jsonify({"data": result})

 






@app.route("/")
def home():
    return "API ATR está rodando com sucesso!"


if __name__ == "__main__":
    app.run(debug=True)
