"""Matriz GUT: Gravidade x Urgencia x Tendencia.

A classificacao e sempre uma proposta do sistema. Quem decide e o
engenheiro -- ver `confirmada_por` na tabela classificacoes_gut.
"""

GRAVIDADE = {
    10: "Extremamente grave",
    8: "Muito grave",
    6: "Grave",
    3: "Pouco grave",
    1: "Sem gravidade significativa",
}

URGENCIA = {
    10: "Intervencao imediata",
    8: "Alta urgencia",
    6: "Medio prazo",
    3: "Pode aguardar planejamento",
    1: "Sem urgencia",
}

TENDENCIA = {
    10: "Agravamento imediato",
    8: "Agravamento rapido",
    6: "Agravamento gradual",
    3: "Agravamento lento",
    1: "Sem tendencia significativa",
}

VALORES_VALIDOS = (1, 3, 6, 8, 10)

PRIORIDADE_ROTULO = {
    1: ("Prioridade 1", "🔴", "#c0392b"),
    2: ("Prioridade 2", "🟡", "#e6a700"),
    3: ("Prioridade 3", "🟢", "#2e7d32"),
}


def validar(valor, nome):
    if valor not in VALORES_VALIDOS:
        raise ValueError(
            f"{nome} deve ser um de {VALORES_VALIDOS}; recebido {valor!r}"
        )
    return valor


def calcular_gut(gravidade, urgencia, tendencia):
    """Devolve o produto G x U x T."""
    validar(gravidade, "gravidade")
    validar(urgencia, "urgencia")
    validar(tendencia, "tendencia")
    return gravidade * urgencia * tendencia


def prioridade(gut):
    """Faixas definidas no TCC: >=512 -> P1; 108..511 -> P2; 1..107 -> P3."""
    if gut >= 512:
        return 1
    if gut >= 108:
        return 2
    return 3


def classificar(gravidade, urgencia, tendencia):
    """Atalho: devolve (gut, prioridade, rotulo, emoji, cor)."""
    gut = calcular_gut(gravidade, urgencia, tendencia)
    p = prioridade(gut)
    rotulo, emoji, cor = PRIORIDADE_ROTULO[p]
    return {
        "gut": gut,
        "prioridade": p,
        "rotulo": rotulo,
        "emoji": emoji,
        "cor": cor,
    }
