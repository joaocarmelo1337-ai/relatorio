"""Ponto de entrada do motor: config -> resultados.

`calcular(cfg)` devolve um objeto com TODOS os números que a apostila cita.
Texto e desenho leem daqui; nenhum número é redigitado em lugar nenhum.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import ancoragem as mod_anc
from . import barras as mod_barras
from . import cargas as mod_cargas
from . import esforcos as mod_esf
from . import flexao as mod_flex
from . import geometria as mod_geo
from .normas import ConfiguracaoInvalida, Normas


@dataclass
class Resultado:
    cfg: dict
    normas: Normas
    geo: mod_geo.Geometria
    cargas: mod_cargas.Cargas
    esforcos: mod_esf.Esforcos
    flexao: mod_flex.Flexao
    anc_reta: mod_anc.Ancoragem
    anc_gancho: mod_anc.Ancoragem
    detalhamento: mod_barras.Detalhamento
    armadura: dict
    avisos: list[str]


def _as_ef(normas: Normas, bitola_mm: float, espacamento_cm: float) -> float:
    """Área efetiva por metro, em cm2/m."""
    return 100.0 / espacamento_cm * normas.area_nominal(bitola_mm)


def _espacamento(
    normas: Normas,
    bloco: dict,
    As_necessaria: float,
    rotulo: str,
    passo: float = 0.5,
    maximo: float = 33.0,
) -> float:
    """Espaçamento adotado. Se o config disser "auto", escolhe o maior
    espaçamento multiplo de `passo` que ainda cobre As_necessaria."""
    valor = bloco["espacamento_cm"]
    if valor != "auto":
        return float(valor)
    area = normas.area_nominal(bloco["bitola_mm"])
    bruto = 100.0 * area / As_necessaria
    esc = math.floor(bruto / passo) * passo
    if esc < passo:
        raise ConfiguracaoInvalida(
            f"Nem a bitola Ø{bloco['bitola_mm']:g} no menor espaçamento cobre "
            f"a armadura {rotulo} ({As_necessaria:.2f} cm2/m). Aumente a bitola."
        )
    return min(esc, maximo)


def calcular(cfg: dict | str | Path, normas: Normas | None = None) -> Resultado:
    if isinstance(cfg, (str, Path)):
        with open(cfg, encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
    # Copia profunda: o motor resolve "auto" gravando o valor escolhido, e isso
    # não pode vazar para o dicionario de quem chamou.
    cfg = copy.deepcopy(cfg)
    normas = normas or Normas.carregar()
    avisos: list[str] = []

    geo = mod_geo.construir(cfg)
    cargas = mod_cargas.calcular(cfg, geo, normas)
    esf = mod_esf.calcular(cfg, geo, cargas)
    flex = mod_flex.calcular(esf.Md, geo, cfg, normas)

    arm = cfg["armaduras"]
    fck = float(cfg["materiais"]["fck"])

    # -- armadura principal adotada ---------------------------------------
    As_calc = flex.As_por_metro
    esp_princ = _espacamento(normas, arm["principal"], As_calc, "principal")
    arm["principal"]["espacamento_cm"] = esp_princ
    As_ef = _as_ef(normas, arm["principal"]["bitola_mm"], esp_princ)
    if As_ef < As_calc:
        raise ConfiguracaoInvalida(
            f"A armadura principal adotada (Ø{arm['principal']['bitola_mm']:g} c/ "
            f"{esp_princ:g} cm -> {As_ef:.2f} cm2/m) não cobre "
            f"o calculado ({As_calc:.2f} cm2/m). Reduza o espaçamento ou aumente a bitola."
        )

    # -- mínima, distribuição e borda -------------------------------------
    rho_min = normas.rho_min(fck)
    As_min = rho_min * geo.h * 100.0
    d_dist = normas["armadura_distribuicao"]
    criterios = {
        f"{d_dist['fracao_da_principal']:.0%} da armadura principal": d_dist["fracao_da_principal"] * As_calc,
        f"{d_dist['fracao_da_minima']:.0%} da armadura mínima": d_dist["fracao_da_minima"] * As_min,
        "valor absoluto mínimo": float(d_dist["absoluto_min_cm2_m"]),
    }
    As_dist = max(criterios.values())
    governa = max(criterios, key=criterios.get)
    esp_dist = _espacamento(
        normas, arm["distribuicao"], As_dist, "de distribuição",
        maximo=float(d_dist["espacamento_max_cm"]),
    )
    arm["distribuicao"]["espacamento_cm"] = esp_dist
    As_dist_ef = _as_ef(normas, arm["distribuicao"]["bitola_mm"], esp_dist)
    if As_dist_ef < As_dist:
        raise ConfiguracaoInvalida(
            f"A distribuição adotada ({As_dist_ef:.2f} cm2/m) não cobre a exigida "
            f"({As_dist:.2f} cm2/m, governada por: {governa})."
        )
    if esp_dist > d_dist["espacamento_max_cm"]:
        avisos.append(
            f"Espaçamento da distribuição ({esp_dist:g} cm) acima do "
            f"máximo de {d_dist['espacamento_max_cm']:g} cm para armadura secundária."
        )

    As_borda = normas["armadura_borda"]["fracao_da_minima"] * As_min
    esp_borda = _espacamento(
        normas, arm["borda"], As_borda, "de borda",
        maximo=float(d_dist["espacamento_max_cm"]),
    )
    arm["borda"]["espacamento_cm"] = esp_borda
    As_borda_ef = _as_ef(normas, arm["borda"]["bitola_mm"], esp_borda)

    # -- ancoragem ---------------------------------------------------------
    anc_reta = mod_anc.calcular(
        arm["principal"]["bitola_mm"], "reta", As_calc, As_ef, cfg, normas
    )
    anc_gancho = mod_anc.calcular(
        arm["principal"]["bitola_mm"], "com_gancho", As_calc, As_ef, cfg, normas
    )

    # -- detalhamento ------------------------------------------------------
    det = mod_barras.montar(
        cfg, geo, normas, anc_reta, anc_gancho, esf.x_Mk_max * 100.0
    )
    avisos.extend(det.avisos)

    # -- verificações de geometria ----------------------------------------
    bl = geo.blondel(normas)
    if not bl["atende"]:
        avisos.append(
            f"Blondel: s + 2e = {bl['soma']:.1f} cm, fora da faixa "
            f"{bl['min']:.0f}-{bl['max']:.0f} cm. O passo fica desconfortável."
        )
    if not bl["piso_atende"]:
        avisos.append(f"Piso {geo.s:.1f} cm abaixo do mínimo de {bl['piso_min']:.0f} cm.")
    if not bl["espelho_atende"]:
        avisos.append(f"Espelho {geo.e:.1f} cm acima do máximo de {bl['espelho_max']:.0f} cm.")
    esp = geo.espessura_minima(normas)
    if not esp["atende"]:
        avisos.append(f"Espessura {geo.h:.1f} cm abaixo do mínimo de {esp['minimo']:.0f} cm.")
    if not flex.ductil:
        avisos.append(
            f"Kx = {flex.kx:.3f} acima do limite {flex.kx_lim:.2f}: domínio "
            f"{flex.dominio}, ruptura frágil. Aumente h ou o fck."
        )
    if esf.foi_pinado:
        avisos.append(
            f"Mk foi PINADO no config em {esf.Mk_pinado:.2f} kN.m; o valor calculado "
            f"a partir das ações seria {esf.Mk_max:.2f} kN.m."
        )

    # -- comparacao de bitolas (seção 5.3) --------------------------------
    comparacao = []
    for b in arm["bitolas_comparadas_mm"]:
        area = normas.area_nominal(b)
        n_por_m = As_calc / area
        comparacao.append(
            {
                "bitola": b,
                "area": area,
                "n_por_metro": n_por_m,
                "espacamento": 100.0 / n_por_m,
            }
        )

    armadura = {
        "As_calc": As_calc,
        "As_ef": As_ef,
        "As_min": As_min,
        "rho_min": rho_min,
        "As_dist": As_dist,
        "As_dist_ef": As_dist_ef,
        "criterios_dist": criterios,
        "governa_dist": governa,
        "As_borda": As_borda,
        "As_borda_ef": As_borda_ef,
        "comparacao_bitolas": comparacao,
    }

    return Resultado(
        cfg=cfg,
        normas=normas,
        geo=geo,
        cargas=cargas,
        esforcos=esf,
        flexao=flex,
        anc_reta=anc_reta,
        anc_gancho=anc_gancho,
        detalhamento=det,
        armadura=armadura,
        avisos=avisos,
    )
