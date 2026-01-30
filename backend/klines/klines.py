from binance.client import Client
from datetime import datetime, timedelta, timezone


client = Client()


# --------------------------------------------------------
# Função genérica para buscar 3000+ candles
# --------------------------------------------------------
def get_klines_extended(symbol, interval, total=2000):
    all_klines = []
    limit = 1500
    end_time = None

    while len(all_klines) < total:
        klines = client.get_klines(
            symbol=symbol, interval=interval, limit=limit, endTime=end_time
        )

        if not klines:
            break

        # evita duplicar candles
        if all_klines and klines[-1][0] >= all_klines[0][0]:
            break

        all_klines = klines + all_klines

        # anda para trás no tempo
        end_time = klines[0][0] - 1

        # segurança contra loop infinito
        if len(klines) == 0:
            break

    return all_klines[-total:]


# --------------------------------------------------------
# Função para formatar os dados brutos da API da Binance
# --------------------------------------------------------
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
