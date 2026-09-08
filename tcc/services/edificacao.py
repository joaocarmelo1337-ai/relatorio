"""Idade da edificacao e faixas etarias usadas nos graficos do TCC."""

from datetime import date


def _para_data(valor):
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor)[:10])


def meses_entre(inicio, fim):
    """Meses completos entre duas datas (o mes so conta quando o dia chega)."""
    inicio, fim = _para_data(inicio), _para_data(fim)
    if inicio is None or fim is None:
        return None
    meses = (fim.year - inicio.year) * 12 + (fim.month - inicio.month)
    if fim.day < inicio.day:
        meses -= 1
    return meses


def idade(data_habite_se, referencia=None):
    """Idade da edificacao em (anos, meses). Referencia = data da vistoria."""
    referencia = _para_data(referencia) or date.today()
    total = meses_entre(data_habite_se, referencia)
    if total is None:
        return None
    if total < 0:
        return (0, 0)
    return (total // 12, total % 12)


def idade_extenso(data_habite_se, referencia=None):
    """Ex.: '2 anos e 5 meses'."""
    resultado = idade(data_habite_se, referencia)
    if resultado is None:
        return "Habite-se nao informado"
    anos, meses = resultado
    partes = []
    if anos:
        partes.append(f"{anos} ano" + ("s" if anos > 1 else ""))
    if meses:
        partes.append(f"{meses} " + ("meses" if meses > 1 else "mes"))
    return " e ".join(partes) if partes else "menos de 1 mes"


FAIXAS = ("0-1 ano", "1-2 anos", "2-3 anos", "mais de 3 anos")


def faixa_etaria(data_habite_se, referencia=None):
    """Faixa usada no grafico 'patologias por idade do imovel'."""
    resultado = idade(data_habite_se, referencia)
    if resultado is None:
        return None
    anos = resultado[0]
    if anos < 1:
        return FAIXAS[0]
    if anos < 2:
        return FAIXAS[1]
    if anos < 3:
        return FAIXAS[2]
    return FAIXAS[3]


def dentro_do_recorte(data_habite_se, referencia=None):
    """O recorte do TCC e ate 3 anos contados do Habite-se."""
    resultado = idade(data_habite_se, referencia)
    return resultado is not None and resultado[0] < 3
