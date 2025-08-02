from flask import Flask, jsonify
from flask import request, jsonify
from flask_cors import CORS
from binance.client import Client
from datetime import datetime, timedelta, timezone
import time
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
)


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
create_table_trend_clarifications_key()
clear_table_trend_clarifications_key()
init_db()


# Função para formatar os dados brutos da API da Binance
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


# Função para calcular ATR
def calcular_atr_movel(dados, periodo=14):
    if len(dados) < periodo + 1:
        print("Poucos dados para calcular ATR móvel.")
        return []

    atrs = []
    for i in range(periodo, len(dados)):
        true_ranges = []
        for j in range(i - periodo + 1, i + 1):
            high = dados[j]["Maximo"]
            low = dados[j]["Minimo"]
            close_anterior = dados[j - 1]["Fechamento"]

            tr = max(high - low, abs(high - close_anterior), abs(low - close_anterior))
            true_ranges.append(tr)

        atr = sum(true_ranges) / periodo
        atrs.append(
            {"index": i, "Tempo": dados[i]["Tempo"], "ATR": atr}  # <--- IMPORTANTE
        )

    return atrs


def suavizar_atr(atrs, periodo=180):
    if len(atrs) < periodo:
        return []

    atr_suavizado = []

    for i in range(periodo - 1, len(atrs)):
        soma = sum([atrs[j]["ATR"] for j in range(i - periodo + 1, i + 1)])
        media = soma / periodo
        atr_suavizado.append({"Tempo": atrs[i]["Tempo"], "ATR_Suavizado": media})
    return atr_suavizado


# 🔍 1️⃣ Consultar o último símbolo salvo
@app.route("/api/last_symbol", methods=["GET"])
def get_last_symbol():
    symbol = symbolo_saved()
    if symbol:
        return jsonify({"symbol": symbol}), 200
    else:
        return jsonify({"message": "Nenhum símbolo salvo"}), 404


# 1️⃣ Endpoint para mudar tempo grafico
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


# funcao para atualizar o klines salvos
@app.route("/api/update_klines", methods=["GET", "POST"])
def update_klines():
    symbol = request.args.get("symbol", "").strip().upper()
    if not symbol:
        return jsonify({"erro": "Parâmetro 'symbol' é obrigatório"}), 400

    salve_or_replace(symbol)  # salva no banco o símbolo atual
    timeFrame = get_timeframe_global().lower()
    print("📌 Intervalo usado:", timeFrame)

    try:
        download_and_save_klines(symbol, intervalo=timeFrame, dias=30)
        return jsonify({"mensagem": f"Dados de {symbol} atualizados com sucesso!"})
    except Exception as e:
        print(f"❌ Erro ao baixar/salvar klines: {str(e)}")
        return jsonify({"erro": str(e)}), 500


# =============================================
# 📊 Guarda no banco de dados dados do ativo
# ############################################
def download_and_save_klines(symbol, intervalo, dias=30, clean_before=True):
    if clean_before:
        Delete_all_Klines(symbol, intervalo)

    start_ms = int(
        (datetime.now(timezone.utc) - timedelta(days=dias)).timestamp() * 1000
    )

    all_klines = []
    while True:
        batch = client.get_klines(
            symbol=symbol, interval=intervalo, startTime=start_ms, limit=1500
        )
        if not batch:
            break
        all_klines.extend(batch)
        start_ms = batch[-1][0] + 1
        time.sleep(0.3)

    klines_formatados = [tuple(k[:11]) for k in all_klines]

    conn = conectar()
    save_klines(
        conn, symbol, intervalo, klines_formatados
    )  # agora vai com o valor correto
    conn.close()


# 1️⃣ Endpoint primario
@app.route("/api/filter_price_atr", methods=["GET", "POST"])
def filter_price_atr():
    symbol = request.args.get("symbol", "").strip().upper()
    if not symbol:
        return jsonify({"erro": "Parâmetro 'symbol' é obrigatório"}), 400

    salve_or_replace(symbol)

    # 3) Recupera do banco (só pra confirmar ou usar daqui pra frente)
    symbol_primary = symbolo_saved()

    # 4) Busca os klines na Binance
    klines = get_timeframe_global()
    try:
        dados_brutos = client.get_klines(
            symbol=symbol_primary, interval=klines, limit=1500
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
                            "tipo": "Tendência Baixa (reversão ----------------)",
                        }
                    )
                    movimento_adicionado = True
                    print(f"pivo rally", {ultimo_pivot_rally_alta})
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

        logger.info(
            f"Hora: {p['closeTime']} | Preço: {p['closePrice']} | Tipo: {p['tipo']}"
        )

        movimentos_para_salvar.append((date, price, type))
    logger.info("=================================\n")
    # Salva todos os dados de uma vez
    save_trend_clarifications(movimentos_para_salvar)

    return jsonify(movimentos)


# 🔍 2️⃣Consultar o último símbolo salvo do ativo secundario
@app.route("/api/last_symbol_second", methods=["GET"])
def get_last_symbol_sec():
    symbol = symbolo_saved_sec()
    if symbol:
        return jsonify({"symbol": symbol}), 200
    else:
        return jsonify({"message": "Nenhum símbolo salvo"}), 404


# 2️⃣ End Pont para pegar dados secundarios
@app.route("/api/filter_price_atr_second", methods=["GET", "POST"])
def filter_price_atr_second():
    symbol = request.args.get("symbol").strip().upper()

    if not symbol:
        return jsonify({"erro": "Parâmetro 'symbol' é obrigatório"}), 400

    # 2) Apaga o que tinha e salva só o novo
    salve_or_replace_sec(symbol)

    # 3) Recupera do banco (só pra confirmar ou usar daqui pra frente)
    symbol_second = symbolo_saved_sec()

    # 4) Busca os klines na Binance
    klines = get_timeframe_global()

    if not klines:
        return (
            jsonify({"erro": "Intervalo de tempo não encontrado no banco de dados"}),
            500,
        )

    try:
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
                            "tipo": "Tendência Baixa (reversão ----------------)",
                        }
                    )
                    movimento_adicionado = True
                    print(f"pivo rally", {ultimo_pivot_rally_alta})
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

    return jsonify(movimentos)


@app.route("/api/filter_price_key", methods=["GET", "POST"])
def filter_price_key():

    symbol_primary = symbolo_saved()
    symbol_second = symbolo_saved_sec()

    if not symbol_primary or not symbol_second:
        return jsonify({"erro": "Símbolos primário ou secundário não encontrados"}), 400

    klines = get_timeframe_global()

    if not klines:
        return (
            jsonify({"erro": "Intervalo de tempo não encontrado no banco de dados"}),
            500,
        )

    try:
        dados_btc_bruto = client.get_klines(
            symbol=symbol_primary,
            interval=klines,
            limit=1500,
        )
        dados_eth_bruto = client.get_klines(
            symbol=symbol_second,
            interval=klines,
            limit=1500,
        )
    except Exception as e:
        return jsonify({"erro": f"Falha ao obter dados da Binance: {str(e)}"}), 500

    # Formata os dados para extrair valores numéricos
    dados_pri = formatar_dados_brutos(dados_btc_bruto)
    dados_sec = formatar_dados_brutos(dados_eth_bruto)

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
                    print(f"pivo rally", {ultimo_pivot_rally_alta})
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


# ==============================================
# funcao para retornar os pontos inportantes
# ##############################################
@app.route("/api/trend_clarifications", methods=["GET"])
def trend_clarifications():
    if request.method == "GET":
        points = important_points()
        return jsonify(points)


# ==================================================
# funcao para retornar os pontos inportantes chaves
# ##################################################
@app.route("/api/trend_clarifications_key", methods=["GET"])
def trend_clarifications_key():
    if request.method == "GET":
        points = important_points_key()
        return jsonify(points)


@app.route("/")
def home():
    return "API ATR está rodando com sucesso!"
