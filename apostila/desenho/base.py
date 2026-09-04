"""Helpers geometricos compartilhados pelos desenhos.

O ponto delicado aqui é o traçado das barras: o cobrimento é medido
PERPENDICULAR a face, não na vertical. Numa laje inclinada isso muda o
desenho - a barra do lance não é a linha do intradorso deslocada para cima,
é a paralela verdadeira. `offset_intradorso` faz esse deslocamento certo,
recortando as retas paralelas nos vertices.
"""
from __future__ import annotations

import math

from engine.geometria import Geometria


def offset_intradorso(geo: Geometria, x_ini: float, x_fim: float, t: float):
    """Reexporta a paralela do motor: desenho e cálculo usam a mesma."""
    return geo.paralela_ao_intradorso(x_ini, x_fim, t)


def direcao(geo: Geometria, x: float) -> tuple[float, float]:
    return geo.tangente(x)


def poli_px(pts, esc) -> str:
    """Path SVG a partir de uma poligonal em coordenadas de projeto."""
    return "M " + " L ".join(f"{esc.px(x):.2f} {esc.py(y):.2f}" for x, y in pts)


def caminho_barra(
    geo: Geometria,
    esc,
    x_ini: float,
    x_fim: float,
    offset: float,
    gancho_ini: float = 0.0,
    gancho_fim: float = 0.0,
) -> str:
    """Path SVG de uma barra: trecho paralelo ao intradorso + ganchos.

    O gancho sobe perpendicular a face, para dentro da laje - é assim que ele
    é dobrado e é por isso que ele não pode passar de h - 2c.
    """
    pts = offset_intradorso(geo, x_ini, x_fim, offset)
    saida = []
    if gancho_ini > 0:
        ux, uy = direcao(geo, x_ini)
        saida.append((pts[0][0] - uy * gancho_ini, pts[0][1] + ux * gancho_ini))
    saida.extend(pts)
    if gancho_fim > 0:
        ux, uy = direcao(geo, x_fim)
        saida.append((pts[-1][0] - uy * gancho_fim, pts[-1][1] + ux * gancho_fim))
    return "M " + " L ".join(f"{esc.px(x):.2f} {esc.py(y):.2f}" for x, y in saida)


def ponto_na_barra(geo: Geometria, x: float, offset: float) -> tuple[float, float]:
    """Ponto sobre o eixo de uma barra paralela ao intradorso, na abscissa x."""
    pts = offset_intradorso(geo, max(geo.x0, x - 1), min(geo.x3, x + 1), offset)
    return pts[len(pts) // 2]


def contorno_peca(geo: Geometria, esc) -> str:
    """Path fechado da seção de concreto: extradorso + topo + intradorso."""
    topo = geo.perfil_extradorso()
    sof = geo.perfil_intradorso()
    d = "M " + " L ".join(f"{esc.px(x):.2f} {esc.py(y):.2f}" for x, y in topo)
    d += " L " + " L ".join(
        f"{esc.px(x):.2f} {esc.py(y):.2f}" for x, y in reversed(sof)
    )
    return d + " Z"
