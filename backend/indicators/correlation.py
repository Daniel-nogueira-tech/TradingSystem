import json
import pandas as pd
import numpy as np
from db import get_all_market_observations_to_matrix, get_latest_market_by_symbol


def calculate_correlation_matrix(window=30):

    data = get_all_market_observations_to_matrix()
    if not data:
        return {"error": "Sem dados no banco"}
    
    price_frames = []
    
    for row in data:
        symbol = row["symbol"]
        notes = row["notes"]


        df = pd.DataFrame(notes)

        if "Tempo" not in df or "Fechamento" not in df:
            continue

        df = df[["Tempo", "Fechamento"]].copy()
        df["Fechamento"] = df["Fechamento"].astype(float)
        df.rename(columns={"Fechamento": symbol}, inplace=True)

        price_frames.append(df)

    # Merge progressivo por open_time
    merged = price_frames[0]

    if len(price_frames) < 2:
        return {"error": "Dados insuficientes para correlação"}

    for df in price_frames[1:]:
        merged = pd.merge(merged, df, on="Tempo", how="inner")

    merged = merged.sort_values("Tempo")

    # Remove linhas onde todos os preços são NaN
    merged = merged.dropna(how="all")

    # Agora remove linhas que tenham qualquer NaN antes de calcular retorno
    merged = merged.dropna()
  
    # Calcula log-retornos
    returns = np.log(merged.drop(columns=["Tempo"]) /
                     merged.drop(columns=["Tempo"]).shift(1))

    # Usa apenas últimos N períodos
    returns = returns.tail(window)

    # Matriz de correlação
    corr_matrix = returns.corr()

    symbols = corr_matrix.columns.tolist()

    matrix = corr_matrix.values.tolist()
    return {
        "symbols": symbols,
        "matrix": matrix
    }

#pega o simbolos com correlação 
def highest_correlation_value(symbol, threshold=0.75, window=90):
    result = calculate_correlation_matrix(window=window)

    if "error" in result:
        return result

    # 🔹 Pega apenas último registro de cada ativo
    latest_data = get_latest_market_by_symbol()

    # 🔹 Cria mapa rápido: symbol -> variacao_pct
    latest_map = {
        item["symbol"]: item["variacao_pct"]
        for item in latest_data
    }

    symbols = result["symbols"]
    matrix = np.array(result["matrix"])

    if symbol not in symbols:
        return {"error": f"Símbolo {symbol} não encontrado na matriz"}

    index = symbols.index(symbol)

    correlations = []

    for i, other_symbol in enumerate(symbols):
        if other_symbol == symbol:
            continue

        value = matrix[index][i]

        if value >= threshold:
            correlations.append({
                "base_asset": symbol,
                "correlated_asset": other_symbol,
                "correlation": round(float(value), 4),
                "variacao_pct": latest_map.get(other_symbol)
            })

    correlations.sort(key=lambda x: x["correlation"], reverse=True)

    return correlations

