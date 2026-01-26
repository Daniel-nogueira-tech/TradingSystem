from binance.client import Client
import pandas as pd
from datetime import datetime
from db import get_timeframe_global, symbolo_saved, get_data_klines

client = Client()


def calculate_vppr(klines):
    vppr_values = []
    vppr_acumulado = 0

    for i, k in enumerate(klines):
        open_price = float(k[1])
        close_price = float(k[4])
        volume = float(k[5])

        delta = close_price - open_price
        vppr_candle = abs(delta) * volume

        if close_price < open_price:
            vppr_candle *= -1

        vppr_acumulado += vppr_candle
        vppr_values.append(vppr_acumulado)

    return vppr_values


def get_vppr(symbol, modo=None, offset=None, limit=None):
    time = get_timeframe_global()
    symbol = symbolo_saved()

    try:
        if modo == "simulation":
            klines = get_data_klines(symbol, time)
        else:
            klines = client.get_klines(symbol=symbol, interval=time, limit=1500)
    except Exception as e:
        print(f"❌ Erro ao buscar dados: {str(e)}")
        return []

    if not klines:
        return []

    vppr_values = calculate_vppr(klines)

    # transforma em Series
    vppr_series = pd.Series(vppr_values)
    # EMA do VPPR
    vppr_ema = vppr_series.ewm(span=200, adjust=False).mean()

    # formatar datas e price
    result = []
    for i, k in enumerate(klines):
        timestamp = int(k[0])
        date_vppr = datetime.fromtimestamp(timestamp / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        result.append(
            {
                "time": date_vppr,
                "vppr": round(vppr_values[i], 2),
                "vppr_ema": round(vppr_ema.iloc[i], 2),
                "open": round(float(k[1]), 2),
                "close": round(float(k[4]), 2),
                "volume": round(float(k[5]), 2),
            }
        )

    # aplica offset/limit se vierem
    if offset is not None and limit is not None:
        result = result[offset : offset + limit]

    return result
