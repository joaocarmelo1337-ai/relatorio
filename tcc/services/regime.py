"""Regime normativo aplicavel a uma unidade.

Regra da aba 'Modelo de dados' da planilha do TCC:

    SE a data de protocolo do projeto for POSTERIOR a 10/06/2023
       ENTAO NBR 17170:2022
       SENAO regime anterior (Anexo D da NBR 15575)

O limite 10/06/2023 e a data de publicacao da NBR 17170 (12/12/2022) somada
aos 180 dias de vacancia.

A distincao importa: o regime anterior previa prazos de 2 anos, extintos pela
NBR 17170. Quem define o regime e a data de PROTOCOLO DO PROJETO -- nao a do
Habite-se, que e a que inicia a contagem da garantia.
"""

from datetime import date

PUBLICACAO_NBR_17170 = date(2022, 12, 12)
DIAS_DE_VACANCIA = 180
LIMITE = date(2023, 6, 10)  # PUBLICACAO + 180 dias

NBR_17170 = "NBR 17170:2022"
ANTERIOR = "Regime anterior — Anexo D da NBR 15575"
INDEFINIDO = "Indefinido — informe a data de protocolo do projeto"


def _para_data(valor):
    if valor is None or valor == "":
        return None
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor)[:10])


def regime_normativo(data_protocolo):
    """Devolve o regime aplicavel, ou INDEFINIDO se nao houver data."""
    protocolo = _para_data(data_protocolo)
    if protocolo is None:
        return INDEFINIDO
    return NBR_17170 if protocolo > LIMITE else ANTERIOR


def alerta_consistencia(data_habite_se, data_vistoria):
    """Trava de coerencia da planilha: vistoria nao pode anteceder o Habite-se."""
    habite_se, vistoria = _para_data(data_habite_se), _para_data(data_vistoria)
    if habite_se is None or vistoria is None:
        return None
    if vistoria < habite_se:
        return (
            "ATENÇÃO: a data da vistoria é anterior à data do Habite-se. "
            "Confira as duas datas antes de prosseguir."
        )
    return "OK"
