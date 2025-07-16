from flask import Flask, jsonify
from flask_cors import CORS
from binance.client import Client
from datetime import datetime
import logging


client = Client()
app = Flask(__name__)
CORS(app)


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    app.run(debug=True)


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


def suavizar_atr(atrs, periodo=90):
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
    try:
        # Busca os dados brutos de preço na Binance
        dados_brutos = client.get_klines(
            symbol="ETHUSDT", interval=Client.KLINE_INTERVAL_1HOUR, limit=500
        )
    except Exception as e:
        return jsonify({"erro": f"Falha ao obter dados da Binance: {str(e)}"}), 1000

    # Formata os dados e extrai preços de fechamento e temposs
    dados = formatar_dados_brutos(dados_brutos)
    closes = [item["Fechamento"] for item in dados]
    timestamps = [item["Tempo"] for item in dados]

    # Calcula o ATR suavizado
    atrs = calcular_atr_movel(dados, periodo=14)
    atr_suave = suavizar_atr(atrs, periodo=90)

    if not atr_suave:
        return jsonify({"erro": "ATR não pôde ser calculado."}), 400

    # Define os limites com base no ATR
    atr_ultima_suave = atr_suave[-1]["ATR_Suavizado"]
    limite = int(atr_ultima_suave * 4)
    confirmar = limite / 2
    print(
        f"ATR Suavizado: {atr_ultima_suave:.2f} | Limite: {limite} | Confirmar: {confirmar}"
    )

    # Inicializa variáveis de controle
    movimentos = []
    estado = "inicio"
    topo = closes[0]
    fundo = closes[0]
    ponto_referencia = closes[0]
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
                topo = preco
                ponto_referencia = preco
                movimentos.append(
                    {"closeTime": tempo, "closePrice": preco, "tipo": "Tendência Alta"}
                )
                movimento_adicionado = True
            elif not movimento_adicionado and preco < ponto_referencia - limite:
                # Inicia tendência de baixa
                estado = "tendencia_baixa"
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
                        "tipo": "Reação Natural (de baixa)",
                    }
                )
                movimento_adicionado = True

        # === REAÇÃO NATURAL ===
        elif estado == "reacao_natural":
            if ultimo_pivot_alta is not None:
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
                elif not movimento_adicionado and preco > ultimo_pivot_alta + confirmar:
                    estado = "tendencia_alta"
                    ultimo_pivot_alta = None
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
                    fundo = preco
                    ultimo_pivot_baixa = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)",
                        }
                    )
                    movimento_adicionado = True

            elif ultimo_pivot_baixa is not None:
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
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    # Reversão para tendência de alta
                    estado = "tendencia_alta"
                    topo = preco
                    ultimo_pivot_alta = None
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
                    and ultimo_pivot_baixa is not None
                    and preco < ultimo_pivot_baixa - confirmar
                ):
                    # Reversão para tendência de baixa
                    estado = "tendencia_baixa"
                    fundo = preco
                    ultimo_pivot_baixa = None
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (retomada)",
                        }
                    )
                    movimento_adicionado = True

        # === RALLY NATURAL ===
        elif estado == "rally_natural":
            if ultimo_pivot_alta is not None:
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
                elif not movimento_adicionado and preco > ultimo_pivot_alta + confirmar:
                    # Retomada da tendência de alta
                    estado = "tendencia_alta"
                    ultimo_pivot_alta = None
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
                    fundo = preco
                    ultimo_pivot_baixa = None
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
            elif ultimo_pivot_baixa is not None:
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
                    ultimo_pivot_baixa = None
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
                    topo = preco
                    ultimo_pivot_alta = None
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
            if ultimo_pivot_alta is not None:
                if (
                    not movimento_adicionado
                    and preco < fundo
                    and preco > ultimo_pivot_rally_alta
                ):
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (fundo)",
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
                    and ultimo_pivot_rally_alta is not None
                    and preco < ultimo_pivot_rally_alta - confirmar
                ):
                    estado = "tendencia_baixa"
                    ultimo_pivot_baixa = None
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

            elif ultimo_pivot_baixa is not None:
                # vindo de tendência de baixa
                if (
                    not movimento_adicionado
                    and preco > topo
                    and preco < ultimo_pivot_rally_baixa
                ):
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append(
                        {
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Reação secundária (Topo)",
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
                    and ultimo_pivot_rally_baixa is not None
                    and preco > ultimo_pivot_rally_baixa + confirmar
                ):
                    estado = "tendencia_alta"
                    ultimo_pivot_alta = None
                    ultimo_pivot_rally_baixa = None
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
            if ultimo_pivot_alta is not None:
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
                elif (
                    not movimento_adicionado is not None
                    and ultimo_pivot_reacao_sec_alta
                    and preco < ultimo_pivot_alta
                    and preco > ultimo_pivot_reacao_sec_alta + confirmar
                ):
                    # volta Rally natural
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

            elif ultimo_pivot_baixa is not None:
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
                elif (
                    not movimento_adicionado is not None
                    and ultimo_pivot_reacao_sec_baixa
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

    # Exibe os movimentos classificados
    print("\n=== MOVIMENTOS CLASSIFICADOS ===")
    for p in movimentos:
        print(f"Hora: {p['closeTime']} | Preço: {p['closePrice']} | Tipo: {p['tipo']}")
    print("=================================\n")

    return jsonify(movimentos)


"""@app.route('/api/filter_price_atr_secondy', methods=["GET", "POST"])
def filter_price_atr_secondy():
    try:
        dados_brutos = client.get_klines(
            symbol="ETHUSDT", interval=Client.KLINE_INTERVAL_1HOUR, limit=5000
        )
    except Exception as e:
        return jsonify({"erro": f"Falha ao obter dados da Binance: {str(e)}"}), 500

    dados = formatar_dados_brutos(dados_brutos)
    closes = [item["Fechamento"] for item in dados]
    timestamps = [item["Tempo"] for item in dados]

    atrs = calcular_atr_movel(dados, periodo=30)
    atr_suave = suavizar_atr(atrs, periodo=30)

    if not atr_suave:
        return jsonify({"erro": "ATR não pôde ser calculado."}), 400
    
    atr_ultima_suave = atr_suave[-1]["ATR_Suavizado"]
    limite = int(atr_ultima_suave * 5)
    confirmar = limite / 2
    print(f"ATR Suavizado: {atr_ultima_suave:.2f} | Limite: {limite} | Confirmar: {confirmar}")

    movimentos = []
    estado = "inicio"
    topo = closes[0]
    fundo = closes[0]
    ponto_referencia = closes[0]
    ultimo_pivot_alta = None
    ultimo_pivot_baixa = None
    ultimo_pivot_reacao_alta = None
    ultimo_pivot_reacao_baixa = None

    movimentos.append({
        "closeTime": timestamps[0],
        "closePrice": ponto_referencia,
        "tipo": "Rally Natural (inicial)"
    })

    for i in range(1, len(closes)):
        preco = closes[i]
        tempo = timestamps[i]
        variacao = preco - ponto_referencia
        movimento_adicionado = False  # Controle para evitar duplicação

        print(f"→ [{estado.upper()}] Preço: {preco} | Ref: {ponto_referencia} | Var: {variacao:.2f} | Limite: {limite}")

        if estado == "inicio":
            if preco >= ponto_referencia + limite:
                estado = "tendencia_alta"
                topo = preco
                ultimo_pivot_alta = preco
                ponto_referencia = preco
                movimentos.append({
                    "closeTime": tempo,
                    "closePrice": preco,
                    "tipo": "Tendência Alta (topo)"
                })
                movimento_adicionado = True
            elif preco <= ponto_referencia - limite:
                estado = "tendencia_baixa"
                fundo = preco
                ultimo_pivot_baixa = preco
                ponto_referencia = preco
                movimentos.append({
                    "closeTime": tempo,
                    "closePrice": preco,
                    "tipo": "Tendência Baixa (fundo)"
                })
                movimento_adicionado = True

        elif estado == "tendencia_alta":
            if preco > topo:
                topo = preco
                ultimo_pivot_alta = preco
                ponto_referencia = preco
                movimentos.append({
                    "closeTime": tempo,
                    "closePrice": preco,
                    "tipo": "Tendência Alta (topo)"
                })
                movimento_adicionado = True
            elif preco <= topo - limite:
                estado = "reacao_natural"
                fundo = preco
                ponto_referencia = preco
                movimentos.append({
                    "closeTime": tempo,
                    "closePrice": preco,
                    "tipo": "Reação Natural (fundo)"
                })
                movimento_adicionado = True

        elif estado == "tendencia_baixa":
            if preco < fundo:
                fundo = preco
                ultimo_pivot_baixa = preco
                ponto_referencia = preco
                movimentos.append({
                    "closeTime": tempo,
                    "closePrice": preco,
                    "tipo": "Tendência Baixa (fundo)"
                })
                movimento_adicionado = True
            elif preco >= fundo + limite:
                estado = "reacao_natural"
                topo = preco
                ultimo_pivot_reacao_baixa = preco
                ponto_referencia = preco
                movimentos.append({
                    "closeTime": tempo,
                    "closePrice": preco,
                    "tipo": "Reação Natural (topo)"
                })
                movimento_adicionado = True

        elif estado == "reacao_natural":
            if ultimo_pivot_alta is not None:  # Vindo de tendência alta
                if not movimento_adicionado and preco < fundo:
                    fundo = preco
                    ultimo_pivot_reacao_alta = preco
                    ponto_referencia = preco
                    movimentos.append({
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Reação Natural (fundo)"
                    })
                    movimento_adicionado = True
                if ultimo_pivot_reacao_alta is not None and preco < ultimo_pivot_reacao_alta - (limite - confirmar):
                    estado = "tendencia_baixa"
                    ultimo_pivot_baixa = preco
                    ultimo_pivot_alta = None
                    if not movimento_adicionado:
                        movimentos.append({
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)"
                        })
                        movimento_adicionado = True
                elif not movimento_adicionado and preco > fundo + limite:
                    estado = "rally_natural"
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append({
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Rally Natural (topo)"
                    })
                    movimento_adicionado = True
            elif ultimo_pivot_baixa is not None:  # Vindo de tendência baixa
                if not movimento_adicionado and preco > topo:
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append({
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Reação Natural (topo)"
                    })
                    movimento_adicionado = True
                if ultimo_pivot_reacao_baixa is not None and preco > ultimo_pivot_reacao_baixa + (limite + confirmar):
                    estado = "tendencia_alta"
                    ultimo_pivot_alta = preco
                    ultimo_pivot_baixa = None
                    if not movimento_adicionado:
                        movimentos.append({
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (reversão)"
                        })
                        movimento_adicionado = True
                elif not movimento_adicionado and preco < topo - limite:
                    estado = "rally_natural"
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append({
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Rally Natural (fundo)"
                    })
                    movimento_adicionado = True

        elif estado == "rally_natural":
            if ultimo_pivot_alta is not None:  # Vindo de tendência alta
                if not movimento_adicionado and preco > topo:
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append({
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Rally Natural (topo)"
                    })
                    movimento_adicionado = True
                if preco > ultimo_pivot_alta:
                    estado = "tendencia_alta"
                    if not movimento_adicionado:
                        movimentos.append({
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (retomada)"
                        })
                        movimento_adicionado = True
                elif ultimo_pivot_reacao_alta is not None and preco < ultimo_pivot_reacao_alta - limite:
                    estado = "tendencia_baixa"
                    ultimo_pivot_baixa = preco
                    ultimo_pivot_alta = None
                    if not movimento_adicionado:
                        movimentos.append({
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (reversão)"
                        })
                        movimento_adicionado = True
                elif not movimento_adicionado and preco < fundo:
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append({
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Rally Natural (fundo)"
                    })
                    movimento_adicionado = True
            elif ultimo_pivot_baixa is not None:  # Vindo de tendência baixa
                if not movimento_adicionado and preco < fundo:
                    fundo = preco
                    ponto_referencia = preco
                    movimentos.append({
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Rally Natural (fundo)"
                    })
                    movimento_adicionado = True
                if preco < ultimo_pivot_baixa:
                    estado = "tendencia_baixa"
                    if not movimento_adicionado:
                        movimentos.append({
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Baixa (retomada)"
                        })
                        movimento_adicionado = True
                elif not movimento_adicionado and preco > topo:
                    topo = preco
                    ponto_referencia = preco
                    movimentos.append({
                        "closeTime": tempo,
                        "closePrice": preco,
                        "tipo": "Rally Natural (topo)"
                    })
                    movimento_adicionado = True
                elif ultimo_pivot_reacao_baixa is not None and preco > ultimo_pivot_reacao_baixa + limite:
                    estado = "tendencia_alta"
                    ultimo_pivot_alta = preco
                    ultimo_pivot_baixa = None
                    if not movimento_adicionado:
                        movimentos.append({
                            "closeTime": tempo,
                            "closePrice": preco,
                            "tipo": "Tendência Alta (reversão)"
                        })
                        movimento_adicionado = True


    logger.info("\n=== MOVIMENTOS CLASSIFICADOS ===")
    for p in movimentos:
        logger.info(f"Hora: {p['closeTime']} | Preço: {p['closePrice']} | Tipo: {p['tipo']}")
    logger.info("=================================\n")

    return jsonify(movimentos)

"""


@app.route("/")
def home():
    return "API ATR está rodando com sucesso!"
