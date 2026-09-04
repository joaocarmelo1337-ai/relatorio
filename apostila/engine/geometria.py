"""Geometria do lance: Blondel, inclinação, espessura média e o contorno real
usado pelos desenhos.

Todas as coordenadas geometricas dos cortes saem daqui, para que desenho e
cálculo nunca divirjam. Origem: pe do patamar inferior, no nível do piso
acabado (y = 0). Eixo x cresce no sentido da subida, em cm.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .normas import ConfiguracaoInvalida, Normas


@dataclass(frozen=True)
class Geometria:
    # entradas
    s: float                  # piso
    e: float                  # espelho
    n: int                    # número de espelhos
    patamar_inf: float
    patamar_sup: float
    largura: float
    h: float                  # espessura da laje
    c: float                  # cobrimento
    arredondar_hm: float | None

    # derivados (preenchidos no __post_init__)
    subida: float = field(init=False)          # desnivel total vencido
    projecao_lance: float = field(init=False)  # projeção horizontal desenhada
    projecao_pisos: float = field(init=False)  # (n-1)*s
    vao_total: float = field(init=False)
    alpha_rad: float = field(init=False)
    h1: float = field(init=False)              # h/cos(alpha)
    hm_exato: float = field(init=False)
    hm: float = field(init=False)              # o efetivamente usado nas cargas
    d: float = field(init=False)               # altura util
    x0: float = field(init=False)
    x1: float = field(init=False)
    x2: float = field(init=False)
    x3: float = field(init=False)
    xk1: float = field(init=False)             # quebra inferior do intradorso
    xk2: float = field(init=False)             # quebra superior do intradorso
    dv: float = field(init=False)              # espessura medida na vertical

    def __post_init__(self) -> None:
        obj = object.__setattr__
        obj(self, "subida", self.e * self.n)
        obj(self, "projecao_lance", self.s * self.n)
        obj(self, "projecao_pisos", self.s * (self.n - 1))
        obj(self, "vao_total", self.patamar_inf + self.s * self.n + self.patamar_sup)

        alpha = math.atan(self.subida / self.projecao_lance)
        obj(self, "alpha_rad", alpha)
        h1 = self.h / math.cos(alpha)
        obj(self, "h1", h1)
        hm_exato = h1 + self.e / 2.0
        obj(self, "hm_exato", hm_exato)
        passo = self.arredondar_hm
        obj(self, "hm", hm_exato if not passo else round(hm_exato / passo) * passo)

        # Altura util: cobrimento + meia bitola seria o rigor, mas o exemplo
        # original adota d = h - c - 0,5 = 9,0 cm. Ver `altura_util()`.
        obj(self, "d", self.h - self.c - 0.5)

        obj(self, "x0", 0.0)
        obj(self, "x1", self.patamar_inf)
        obj(self, "x2", self.patamar_inf + self.projecao_lance)
        obj(self, "x3", self.vao_total)
        dv = self.h / math.cos(alpha)
        obj(self, "dv", dv)
        ta = math.tan(alpha)
        obj(self, "xk1", self.x1 + (dv - self.h) / ta)
        obj(self, "xk2", self.x2 - (dv - self.h) / ta)

    # -- ângulos ----------------------------------------------------------
    @property
    def alpha_graus(self) -> float:
        return math.degrees(self.alpha_rad)

    @property
    def cos_alpha(self) -> float:
        return math.cos(self.alpha_rad)

    @property
    def tan_alpha(self) -> float:
        return math.tan(self.alpha_rad)

    # -- contorno ---------------------------------------------------------
    def intradorso(self, x: float) -> float:
        """Cota y da face inferior da laje na abscissa x."""
        if x <= self.xk1:
            return -self.h
        if x >= self.xk2:
            return self.subida - self.h
        return -self.dv + self.tan_alpha * (x - self.x1)

    def perfil_extradorso(self) -> list[tuple[float, float]]:
        """Poligonal da face superior, incluindo os degraus."""
        pts: list[tuple[float, float]] = [(self.x0, 0.0), (self.x1, 0.0)]
        for i in range(self.n):
            x = self.x1 + i * self.s
            y = i * self.e
            pts.append((x, y + self.e))
            pts.append((x + self.s, y + self.e))
        pts.append((self.x3, self.subida))
        return pts

    def perfil_intradorso(self) -> list[tuple[float, float]]:
        return [
            (self.x0, -self.h),
            (self.xk1, -self.h),
            (self.xk2, self.subida - self.h),
            (self.x3, self.subida - self.h),
        ]

    # -- verificações -----------------------------------------------------
    def blondel(self, normas: Normas) -> dict:
        b = normas["blondel"]
        soma = self.s + 2 * self.e
        return {
            "soma": soma,
            "min": b["soma_min_cm"],
            "max": b["soma_max_cm"],
            "atende": b["soma_min_cm"] <= soma <= b["soma_max_cm"],
            "piso_min": b["piso_min_cm"],
            "piso_atende": self.s >= b["piso_min_cm"],
            "espelho_max": b["espelho_max_cm"],
            "espelho_atende": self.e <= b["espelho_max_cm"],
        }

    def espessura_minima(self, normas: Normas) -> dict:
        m = normas["espessura_minima_cm"]
        return {
            "minimo": m["laje_piso"],
            "atende": self.h >= m["laje_piso"],
            "estimativa_vao_40": self.vao_total / 40.0,
        }


def construir(cfg: dict) -> Geometria:
    g = cfg["geometria"]
    if g.get("esquema", "biapoiado") != "biapoiado":
        raise ConfiguracaoInvalida(
            f"geometria.esquema = '{g['esquema']}' não implementado. "
            f"O motor só resolve 'biapoiado' (patamar + lance + patamar sobre "
            f"dois apoios extremos)."
        )
    if g["n_degraus"] < 2:
        raise ConfiguracaoInvalida("geometria.n_degraus deve ser >= 2.")
    if g["espessura_h"] <= 2 * g["cobrimento_c"]:
        raise ConfiguracaoInvalida(
            f"espessura_h ({g['espessura_h']} cm) precisa ser maior que "
            f"2 x cobrimento ({2 * g['cobrimento_c']} cm)."
        )
    return Geometria(
        s=float(g["piso_s"]),
        e=float(g["espelho_e"]),
        n=int(g["n_degraus"]),
        patamar_inf=float(g["patamar_inferior"]),
        patamar_sup=float(g["patamar_superior"]),
        largura=float(g["largura_lance"]),
        h=float(g["espessura_h"]),
        c=float(g["cobrimento_c"]),
        arredondar_hm=g.get("arredondar_hm_cm"),
    )
