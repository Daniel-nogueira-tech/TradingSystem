import pandas as pd
from datetime import datetime
from db import get_timeframe_global, get_data_klines, symbolo_saved, save_rsi
from binance.client import Client

client = Client()


def calculate_rsi(closes, period=14):
    series = pd.Series(closes)
    delta = series.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))
    return rsi


def get_rsi(symbol, period=14, media_period=6, modo=None, offset=None, limit=None):
    time = get_timeframe_global()
    symbol_primary = symbolo_saved()

    try:
        if modo == "simulation":
            klines = get_data_klines(symbol_primary, time)
        else:
            klines = client.get_klines(symbol=symbol, interval=time, limit=1500)
    except Exception as e:
        print(f"❌ Erro ao buscar dados: {str(e)}")
        return []

    if not klines:
        return []

    closes = [float(k[4]) for k in klines]
    rsi_values = calculate_rsi(closes, period)
    rsi_ma = rsi_values.rolling(window=media_period).mean()

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

    # aplica offset/limit se vierem
    if offset is not None and limit is not None:
        result = result[offset : offset + limit]

    return result
