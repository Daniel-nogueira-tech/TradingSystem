from flask import Flask, jsonify
from flask import request, jsonify
from flask_cors import CORS
from binance.client import Client
from datetime import datetime
import logging
from db import create_table, salve_or_replace, symbolo_saved


client = Client()
app = Flask(__name__)
CORS(app)


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    app.run(debug=True)

create_table()


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


# Endpoint principal
@app.route("/api/filter_price_atr", methods=["GET", "POST"])
def filter_price_atr():
    # Pega o símbolo do query string (ex: ?symbol=BTCUSDT)
    symbol = request.args.get("symbol", "").strip().upper()
    if not symbol:
        return jsonify({"erro": "Parâmetro 'symbol' é obrigatório"}), 400

    # 2) Apaga o que tinha e salva só o novo
    salve_or_replace(symbol)

    # 3) Recupera do banco (só pra confirmar ou usar daqui pra frente)
    symbol_primary = symbolo_saved()

    # 4) Busca os klines na Binance

    try:
        dados_brutos = client.get_klines(
            symbol=symbol_primary, interval=Client.KLINE_INTERVAL_1HOUR, limit=500
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

    # Define os limites com base no ATR
    atr_ultima_suave = atr_suave[-1]["ATR_Suavizado"]
    atr_mult = atr_ultima_suave * 4

    # Aredonda os valores
    round_atr = round(atr_mult, 2)
    confir = round_atr / 2
    confir_round = round(confir, 2)

    limite = round_atr
    confirmar = confir_round

    print(
        f"ATR Suavizado: {atr_ultima_suave:.2f} | Limite: {limite} | Confirmar: {confirmar}"
    )

    # Inicializa variáveis de controle
    movimentos = []
    estado = "inicio"
    topo = closes[0]
    fundo = closes[0]
    ponto_referencia = closes[0]
    tendencia_atual = None
    ultimo_pivot_alta = None
    ultimo_pivot_baixa = None
    ultimo_pivot_reacao_sec_alta = None
    ultimo_pivot_reacao_sec_baixa = None
    ultimo_pivot_rally_alta = closes[0]
    ultimo_pivot_rally_baixa = closes[0]

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

        print(
            f"→ [{estado.upper()}] Preço: {preco} | Ref: {ponto_referencia} | Var: {variacao:.2f} | Limite: {limite}"
        )

        # === ESTADO INICIAL ===
        # Detecta início de tendência
        if estado == "inicio":
            if not movimento_adicionado and preco > ponto_referencia + limite:
                # Inicia tendência de alta
                estado = "tendencia_alta"
                tendencia_atual = "Alta"
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
                    ultimo_pivot_rally_alta = preco
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
            elif tendencia_atual == "Baixa":
                # Vindo de tendência baixa
                if not movimento_adicionado and preco > topo:
                    # Continuação da reação
                    topo = preco
                    ultimo_pivot_rally_baixa = preco
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
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco > ultimo_pivot_reacao_sec_baixa
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
                    ultimo_pivot_reacao_sec_alta = preco
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
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária",
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
                    ultimo_pivot_reacao_sec_baixa = preco
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
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária",
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
                    #  volta ao rally
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
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
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
                    ultimo_pivot_rally_alta = preco
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
                    and ultimo_pivot_baixa is not None
                    and ultimo_pivot_baixa
                    and preco < ultimo_pivot_baixa - confirmar
                ):
                    estado = "tendencia_baixa"
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
                    ultimo_pivot_rally_baixa = preco
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
                            "tipo": "Reação secundária",
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
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True
                    print(f"ultimo rally: ", {ultimo_pivot_rally_alta})

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
                            "tipo": "Reação secundária",
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
                    print(f"reacao sec :", {ultimo_pivot_reacao_sec_baixa})
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
    for p in movimentos:
        logger.info(
            f"Hora: {p['closeTime']} | Preço: {p['closePrice']} | Tipo: {p['tipo']}"
        )
    logger.info("=================================\n")

    return jsonify(movimentos)


@app.route("/api/filter_price_atr_secondy", methods=["GET", "POST"])
def filter_price_atr_secondy():
    symbol = request.args.get("symbol", default="ETHUSDT").strip().upper()

    print(f"🔍 Recebido símbolo: '{symbol}'")

    try:
        dados_brutos = client.get_klines(
            symbol=symbol, interval=Client.KLINE_INTERVAL_1HOUR, limit=1500
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

    # Define os limites com base no ATR
    atr_ultima_suave = atr_suave[-1]["ATR_Suavizado"]
    atr_mult = atr_ultima_suave * 4

    # Aredonda os valores
    round_atr = round(atr_mult, 2)
    confir = round_atr / 2
    confir_round = round(confir, 2)

    limite = round_atr
    confirmar = confir_round

    # Inicializa variáveis de controle
    movimentos = []
    estado = "inicio"
    topo = closes[0]
    fundo = closes[0]
    ponto_referencia = closes[0]
    tendencia_atual = None
    ultimo_pivot_alta = None
    ultimo_pivot_baixa = None
    ultimo_pivot_reacao_sec_alta = None
    ultimo_pivot_reacao_sec_baixa = None
    ultimo_pivot_rally_alta = closes[0]
    ultimo_pivot_rally_baixa = closes[0]

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

        # === ESTADO INICIAL ===
        # Detecta início de tendência
        if estado == "inicio":
            if not movimento_adicionado and preco > ponto_referencia + limite:
                # Inicia tendência de alta
                estado = "tendencia_alta"
                tendencia_atual = "Alta"
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
                    ultimo_pivot_rally_alta = preco
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
                    and preco > fundo + limite
                    and preco < ultimo_pivot_alta
                ):
                    # Rally Natural (recuperacao)
                    estado = "rally_natural"
                    topo = preco
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
            elif tendencia_atual == "Baixa":
                # Vindo de tendência baixa
                if not movimento_adicionado and preco > topo:
                    # Continuação da reação
                    topo = preco
                    ultimo_pivot_rally_baixa = preco
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
                    and preco < topo - limite
                    and preco > ultimo_pivot_baixa
                ):
                    # Rally Natural (respiro de baixa)
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
                    and ultimo_pivot_baixa is not None
                    and preco < ultimo_pivot_baixa - confirmar
                ):
                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
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
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco > ultimo_pivot_reacao_sec_baixa
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
                    ultimo_pivot_reacao_sec_alta = preco
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
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária",
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
                    ultimo_pivot_reacao_sec_baixa = preco
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
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária",
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
                    #  volta ao rally
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
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
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
                    ultimo_pivot_rally_alta = preco
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
                    and ultimo_pivot_baixa is not None
                    and ultimo_pivot_baixa
                    and preco < ultimo_pivot_baixa - confirmar
                ):
                    estado = "tendencia_baixa"
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
                    ultimo_pivot_rally_baixa = preco
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
                            "tipo": "Reação secundária",
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
                            "tipo": "Reação secundária",
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
    try:
        dados_btc_bruto = client.get_klines(
            symbol="BTCUSDT", interval=Client.KLINE_INTERVAL_1HOUR, limit=1500
        )
        dados_eth_bruto = client.get_klines(
            symbol="ETHUSDT", interval=Client.KLINE_INTERVAL_1HOUR, limit=1500
        )
    except Exception as e:
        return jsonify({"erro": f"Falha ao obter dados da Binance: {str(e)}"}), 500

    dados_btc = formatar_dados_brutos(dados_btc_bruto)
    dados_eth = formatar_dados_brutos(dados_eth_bruto)

    qtd_candles = min(len(dados_btc), len(dados_eth))
    movimentos = []

    for i in range(qtd_candles):
        timestamp = dados_btc[i]["Tempo"]
        fechamento_btc = dados_btc[i]["Fechamento"]
        fechamento_eth = dados_eth[i]["Fechamento"]
        soma = fechamento_btc / 25 + fechamento_eth

        movimentos.append(
            {
                "closeTime": timestamp,
                "closePrice": soma,
                "tipo": "Soma BTC + ETH",
                "Tempo": timestamp,
                "Maximo": dados_btc[i]["Maximo"] / 25 + dados_eth[i]["Maximo"],
                "Minimo": dados_btc[i]["Minimo"] / 25 + dados_eth[i]["Minimo"],
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

    atr_ultima_suave = atr_suave[-1]["ATR_Suavizado"]
    atr_mult = atr_ultima_suave * 4

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
    movimentos = []
    estado = "inicio"
    topo = closes[0]
    fundo = closes[0]
    ponto_referencia = closes[0]
    tendencia_atual = None
    ultimo_pivot_alta = None
    ultimo_pivot_baixa = None
    ultimo_pivot_reacao_sec_alta = None
    ultimo_pivot_reacao_sec_baixa = None
    ultimo_pivot_rally_alta = closes[0]
    ultimo_pivot_rally_baixa = closes[0]

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

        # === ESTADO INICIAL ===
        # Detecta início de tendência
        if estado == "inicio":
            if not movimento_adicionado and preco > ponto_referencia + limite:
                # Inicia tendência de alta
                estado = "tendencia_alta"
                tendencia_atual = "Alta"
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
                    ultimo_pivot_rally_alta = preco
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
                    print(f"pivo :", {ultimo_pivot_alta})

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
            elif tendencia_atual == "Baixa":
                # Vindo de tendência baixa
                if not movimento_adicionado and preco > topo:
                    # Continuação da reação
                    topo = preco
                    ultimo_pivot_rally_baixa = preco
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
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa
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
                    ultimo_pivot_reacao_sec_alta = preco
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
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária",
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
                    ultimo_pivot_reacao_sec_baixa = preco
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
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária",
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
                    #  volta ao rally
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
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    estado = "tendencia_alta"
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
                elif (
                    not movimento_adicionado
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    estado = "tendencia_baixa"
                    tendencia_atual = "Baixa"
                    ultimo_pivot_rally_alta = preco
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
                    and ultimo_pivot_baixa is not None
                    and ultimo_pivot_baixa
                    and preco < ultimo_pivot_baixa - confirmar
                ):
                    estado = "tendencia_baixa"
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
                    ultimo_pivot_rally_baixa = preco
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
                    and ultimo_pivot_alta is not None
                    and preco > ultimo_pivot_alta + confirmar
                ):
                    tendencia_atual = "Alta"
                    estado = "tendencia_alta"
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
                    and ultimo_pivot_reacao_sec_alta is not None
                    and preco > ultimo_pivot_reacao_sec_alta + confirmar
                ):
                    tendencia_atual = "Alta"
                    estado = "tendencia_alta"
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
                            "tipo": "Rally Natural (retomada)",
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
                    and ultimo_pivot_baixa is not None
                    and preco > ultimo_pivot_baixa - confirmar
                ):
                    tendencia_atual = "Baixo"
                    estado = "tendencia_baixa"
                    fundo = preco
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
                    and ultimo_pivot_reacao_sec_baixa is not None
                    and preco > ultimo_pivot_reacao_sec_baixa - confirmar
                ):
                    tendencia_atual = "Baixa"
                    estado = "tendencia_baixa"
                    fundo = preco
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
                            "tipo": "Reação secundária",
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


@app.route("/")
def home():
    return "API ATR está rodando com sucesso!"
