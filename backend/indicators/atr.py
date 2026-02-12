from db import save_atr


def calculate_moving_atr(data, period=5):
    if len(data) < period + 30:
        print("Poucos dados para calcular ATR móvel.")
        return []

    atrs = []
    for i in range(period, len(data)):
        true_ranges = []
        for j in range(i - period + 1, i + 1):
            high = data[j]["Maximo"]
            low = data[j]["Minimo"]
            close_anterior = data[j - 1]["Fechamento"]

            tr = max(high - low, abs(high - close_anterior), abs(low - close_anterior))
            true_ranges.append(tr)

        atr = sum(true_ranges) / period
        atrs.append({"index": i, "Tempo": data[i]["Tempo"], "ATR": atr})
    return atrs


def smooth_atr(atrs, period=365):
    if len(atrs) < period:
        return []

    atr_soft = []
    for i in range(period - 1, len(atrs)):
        sum_atr = sum([atrs[j]["ATR"] for j in range(i - period + 1, i + 1)])
        average = sum_atr / period
        atr_soft.append({"Tempo": atrs[i]["Tempo"], "atr_soft": average})
    save_atr(atr_soft)
    return atr_soft
