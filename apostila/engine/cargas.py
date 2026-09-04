"""Ações permanentes e variáveis sobre o lance e sobre o patamar."""
from __future__ import annotations

from dataclasses import dataclass

from .geometria import Geometria
from .normas import Normas


@dataclass(frozen=True)
class Cargas:
    """Cargas de servico em kN/m2, por trecho."""

    pp_lance: float
    pp_patamar: float
    revestimento: float
    guarda_corpo: float
    acidental: float
    acidental_da_tabela: bool
    uso: str

    @property
    def g_lance(self) -> float:
        """Permanente total no lance."""
        return self.pp_lance + self.revestimento + self.guarda_corpo

    @property
    def g_patamar(self) -> float:
        return self.pp_patamar + self.revestimento + self.guarda_corpo

    @property
    def q_lance(self) -> float:
        """Total de servico no lance (g + q)."""
        return self.g_lance + self.acidental

    @property
    def q_patamar(self) -> float:
        return self.g_patamar + self.acidental


def calcular(cfg: dict, geo: Geometria, normas: Normas) -> Cargas:
    a = cfg["acoes"]
    gamma_conc = normas.peso_especifico_concreto()

    imposta = a.get("acidental_kN_m2")
    if imposta is None:
        acidental = normas.carga_acidental(a["uso"])
        da_tabela = True
    else:
        acidental = float(imposta)
        da_tabela = False

    return Cargas(
        # hm e h estão em cm; /100 para metro.
        pp_lance=gamma_conc * geo.hm / 100.0,
        pp_patamar=gamma_conc * geo.h / 100.0,
        revestimento=float(a.get("revestimento_kN_m2", 0.0)),
        guarda_corpo=float(a.get("guarda_corpo_kN_m2", 0.0)),
        acidental=acidental,
        acidental_da_tabela=da_tabela,
        uso=a["uso"],
    )
