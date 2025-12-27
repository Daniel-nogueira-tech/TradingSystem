def operation(movimentos):
    natural_reaction = None
    last_high_top = None
    encontrou_reacao = False

    # loop de trás pra frente (como for i = len-1; i >= 0; i--)
    for i in range(len(movimentos) - 1, -1, -1):
        m = movimentos[i]
        tipo = m.get("tipo", "")

        # captura a primeira Reação Natural encontrada (mais recente)
        if ("Reação Natural" in tipo) and (not encontrou_reacao):
            natural_reaction = {
                "closePrice": m.get("closePrice"),
                "closeTime": m.get("closeTime"),
                "tipo": m.get("tipo"),
                "index": i,
            }
            encontrou_reacao = True
            continue  # continua voltando para achar o topo de alta que a precedeu

        # quando já encontrou a Reação Natural, pega o primeiro Tendência Alta anterior
        if encontrou_reacao and ("Tendência Alta" in tipo):
            last_high_top = {
                "closePrice": m.get("closePrice"),
                "closeTime": m.get("closeTime"),
                "tipo": m.get("tipo"),
                "index": i,
            }
            # equivale ao 'break' do seu JS (achou o último topo que originou a RN)
            break

    return {"natural_reaction": natural_reaction, "last_high_top": last_high_top}
