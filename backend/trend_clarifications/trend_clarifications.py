from binance.client import Client
from db import (
    salve_or_replace,
    symbolo_saved,
    get_timeframe_global,
    save_trend_clarifications,
    clear_table_trend_clarifications,
    get_data_klines,
    get_atr_first_of_month,
)
from indicators.atr import calculate_moving_atr, smooth_atr
from operation.operation import operation
from klines.klines import get_klines_extended, format_raw_data
from klines.Market_observation import format_raw_data
from download_simulation.download_simulation import download_and_save_klines


client = Client()


def trend_clarifications_atr(symbol, modo):
    salve_or_replace(symbol)

    #  Recupera do banco (só pra confirmar ou usar daqui pra frente)
    symbol_primary = symbolo_saved()

    #  Busca os klines na Binance
    time = get_timeframe_global()
    try:
        if modo == "simulation":
            # 🔁 Limpa os dados antigos da tabela antes de salvar os novos
            clear_table_trend_clarifications()
            # 🔁 Pega os dados do banco
            raw_data = get_data_klines(symbol_primary, time)
            print(f"✅ raw_data carregado: {len(raw_data) if raw_data else 0} registros")
            
            # Se não houver dados, tenta fazer download automaticamente
            if not raw_data:
                print(f"⚠️ Nenhum dado local encontrado para {symbol_primary}. Baixando dados históricos...")
                try:
                    download_and_save_klines(
                        symbol_primary,
                        intervalo=time,
                        date_start=None,
                        date_end=None,
                        days=365,  # Baixa 365 dias de dados
                        clean_before=False
                    )
                    raw_data = get_data_klines(symbol_primary, time)
                    print(f"✅ Dados baixados com sucesso: {len(raw_data) if raw_data else 0} registros")
                except Exception as download_e:
                    raise ValueError(f"Não foi possível baixar dados: {str(download_e)}")
            
            if not raw_data:
                raise ValueError(f"Nenhum dado encontrado para {symbol_primary} {time}")
            
            data = format_raw_data(raw_data)
            print(f"✅ dados formatados: {len(data)} candles")

        else:
            clear_table_trend_clarifications()
            # 🔁 Pega os dados em tempo real da Binance
            raw_data = get_klines_extended(
                symbol=symbol_primary, interval=time, total=2160
            )
            data = format_raw_data(raw_data)

    except Exception as e:
        print(f"❌ Erro ao buscar klines: {str(e)}")
        raise Exception(f"Erro ao buscar klines: {str(e)}")

    # Extrai preços de fechamento e tempos
    closes = [item["Fechamento"] for item in data]
    timestamps = [item["Tempo"] for item in data]
    
    print(f"✅ closes: {len(closes)}, timestamps: {len(timestamps)}")

    # Calcula o ATR suavizado
    atrs = calculate_moving_atr(data)
    print(f"✅ ATRs calculados: {len(atrs) if atrs else 0}")
    
    atr_suave = smooth_atr(atrs)
    print(f"✅ ATR suavizado: {len(atr_suave) if atr_suave else 0}")

    if not atr_suave:
        raise ValueError("ATR não pôde ser calculado.")

    if time == "1d":
        verify_time_multiply = 3
    else:
        verify_time_multiply = 5

    # Define os limites com base no ATR
    atr_ultima_suave = get_atr_first_of_month()[-1][0]

    atr_mult = atr_ultima_suave * verify_time_multiply

    # Aredonda os valores
    round_atr = round(atr_mult, 2)
    confir = round_atr / 2
    confir_round = round(confir, 2)

    limit = round_atr
    confirmar = confir_round

    # Inicializa variáveis de controle
    cont = 0
    movements = []
    state = "inicio"
    top = closes[0]
    bottom = closes[0]
    reference_point = closes[0]
    starting_point = closes[0]
    current_trend = None

    # pivos de tendencia
    last_pivot_high = None
    last_pivot_down = None

    # pivos de reação natural secundária
    last_pivot_reaction_sec_high = None
    last_pivot_reaction_sec_low = None
    last_pivot_reaction_sec_high_temp = None
    last_pivot_reaction_sec_low_temp = None

    # pivos de rally natural
    last_pivot_rally_high = None
    last_pivot_rally_low = None
    last_pivot_rally_high_temp = None
    last_pivot_rally_low_temp = None
    
    # pivos de reação secundária dentro do rally natural
    last_pivot_rally_sec_low = None
    last_pivot_rally_sec_low_temp = None
    last_pivot_rally_sec_high = None
    last_pivot_rally_sec_high_temp = None



    # Primeiro ponto é sempre um Rally Natural Inicial
    movements.append(
        {
            "closeTime": timestamps[0],
            "closePrice": reference_point,
            "tipo": "Rally Natural (inicial)",
            "limite": limit,
        }
    )

    for i in range(1, len(closes)):
        price = closes[i]
        tempo = timestamps[i]
        added_movement = False  # Controle para evitar duplicação
        cont += 1
        price = price
        # === ESTADO INICIAL ===
        # Detecta início de tendência
        if state == "inicio":
            if not added_movement and price > reference_point + limit:
                # Inicia tendência de alta
                state = "tendencia_alta"
                current_trend = "Alta"
                last_pivot_high = price
                top = price
                reference_point = price
                movements.append(
                    {
                        "closeTime": tempo,
                        "closePrice": price,
                        "tipo": "Tendência Alta (compra)",
                        "limite": limit,
                    }
                )
                added_movement = True

            elif not added_movement and price < reference_point - limit:
                # Inicia tendência de baixa
                state = "tendencia_baixa"
                current_trend = "Baixa"
                last_pivot_down = price
                bottom = price
                reference_point = price
                movements.append(
                    {
                        "closeTime": tempo,
                        "closePrice": price,
                        "tipo": "Tendência Baixa (venda)",
                        "limite": limit,
                    }
                )
                added_movement = True

        # === TENDÊNCIA DE ALTA ===
        elif not added_movement and state == "tendencia_alta":
            if price > top:
                # Continua tendência de alta
                top = price
                last_pivot_high = price
                reference_point = price
                movements.append(
                    {
                        "closeTime": tempo,
                        "closePrice": price,
                        "tipo": "Tendência Alta (topo)",
                        "limite": limit,
                    }
                )
                added_movement = True
            elif not added_movement and price < top - limit:
                # Transição para reação natural (correção)
                state = "reacao_natural"
                last_pivot_rally_high_temp = price
                bottom = price
                reference_point = price
                movements.append(
                    {
                        "closeTime": tempo,
                        "closePrice": price,
                        "tipo": "Reação Natural (Alta)",
                        "limite": limit,
                    }
                )
                added_movement = True

        # === TENDÊNCIA DE BAIXA ===
        elif not added_movement and state == "tendencia_baixa":
            if price < bottom:
                # Continua tendência de baixa
                bottom = price
                last_pivot_down = price
                reference_point = price
                movements.append(
                    {
                        "closeTime": tempo,
                        "closePrice": price,
                        "tipo": "Tendência Baixa (fundo)",
                        "limite": limit,
                    }
                )
                added_movement = True
            elif not added_movement and price > bottom + limit:
                # Transição para reação natural (correção)
                state = "reacao_natural"
                top = price
                last_pivot_rally_low_temp = price
                reference_point = price
                movements.append(
                    {
                        "closeTime": tempo,
                        "closePrice": price,
                        "tipo": "Reação Natural (Baixa)",
                        "limite": limit,
                    }
                )
                added_movement = True

        # === REAÇÃO NATURAL ===
        elif state == "reacao_natural":
            if current_trend == "Alta":
                # Vindo de tendência de alta
                if not added_movement and price < bottom:
                    # Continuação da reação
                    bottom = price
                    last_pivot_rally_high_temp = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação Natural (fundo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > bottom + limit
                    and price < last_pivot_high
                ):
                    # Rally Natural (recuperacao)
                    state = "rally_natural"
                    top = price
                    last_pivot_rally_high = last_pivot_rally_high_temp
                    last_pivot_rally_low = None
                    starting_point = None
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (Alta)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > last_pivot_high + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    last_pivot_high = price
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and starting_point is not None
                    and price < starting_point - confirmar
                ):
                    # Reversão para tendência de baixa
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    bottom = price
                    last_pivot_down = price
                    starting_point = None
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_rally_high is not None
                    and price < last_pivot_rally_high - confirmar
                ):

                    # Reversão para tendência de baixa
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_down is not None
                    and price < last_pivot_down - confirmar
                ):

                    # Reversão para tendência de baixa
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

            elif current_trend == "Baixa":
                # Vindo de tendência baixa
                if not added_movement and price > top:
                    # Continuação da reação
                    top = price
                    last_pivot_rally_low_temp = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação Natural (topo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_down is not None
                    and price < top - limit
                    and price > last_pivot_down
                ):
                    # Rally Natural (respiro de baixa)
                    state = "rally_natural"
                    bottom = price
                    last_pivot_rally_low = last_pivot_rally_low_temp
                    last_pivot_rally_high = None
                    starting_point = None
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (Baixa)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_down is not None
                    and price < last_pivot_down - confirmar
                ):
                    # Reversão para tendência de baixa
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and starting_point is not None
                    and price > starting_point + confirmar
                ):
                    # Reversão para tendência de alta
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    top = price
                    last_pivot_high = price
                    starting_point = None
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_rally_low is not None
                    and price > last_pivot_rally_low + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    top = price
                    last_pivot_high = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > last_pivot_high + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    top = price
                    last_pivot_high = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

        # === RALLY NATURAL ===
        elif state == "rally_natural":
            if current_trend == "Alta":
                # Vindo de tendência alta
                if (
                    not added_movement
                    and price > top
                    and price < last_pivot_high
                ):
                    # Continuação do rally
                    top = price
                    last_pivot_reaction_sec_high_temp = price
                    last_pivot_rally_sec_high = last_pivot_rally_sec_high_temp
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (topo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > last_pivot_high + confirmar
                ):
                    # Retomada da tendência de alta
                    state = "tendencia_alta"
                    last_pivot_high = price
                    current_trend = "Alta"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_rally_high is not None
                    and price < top - limit
                    and price > last_pivot_rally_high
                ):
                    state = "reacao_secundaria"
                    bottom = price
                    last_pivot_reaction_sec_high = last_pivot_reaction_sec_high_temp
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária (Alta)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_rally_high is not None
                    and price < last_pivot_rally_high - confirmar
                ):
                    state = "tendencia_baixa"
                    bottom = price
                    current_trend = "Baixa"
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                added_movement = True

            elif current_trend == "Baixa":
                # Vindo de tendência baixa
                if (
                    not added_movement
                    and price < bottom
                    and price > last_pivot_down
                ):
                    # Continuação do rally
                    bottom = price
                    reference_point = price
                    last_pivot_reaction_sec_low_temp = price
                    last_pivot_rally_sec_low = last_pivot_rally_sec_low_temp
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (fundo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement and price < last_pivot_down - confirmar
                ):
                    # Retomada da tendência de baixa
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_rally_low is not None
                    and price > bottom + limit
                    and price < last_pivot_rally_low
                ):
                    state = "reacao_secundaria"
                    top = price
                    last_pivot_reaction_sec_low = last_pivot_reaction_sec_low_temp
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_rally_low is not None
                    and price > last_pivot_rally_low + confirmar
                ):
                    state = "tendencia_alta"
                    top = price
                    current_trend = "Alta"
                    last_pivot_high = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                added_movement = True

        # ======== Reação secundária ===========
        elif state == "reacao_secundaria":
            if current_trend == "Alta":
                if not added_movement and price < bottom:
                    last_pivot_rally_sec_high_temp = bottom
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária (Fundo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_reaction_sec_high is not None
                    and price > bottom + limit
                    and price < last_pivot_reaction_sec_high
                ):
                    # rally secundário
                    state = "rally_secundario"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally secundário (Alta)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_reaction_sec_high is not None
                    and price > bottom + limit
                    and price > last_pivot_reaction_sec_high + confirmar
                    and price < last_pivot_high
                ):
                    #  volta ao rally
                    state = "rally_natural"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (retorno)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > last_pivot_high + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    last_pivot_high = price
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                elif (
                    not added_movement
                    and last_pivot_rally_high is not None
                    and price < last_pivot_rally_high - confirmar
                ):
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    last_pivot_down = price
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_rally_sec_high is not None
                    and price < last_pivot_rally_sec_high - confirmar
                ):
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    last_pivot_down = price
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

            elif current_trend == "Baixa":
                # vindo de tendência de baixa
                if not added_movement and price > top:
                    top = price
                    last_pivot_rally_sec_low_temp = top
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária (topo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price < top - limit
                    and price > last_pivot_reaction_sec_low
                ):
                    #  volta ao rally
                    state = "rally_secundario"
                    bottom = price
                    current_trend = "Baixa"
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally secundário (Baixa)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price < top - limit
                    and price < last_pivot_reaction_sec_low - confirmar
                    and price > last_pivot_down
                ):
                    #  volta ao rally
                    state = "rally_natural"
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (retorno)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_down is not None
                    and last_pivot_down
                    and price < last_pivot_down - confirmar
                ):
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    last_pivot_down = price
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_rally_low is not None
                    and price > last_pivot_rally_low + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    last_pivot_high = price
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_rally_sec_low is not None
                    and price > last_pivot_rally_sec_low + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    last_pivot_high = price
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                    

            # ======== Reação secundária ===========
        elif state == "rally_secundario":
            if current_trend == "Alta":
                if not added_movement and price > top:
                    top = price
                    reference_point = price
                    last_pivot_rally_sec_high = last_pivot_rally_sec_high_temp
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally secundário (Topo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price < top - limit
                    and price > last_pivot_reaction_sec_high
                ):
                    state = "reacao_secundaria"
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                    # retorno do rally secundario para reacao
                elif (
                    not added_movement
                    and last_pivot_reaction_sec_high is not None
                    and price > last_pivot_reaction_sec_high + confirmar
                    and price < last_pivot_high
                ):
                    state = "rally_natural"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (retorno)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > last_pivot_high + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    last_pivot_high = price
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_rally_high is not None
                    and price < top - limit
                    and price > last_pivot_rally_high
                ):
                    state = "reacao_secundaria"
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_rally_high is not None
                    and price < last_pivot_rally_high - confirmar
                ):
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_high is not None
                    and price > last_pivot_high + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

            elif current_trend == "Baixa":
                # vindo de tendência de baixa
                if not added_movement and price < bottom:
                    bottom = price
                    last_pivot_rally_sec_low = last_pivot_rally_sec_low_temp
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally secundário (Fundo)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price > bottom + limit
                    and price < last_pivot_reaction_sec_low
                ):
                    state = "reacao_secundaria"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária (Baixa)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                    # retorno do rally secundario para reacao
                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price < last_pivot_reaction_sec_low - confirmar
                    and price > last_pivot_down
                ):
                    state = "rally_natural"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (retorno)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price > last_pivot_down
                    and price < last_pivot_reaction_sec_low - confirmar
                ):
                    # volta Rally natural
                    state = "rally_natural"
                    bottom = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Rally Natural (Baixa)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

                elif (
                    not added_movement
                    and last_pivot_reaction_sec_low is not None
                    and price > bottom + limit
                    and price < last_pivot_rally_low
                ):
                    state = "reacao_secundaria"
                    top = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Reação secundária",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                # reverse trendUp
                elif (
                    not added_movement
                    and last_pivot_rally_low is not None
                    and price > last_pivot_rally_low + confirmar
                ):
                    state = "tendencia_alta"
                    current_trend = "Alta"
                    top = price
                    last_pivot_high = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Alta (compra)",
                            "limite": limit,
                        }
                    )
                    added_movement = True
                elif (
                    not added_movement
                    and last_pivot_down is not None
                    and price < last_pivot_down - confirmar
                ):
                    state = "tendencia_baixa"
                    current_trend = "Baixa"
                    bottom = price
                    last_pivot_down = price
                    reference_point = price
                    movements.append(
                        {
                            "closeTime": tempo,
                            "closePrice": price,
                            "tipo": "Tendência Baixa (venda)",
                            "limite": limit,
                        }
                    )
                    added_movement = True

    # Cria lista de tuplas para bulk insert
    movements_to_save = []
    operation(movements)

    for p in movements:
        date = p["closeTime"]
        price = p["closePrice"]
        type = p["tipo"]
        atr = p["limite"]

        movements_to_save.append((date, price, type, atr))

    # Salva todos os dados de uma vez
    save_trend_clarifications(movements_to_save)
    
    return(movements)