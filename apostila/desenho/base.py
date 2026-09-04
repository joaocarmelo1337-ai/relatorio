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


def _paralela(p, q, t):
    """Reta paralela ao segmento p->q, deslocada t para o lado de cima."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    c = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / c, dx / c        # normal apontando para cima (y cresce)
    if ny < 0:
        nx, ny = -nx, -ny
    return (p[0] + nx * t, p[1] + ny * t), (q[0] + nx * t, q[1] + ny * t)


def _intersecao(a1, a2, b1, b2):
    x1, y1 = a1; x2, y2 = a2; x3, y3 = b1; x4, y4 = b2
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-12:
        return a2
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def offset_intradorso(geo: Geometria, x_ini: float, x_fim: float, t: float):
    """Poligonal paralela ao intradorso, a distancia perpendicular t."""
    xs = [x_ini] + [k for k in (geo.xk1, geo.xk2) if x_ini < k < x_fim] + [x_fim]
    brutos = [(x, geo.intradorso(x)) for x in xs]
    segs = [_paralela(a, b, t) for a, b in zip(brutos, brutos[1:])]
    pts = [segs[0][0]]
    for s1, s2 in zip(segs, segs[1:]):
        pts.append(_intersecao(s1[0], s1[1], s2[0], s2[1]))
    pts.append(segs[-1][1])
    return pts


def direcao(geo: Geometria, x: float) -> tuple[float, float]:
    """Vetor unitario tangente ao intradorso em x (sentido da subida)."""
    if geo.xk1 < x < geo.xk2:
        return math.cos(geo.alpha_rad), math.sin(geo.alpha_rad)
    return 1.0, 0.0


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
