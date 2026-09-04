"""Dimensionamento a flexão simples: linha neutra, ductilidade e área de aço.

Nada de 0,425 e 1,25 fixos: lambda e alpha_c saem de `Normas` e variam com fck,
como manda a NBR 6118 acima de 50 MPa.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .normas import Normas


class SecaoInsuficiente(Exception):
    """Md acima do que a seção comprime: não há solução com armadura simples."""


@dataclass(frozen=True)
class Flexao:
    Md: float          # kN.cm
    bw: float          # cm
    d: float           # cm
    fck: float         # MPa
    fyk: float         # MPa
    gamma_c: float
    gamma_s: float
    lam: float
    alpha_c: float
    kx_lim: float
    eps_cu: float      # permil
    eps_su: float      # permil
    lim_dom_23: float

    fcd: float = field(init=False)      # kN/cm2
    fyd: float = field(init=False)      # kN/cm2
    Mlim: float = field(init=False)     # kN.cm - momento que esgota o bloco
    x: float = field(init=False)        # cm
    kx: float = field(init=False)
    z: float = field(init=False)        # braco de alavanca
    As: float = field(init=False)       # cm2 na largura bw
    eps_s: float = field(init=False)    # permil
    dominio: str = field(init=False)

    def __post_init__(self) -> None:
        obj = object.__setattr__
        fcd = self.fck / self.gamma_c / 10.0        # MPa -> kN/cm2
        fyd = self.fyk / self.gamma_s / 10.0
        obj(self, "fcd", fcd)
        obj(self, "fyd", fyd)

        base = (self.alpha_c / 2.0) * self.bw * self.d ** 2 * fcd
        obj(self, "Mlim", base)
        razao = self.Md / base
        if razao >= 1.0:
            raise SecaoInsuficiente(
                f"Md = {self.Md / 100:.2f} kN.m excede o limite da seção com "
                f"armadura simples ({base / 100:.2f} kN.m).\n"
                f"  Aumente a espessura, o fck, ou reveja o esquema estrutural."
            )
        x = (self.d / self.lam) * (1.0 - math.sqrt(1.0 - razao))
        obj(self, "x", x)
        obj(self, "kx", x / self.d)
        obj(self, "z", self.d - 0.5 * self.lam * x)
        obj(self, "As", self.Md / (fyd * (self.d - 0.5 * self.lam * x)))
        obj(self, "eps_s", self.eps_cu * (self.d - x) / x)
        obj(self, "dominio", self._dominio())

    def _dominio(self) -> str:
        if self.kx <= self.lim_dom_23:
            return "2"
        if self.kx <= self.kx_lim:
            return "3"
        return "4"

    @property
    def ductil(self) -> bool:
        return self.kx <= self.kx_lim

    @property
    def As_por_metro(self) -> float:
        return self.As * 100.0 / self.bw


def calcular(Md_kNm: float, geo, cfg: dict, normas: Normas, bw: float = 100.0) -> Flexao:
    fck = float(cfg["materiais"]["fck"])
    return Flexao(
        Md=Md_kNm * 100.0,
        bw=bw,
        d=geo.d,
        fck=fck,
        fyk=normas.fyk(cfg["materiais"]["aco_principal"]),
        gamma_c=float(cfg["materiais"]["gamma_c"]),
        gamma_s=float(cfg["materiais"]["gamma_s"]),
        lam=normas.lambda_(fck),
        alpha_c=normas.alpha_c(fck),
        kx_lim=normas.kx_limite(fck),
        eps_cu=normas.eps_cu_permil(fck),
        eps_su=normas.eps_su_permil(),
        lim_dom_23=normas.limite_dominio_2_3(fck),
    )
