"""Aderência, comprimento de ancoragem e ganchos."""
from __future__ import annotations

from dataclasses import dataclass, field

from .normas import Normas


@dataclass(frozen=True)
class Ancoragem:
    bitola_mm: float
    fck: float
    gamma_c: float
    fyd: float          # kN/cm2
    eta1: float
    eta2: float
    eta3: float
    alpha: float
    modo: str           # "reta" | "com_gancho"
    As_calc: float
    As_ef: float
    frac_lb_min: float
    n_phi_min: int
    abs_min_cm: float

    fctd: float = field(init=False)     # kN/cm2
    fbd: float = field(init=False)      # kN/cm2
    lb: float = field(init=False)       # cm
    lb_min: float = field(init=False)
    lb_nec_bruto: float = field(init=False)
    lb_nec: float = field(init=False)
    governa_minimo: bool = field(init=False)

    def __post_init__(self) -> None:
        obj = object.__setattr__
        phi = self.bitola_mm / 10.0                       # mm -> cm
        fctd = 0.21 * self.fck ** (2.0 / 3.0) / self.gamma_c / 10.0   # kN/cm2
        fbd = self.eta1 * self.eta2 * self.eta3 * fctd
        lb = (phi / 4.0) * (self.fyd / fbd)
        obj(self, "fctd", fctd)
        obj(self, "fbd", fbd)
        obj(self, "lb", lb)
        lb_min = max(self.frac_lb_min * lb, self.n_phi_min * phi, self.abs_min_cm)
        obj(self, "lb_min", lb_min)
        bruto = self.alpha * lb * self.As_calc / self.As_ef
        obj(self, "lb_nec_bruto", bruto)
        obj(self, "lb_nec", max(bruto, lb_min))
        obj(self, "governa_minimo", lb_min > bruto)

    @property
    def lb_em_phi(self) -> float:
        return self.lb / (self.bitola_mm / 10.0)


def calcular(
    bitola_mm: float,
    modo: str,
    As_calc: float,
    As_ef: float,
    cfg: dict,
    normas: Normas,
) -> Ancoragem:
    mat = cfg["materiais"]
    aco = mat["aco_principal"]
    m = normas["aderencia"]["lb_min"]
    return Ancoragem(
        bitola_mm=bitola_mm,
        fck=float(mat["fck"]),
        gamma_c=float(mat["gamma_c"]),
        fyd=normas.fyk(aco) / float(mat["gamma_s"]) / 10.0,
        eta1=normas.eta1(aco),
        eta2=normas.eta2(mat.get("aderencia", "boa")),
        eta3=normas.eta3(bitola_mm),
        alpha=normas.alpha_ancoragem(modo),
        modo=modo,
        As_calc=As_calc,
        As_ef=As_ef,
        frac_lb_min=float(m["fracao_lb"]),
        n_phi_min=int(m["n_phi"]),
        abs_min_cm=float(m["absoluto_cm"]),
    )
