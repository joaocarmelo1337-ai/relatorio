"""Esforços solicitantes do conjunto patamar + lance + patamar.

Modelo: viga biapoiada de 1 m de largura, com carga uniforme por trechos
(patamar inferior, lance, patamar superior). Os diagramas M(x) e V(x) saem
analiticamente, o que permite desenha-los com a mesma precisão do cálculo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .geometria import Geometria
from .cargas import Cargas


@dataclass(frozen=True)
class Trecho:
    x_ini: float   # m
    x_fim: float   # m
    q: float       # kN/m (faixa de 1 m)

    @property
    def comprimento(self) -> float:
        return self.x_fim - self.x_ini

    @property
    def resultante(self) -> float:
        return self.q * self.comprimento

    @property
    def centroide(self) -> float:
        return (self.x_ini + self.x_fim) / 2.0


@dataclass(frozen=True)
class Esforcos:
    trechos: tuple[Trecho, ...]
    vao: float                 # m
    gamma_f: float
    R_a: float = field(init=False)
    R_b: float = field(init=False)
    carga_total: float = field(init=False)
    Mk_max: float = field(init=False)
    x_Mk_max: float = field(init=False)
    Vk_max: float = field(init=False)
    Mk_pinado: float | None = None

    def __post_init__(self) -> None:
        obj = object.__setattr__
        total = sum(t.resultante for t in self.trechos)
        momento_b = sum(t.resultante * (self.vao - t.centroide) for t in self.trechos)
        r_a = momento_b / self.vao
        obj(self, "carga_total", total)
        obj(self, "R_a", r_a)
        obj(self, "R_b", total - r_a)
        x_max = self._abscissa_cortante_nula()
        obj(self, "x_Mk_max", x_max)
        obj(self, "Mk_max", self.M(x_max))
        obj(self, "Vk_max", max(abs(r_a), abs(total - r_a)))

    # -- diagramas --------------------------------------------------------
    def V(self, x: float) -> float:
        """Cortante caracteristico em x (m), em kN."""
        v = self.R_a
        for t in self.trechos:
            if x <= t.x_ini:
                break
            v -= t.q * (min(x, t.x_fim) - t.x_ini)
        return v

    def M(self, x: float) -> float:
        """Momento caracteristico em x (m), em kN.m."""
        m = self.R_a * x
        for t in self.trechos:
            if x <= t.x_ini:
                break
            a = min(x, t.x_fim) - t.x_ini
            m -= t.q * a * (x - t.x_ini - a / 2.0)
        return m

    def _abscissa_cortante_nula(self) -> float:
        """Ponto de momento máximo: onde o cortante troca de sinal."""
        v = self.R_a
        for t in self.trechos:
            if t.q > 0 and v - t.q * t.comprimento <= 0:
                return t.x_ini + v / t.q
            v -= t.q * t.comprimento
        return self.vao / 2.0

    def amostrar(self, n: int = 200) -> list[tuple[float, float, float]]:
        """[(x, M, V)] para desenho. Inclui os pontos de quebra dos trechos."""
        xs = {i * self.vao / n for i in range(n + 1)}
        for t in self.trechos:
            xs.add(t.x_ini)
            xs.add(t.x_fim)
        xs.add(self.x_Mk_max)
        return [(x, self.M(x), self.V(x)) for x in sorted(xs)]

    # -- valores de cálculo ----------------------------------------------
    @property
    def Mk(self) -> float:
        """Momento caracteristico adotado (pinado no config, ou o calculado)."""
        return self.Mk_max if self.Mk_pinado is None else self.Mk_pinado

    @property
    def Md(self) -> float:
        return self.gamma_f * self.Mk

    @property
    def Vd(self) -> float:
        return self.gamma_f * self.Vk_max

    @property
    def foi_pinado(self) -> bool:
        return self.Mk_pinado is not None


def calcular(cfg: dict, geo: Geometria, cargas: Cargas) -> Esforcos:
    m = 1 / 100.0  # cm -> m
    trechos = (
        Trecho(0.0, geo.x1 * m, cargas.q_patamar),
        Trecho(geo.x1 * m, geo.x2 * m, cargas.q_lance),
        Trecho(geo.x2 * m, geo.x3 * m, cargas.q_patamar),
    )
    pinado = cfg.get("esforcos", {}).get("momento_caracteristico_kNm")
    return Esforcos(
        trechos=trechos,
        vao=geo.x3 * m,
        gamma_f=float(cfg["materiais"]["gamma_f"]),
        Mk_pinado=None if pinado is None else float(pinado),
    )
