

def add_price_variation(data):
    previous_close = None

    for candle in data:
        close_price = candle.get("Fechamento")
        
        if previous_close is None:
            candle["variacao"] = 0.0
            candle["variacao_pct"] = 0.0
        else:
            variation = close_price - previous_close
            variation_pct = (variation / previous_close) * 100 if previous_close != 0 else 0

            candle["variacao"] = round(variation, 2)
            candle["variacao_pct"] = round(variation_pct, 4)

        previous_close = close_price

    return data