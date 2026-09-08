"""Relogio de garantias.

Calcula vencimento, dias restantes e situacao a partir da data-base
(normalmente o Habite-se) e do prazo da regra aplicavel.

IMPORTANTE -- ver AVISO_TECNICO: o resultado e indicativo, ferramenta de
apoio tecnico e documental. Nao afirma responsabilidade de construtora.
"""

import calendar
from datetime import date

SEM_PRAZO = "SEM PRAZO TIPIFICADO"
VENCIDA = "VENCIDA"
VENCE_6 = "VENCE EM ATE 6 MESES"
VENCE_12 = "VENCE EM ATE 12 MESES"
VIGENTE = "VIGENTE"

SITUACAO_VISUAL = {
    VIGENTE: ("🟢", "#2e7d32"),
    VENCE_12: ("🟡", "#e6a700"),
    VENCE_6: ("🟠", "#e67e22"),
    VENCIDA: ("🔴", "#c0392b"),
    SEM_PRAZO: ("⚪", "#7f8c8d"),
}

AVISO_TECNICO = (
    "A situacao apresentada constitui ferramenta de apoio tecnico e "
    "documental, devendo ser conferida com o Manual da Edificacao, Termo de "
    "Garantia, documentacao contratual e demais condicoes aplicaveis."
)


def _para_data(valor):
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor)[:10])


def somar_meses(data_base, meses):
    """Soma meses a uma data, ajustando o dia para o fim do mes quando preciso.

    Ex.: 31/01 + 1 mes -> 28/02 (ou 29/02 em ano bissexto).
    """
    data_base = _para_data(data_base)
    total = data_base.month - 1 + meses
    ano = data_base.year + total // 12
    mes = total % 12 + 1
    dia = min(data_base.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def data_vencimento(data_base, prazo_anos):
    """Vencimento da garantia. None quando nao ha prazo tipificado."""
    if prazo_anos is None or data_base is None:
        return None
    return somar_meses(data_base, int(round(float(prazo_anos) * 12)))


def dias_restantes(vencimento, referencia=None):
    """Negativo quando ja venceu. None quando nao ha prazo."""
    vencimento = _para_data(vencimento)
    if vencimento is None:
        return None
    referencia = _para_data(referencia) or date.today()
    return (vencimento - referencia).days


def situacao(vencimento, referencia=None):
    """Um dos cinco status do relogio de garantias."""
    vencimento = _para_data(vencimento)
    if vencimento is None:
        return SEM_PRAZO
    referencia = _para_data(referencia) or date.today()
    if vencimento < referencia:
        return VENCIDA
    if vencimento <= somar_meses(referencia, 6):
        return VENCE_6
    if vencimento <= somar_meses(referencia, 12):
        return VENCE_12
    return VIGENTE


def avaliar(data_base, prazo_anos, referencia=None):
    """Devolve o quadro completo de uma garantia, pronto para a tela."""
    venc = data_vencimento(data_base, prazo_anos)
    sit = situacao(venc, referencia)
    emoji, cor = SITUACAO_VISUAL[sit]
    return {
        "data_inicial": _para_data(data_base),
        "prazo_anos": prazo_anos,
        "data_vencimento": venc,
        "dias_restantes": dias_restantes(venc, referencia),
        "situacao": sit,
        "emoji": emoji,
        "cor": cor,
        "aviso": AVISO_TECNICO,
    }


def em_alerta(quadro):
    """Alerta preventivo: manifestacao em sistema com garantia perto do fim.

    Vale tanto para o que esta prestes a vencer quanto para o que acabou de
    vencer -- nos dois casos o engenheiro precisa ser avisado.
    """
    return quadro["situacao"] in (VENCE_6, VENCE_12, VENCIDA)
