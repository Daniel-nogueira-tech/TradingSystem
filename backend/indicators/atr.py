def calcular_atr_movel(dados, periodo=None):
    if len(dados) < periodo + 30:
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
        atrs.append({"index": i, "Tempo": dados[i]["Tempo"], "ATR": atr})
    return atrs


def suavizar_atr(atrs, periodo=None):
    if len(atrs) < periodo:
        return []

    atr_suavizado = []
    for i in range(periodo - 1, len(atrs)):
        soma = sum([atrs[j]["ATR"] for j in range(i - periodo + 1, i + 1)])
        media = soma / periodo
        atr_suavizado.append({"Tempo": atrs[i]["Tempo"], "ATR_Suavizado": media})
    return atr_suavizado
