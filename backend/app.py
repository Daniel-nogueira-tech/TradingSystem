from flask import Flask, jsonify,request, jsonify
from flask_cors import CORS
import json
from binance.client import Client
import logging
import re
from db import (
    create_table,
    salve_or_replace,
    symbolo_saved,
    create_table_timeframe_global,
    get_timeframe_global,
    create_table_trend_clarifications,
    important_points,
    init_db,
    get_trend_clarifications,
    get_date_simulation,
    init_db_rsi,
    save_rsi,
    get_data_rsi,
    ini_db_vppr,
    save_vppr,
    get_data_vppr,
    init_db_atr,
    save_market_observations,
    get_latest_market_by_symbol,
    remover_symbol,
    get_all_symbols,
    get_complete_data_market_observations,
    init_db_correlation,
    get_complete_data_candles_simulation,
     get_complete_data_candles
)
from indicators.rsi import get_rsi
from indicators.vppr import get_vppr , get_vppr_correlation
from klines.klines import  format_raw_data
from klines.Market_observation import get_klines_observation, format_raw_data
from price_variation.price_variation import add_price_variation
from indicators.correlation import calculate_correlation_matrix,highest_correlation_value
from trend_clarifications.trend_clarifications import trend_clarifications_atr
from download_simulation.download_simulation import download_and_save_klines,download_and_save_klines
from download_simulation.download_correlation import download_and_save_klines_correlation

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
calculate_correlation_matrix()
init_db_correlation()


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

    if not symbol:
        return jsonify({"erro": "Parâmetro 'symbol' é obrigatório"}), 400

    if not re.fullmatch(r"[A-Z]{5,12}", symbol) or not symbol.endswith("USDT"):
        return jsonify({"error": "Símbolo inválido"}), 400

    data = get_vppr(
        symbol,
        modo=modo,
        offset=offset,
        limit=limit,
    )

    data_correlation = get_vppr_correlation(
        symbol,
        modo=modo,
        offset=offset,
        limit=limit,
    )

    combined_data = []
    if not data_correlation:
        combined_data = data
    else:
        data_dict = {
           item["time"]: {
               "vppr": float(item.get("vppr", 0)),
               "vppr_ema": float(item.get("vppr_ema", 0)),
           }
           for item in data
        }

        corr_dict = {
           item["time"]: {
               "vppr": float(item.get("vppr", 0)),
               "vppr_ema": float(item.get("vppr_ema", 0)),
           }
           for item in data_correlation
        }

        common_times = data_dict.keys() & corr_dict.keys()

        for ts in sorted(common_times):
            combined_vppr = data_dict[ts]["vppr"] + corr_dict[ts]["vppr"]
            combined_vppr_ema = (
                data_dict[ts]["vppr_ema"] + corr_dict[ts]["vppr_ema"]
            )
            combined_data.append({
                "time": ts,
                "vppr": combined_vppr,
                "vppr_ema": combined_vppr_ema,
            })

    save_vppr(combined_data)
    return jsonify(combined_data)


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
# 1️⃣ Função para (BAIXAR) o klines salvos para simular primeiro ativo
# ----------------------------------------------------------------------
@app.route("/api/update_klines", methods=["GET", "POST"])
def update_klines():
    symbol = str(request.args.get("symbol", "")).strip().upper()
    date_start = request.args.get("date_start", "").strip()
    date_end = request.args.get("date_end", "").strip()
    days = request.args.get("days", "").strip()
    

    if not symbol:
        return jsonify({"erro": "Parâmetro 'symbol' é obrigatório"}), 400
    if not re.fullmatch(r"[A-Z]{5,12}", symbol) or not symbol.endswith("USDT"):
        return jsonify({"error": "Símbolo inválido"}), 400

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


# ----------------------------------------------------------------------
# 1️⃣ Função para (BAIXAR) o klines salvos para simular ativo de correlação
# ----------------------------------------------------------------------
@app.route("/api/update_klines_correlation", methods=["GET", "POST"])
def update_klines_correlation():
    symbol = str(request.args.get("symbol", "")).strip().upper()
    date_start = request.args.get("date_start", "").strip()
    date_end = request.args.get("date_end", "").strip()
    days = request.args.get("days", "").strip()

    correlations= highest_correlation_value(symbol)
        
    if not correlations:
       return []
    top_symbol = correlations[0]["correlated_asset"]

    if not top_symbol :
        return jsonify({"erro": "Parâmetro 'symbol' é obrigatório"}), 400
    if not re.fullmatch(r"[A-Z]{5,12}", top_symbol) or not top_symbol.endswith("USDT"):
        return jsonify({"error": "Símbolo inválido"}), 400

    days = int(days) if days.isdigit() else None

    timeFrame = get_timeframe_global().lower()

    try:
        download_and_save_klines_correlation(
            top_symbol,
            intervalo=timeFrame,
            date_start=date_start,
            date_end=date_end,
            days=days,
        )
        return jsonify({"mensagem": f"Dados de {top_symbol} atualizados com sucesso!"})
    except Exception as e:
        print(f"❌ Erro ao baixar/salvar klines: {str(e)}")
        return jsonify({"erro": str(e)}), 500

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

    sliced_movements = movements[offset : offset + limit]

    data = [
        {
            "closeTime": m[0],
            "closePrice": m[1],
            "tipo": m[2],
            "limite": m[3],
        }
        for m in sliced_movements
    ]
    return jsonify(data)


# -------------------------------------------
# 📊 Pega as confirmações de entrada (Buy/Sell) com paginação
# -------------------------------------------
@app.route("/api/simulate_full", methods=["GET"])
def simulate_full():
    """Retorna dados completos (offset/limit)"""
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 100))
    
    candles = get_complete_data_candles_simulation(offset=offset, limit=limit)
    
    if not candles:
        return jsonify([])
    
    data = [
        {
            "tempo": r[0],
            "open": r[1],
            "high": r[2],
            "low": r[3],
            "close": r[4],
            "volume": r[5]
        }
        for r in candles
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
    if not re.fullmatch(r"[A-Z]{5,12}", symbol) or not symbol.endswith("USDT"):
        return jsonify({"error": "Símbolo inválido"}), 400

    try:
        movements = trend_clarifications_atr(symbol, modo)
        return jsonify(movements), 200
    except Exception as e:
        print(f"❌ Erro em filter_price_atr: {str(e)}")
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------
# Função para pegar os dados completos candle
# -----------------------------------------------
@app.route("/api/complete_data_candle", methods=["GET"])
def complete_data(): 
    try:
        candles =  get_complete_data_candles()

        if not candles:
           return jsonify([])

        data = [
        {
            "tempo": r[0],
            "open": r[1],
            "high": r[2],
            "low": r[3],
            "close": r[4],
            "volume": r[5]
        }
        for r in candles
        ]
        return jsonify(data), 200
    except Exception as e:
        print(f"❌ Erro em get_complete_data: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
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
    if not re.fullmatch(r"[A-Z]{5,12}", symbol) or not symbol.endswith("USDT"):
        return jsonify({"error": "Símbolo inválido"}), 400

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
        
        time_flame = get_timeframe_global()
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
                raw_data = get_klines_observation(symbol=symbol_clean, interval=time_flame, total=1500)
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
    
# pega dados de observação de mercado 
@app.route("/api/get_market_observation", methods=["POST"])
def get_market_observation():
    data = request.get_json()
    if not data or "symbol" not in data:
        return jsonify({"error": "Symbol não enviado"}), 400

    symbol = data["symbol"]
    result = get_complete_data_market_observations(symbol)

    return jsonify({"data": result})

#================================================================
# Pega dos dados calculados para matriz de correlação de pearson
#================================================================
@app.route("/api/get_correlation",methods=["GET"])
def get_correlation():
    result = calculate_correlation_matrix(window=30)
    if not result:
        return jsonify({"error": "Matriz de correlação vazia"}), 400
    
    return jsonify(result)

#pega símbolos correlacionados com ativo principal
@app.route("/api/get_symbols_with_correlation",methods=["GET"])
def symbols_with_correlation():

    symbol = request.args.get("symbol","BTCUSDT")
    result = highest_correlation_value(symbol)
    if not result or not symbol:
        return jsonify({"Error": "Ao pegar símbolos correlacionados."}),400
    if not re.fullmatch(r"[A-Z]{5,12}", symbol) or not symbol.endswith("USDT"):
        return jsonify({"error": "Símbolo inválido"}), 400
    
    return jsonify(result)

#================================================================
#☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆
#               Dados do usuário para simular 
#☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆
#================================================================
@app.route("/api/save_backtest_results", methods=["POST"])
def save_backtest():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dados de simulação não enviados"}), 400

    try:
        # salvar os dados de simulação no banco de dados
        return jsonify({"message": "Dados de simulação salvos com sucesso!"}), 200
    except Exception as e:
        print(f"❌ Erro ao salvar dados de simulação: {str(e)}")
        return jsonify({"error": f"Erro ao salvar dados de simulação: {str(e)}"}), 500




























@app.route("/")
def home():
    return "API ATR está rodando com sucesso!"


if __name__ == "__main__":
    app.run(debug=True)
