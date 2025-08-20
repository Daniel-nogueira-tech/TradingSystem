import pandas as pd
from datetime import datetime
from flask import request, jsonify
from db import get_timeframe_global, get_data_klines
from binance.client import Client


def calculate_rsi(closes, period=14):
    """
    Calcula o RSI dado uma lista de preços de fechamento.
    """
    series = pd.Series(closes)
    # Diferenças entre fechamentos consecutivos
    delta = series.diff()
    # Ganhos e perdas separados
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    # Médias móveis exponenciais (EMA)
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()

    # RS (Relative Strength)
    rs = avg_gain / avg_loss

    # RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def get_rsi_from_db(symbol, modo, period=14, media_period=6):
    modo == "simulation"
    time = get_timeframe_global()
    try:
        if modo == "simulation":
            # Busca dados já salvos no banco para simular
            klines = get_data_klines(symbol, time)
        else:
            # Busca da Binance
            klines = Client.get_klines(symbol=symbol, interval=time, limit=1500)
    except Exception as e:
        print(f"❌ Erro Binance: {str(e)}")
        return []

    if not klines:
        return []

    # extrair fechamentos
    closes = [float(k[4]) for k in klines]

    # calcular RSI
    rsi_values = calculate_rsi(closes, period)

    # 🔹 Calcula a média móvel do RSI
    rsi_ma = rsi_values.rolling(window=media_period).mean()

    # retorna junto com timestamp formatado
    result = []
    for k, rsi, ma in zip(klines, rsi_values, rsi_ma):
        timestamp = k[0] if isinstance(k[0], int) else int(k["open_time"])
        date_str = datetime.fromtimestamp(timestamp / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        result.append(
            {
                "time": date_str,
                "rsi": round(rsi, 2) if not pd.isna(rsi) else None,
                "rsi_ma": round(ma, 2) if not pd.isna(ma) else None,
            }
        )

    return result
