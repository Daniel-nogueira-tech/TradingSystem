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
)
from indicators.atr import calcular_atr_movel, suavizar_atr
from indicators.rsi import get_rsi
from operation.operation import operation
from indicators.vppr import get_vppr
from klines.klines import get_klines_extended, formatar_dados_brutos

client = Client()
app = Flask(__name__)
CORS(app)


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


create_table()
create_table_trend_clarifications()
clear_table_trend_clarifications()
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
    limit = int(request.args.get("limit", 10))

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
    limit = int(request.args.get("limit", 10))

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
            dados_brutos = get_data_klines(symbol_primary, time)
            dados = formatar_dados_brutos(dados_brutos)

        else:
            clear_table_trend_clarifications()
            # 🔁 Pega os dados em tempo real da Binance
            dados_brutos = get_klines_extended(
                symbol=symbol_primary, interval=time, total=2160
            )
            dados = formatar_dados_brutos(dados_brutos)

    except Exception as e:
        print(f"❌ Erro Binance: {str(e)}")
        return jsonify({"erro": str(e)}), 500

    # Formata os dados e extrai preços de fechamento e tempos
    dados = formatar_dados_brutos(dados_brutos)
    closes = [item["Fechamento"] for item in dados]
    timestamps = [item["Tempo"] for item in dados]

    # Calcula o ATR suavizado
    atrs = calcular_atr_movel(dados)
    atr_suave = suavizar_atr(atrs)

    if not atr_suave:
        return jsonify({"erro": "ATR não pôde ser calculado."}), 400

    if time == "1d":
        verify_time_multiply = 5
    else:
        verify_time_multiply = 6

    # Define os limites com base no ATR
    atr_ultima_suave = get_atr_first_of_month()[-1][0]

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
    ultimo_pivot_rally_sec_baixa = None
    ultimo_pivot_rally_sec_temp_baixa = None
    ultimo_pivot_rally_sec_alta = None
    ultimo_pivot_rally_sec_temp_alta = None

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
        movimento_adicionado = False  # Controle para evitar duplicação
        cont += 1
        price = preco

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
                        "tipo": "Tendência Alta (compra)",
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
                        "tipo": "Tendência Baixa (venda)",
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
                ultimo_pivot_rally_alta_temp = preco
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
                ultimo_pivot_rally_baixa_temp = preco
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
                            "tipo": "Tendência Alta (compra)",
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
                            "tipo": "Tendência Baixa (venda)",
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
                            "tipo": "Tendência Baixa (venda)",
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
                            "tipo": "Tendência Baixa (venda)",
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
                            "tipo": "Tendência Baixa (venda)",
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
                            "tipo": "Tendência Alta (compra)",
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
                            "tipo": "Tendência Alta (compra)",
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
                            "tipo": "Tendência Alta (compra)",
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
                    ultimo_pivot_rally_sec_alta = ultimo_pivot_rally_sec_temp_alta
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
                            "tipo": "Tendência Alta (compra)",
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
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    estado = "tendencia_baixa"
                    fundo = preco
                    tendencia_atual = "Baixa"
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (venda)",
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
                    ultimo_pivot_rally_sec_baixa = ultimo_pivot_rally_sec_temp_baixa
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
                            "tipo": "Tendência Baixa (venda)",
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
                    topo = preco
                    tendencia_atual = "Alta"
                    ultimo_pivot_alta = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (compra)",
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
                    and preco > ultimo_pivot_reacao_sec_alta + confirmar
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
                            "tipo": "Tendência Alta (compra)",
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
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_sec_alta is not None
                    and preco < ultimo_pivot_rally_sec_alta - confirmar
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
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

            elif tendencia_atual == "Baixa":
                # vindo de tendência de baixa
                if not movimento_adicionado and preco > topo:
                    topo = preco
                    ultimo_pivot_rally_sec_temp_baixa = topo
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
                    tendencia_atual = "Baixa"
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
                    and preco < ultimo_pivot_reacao_sec_baixa - confirmar
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
                            "tipo": "Tendência Baixa (venda)",
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
                            "tipo": "Tendência Alta (compra)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_sec_baixa is not None
                    and preco > ultimo_pivot_rally_sec_baixa + confirmar
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
                            "tipo": "Tendência Alta (compra)",
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
                    ultimo_pivot_rally_sec_alta = ultimo_pivot_rally_sec_temp_alta

                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundário (Topo)",
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
                            "tipo": "Reação secundária",
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
                            "tipo": "Tendência Alta (compra)",
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
                            "tipo": "Tendência Baixa (venda)",
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
                    fundo = preco
                    ultimo_pivot_baixa = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

            elif tendencia_atual == "Baixa":
                # vindo de tendência de baixa
                if not movimento_adicionado and preco < fundo:
                    fundo = preco
                    ultimo_pivot_rally_sec_baixa = ultimo_pivot_rally_sec_temp_baixa
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Rally secundário (Fundo)",
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
                # reverse trendUp
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
                            "tipo": "Tendência Alta (compra)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_baixa is not None
                    and preco < ultimo_pivot_baixa - confirmar
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
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limite,
                        }
                    )
                    movimento_adicionado = True

    # Cria lista de tuplas para bulk insert
    movimentos_para_salvar = []
    operation(movimentos)

    for p in movimentos:
        date = p["closeTime"]
        price = p["closePrice"]
        type = p["tipo"]
        atr = p["limite"]

        movimentos_para_salvar.append((date, price, type, atr))

    # Salva todos os dados de uma vez
    save_trend_clarifications(movimentos_para_salvar)

    return jsonify(movimentos)


# -----------------------------------------------
# Função para retornar os pontos importantes.
# -----------------------------------------------
@app.route("/api/trend_clarifications", methods=["GET"])
def pivot_points():
    if request.method == "GET":
        points = important_points()
        return jsonify(points)


@app.route("/")
def home():
    return "API ATR está rodando com sucesso!"


if __name__ == "__main__":
    app.run(debug=True)
