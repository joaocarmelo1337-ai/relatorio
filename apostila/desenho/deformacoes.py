"""Diagrama de deformações da seção, com os domínios e a linha neutra.

Mostra a seção real (h, d, cobrimento), a posição calculada de x, o diagrama
de deformações que dela decorre e a faixa de domínios em que o Kx caiu. Tudo
sai do `Flexão` do motor - se o fck ou a espessura mudarem, a linha neutra
anda sozinha.
"""
from __future__ import annotations

from engine.api import Resultado

from .prancha import (COTA, CONCRETO, DISTRIBUICAO, EIXO, PRINCIPAL, Prancha,
                      TINTA, num)

VERDE = "#0f6e56"
OLIVA = "#3b6d11"
VERMELHO = "#a32d2d"


def desenhar(r: Resultado, largura: float = 1680, altura: float = 950) -> str:
    geo, f = r.geo, r.flexao
    p = Prancha(largura, altura, 210, 120, 60, 205)

    # ---------------- 1. seção transversal -------------------------------
    x0, y0 = 240.0, 150.0
    bw_px, h_px = 300.0, 330.0
    k = h_px / geo.h
    p.texto(x0, y0 - 42, "SEÇÃO (1 m de largura)", 15, TINTA, negrito=True)
    p.add(f'<rect x="{x0}" y="{y0}" width="{bw_px}" height="{h_px}" '
          f'fill="{CONCRETO}" stroke="{TINTA}" stroke-width="1.9"/>')
    p.add(f'<rect x="{x0}" y="{y0}" width="{bw_px}" height="{h_px}" '
          f'fill="url(#hachura)" stroke="none"/>')

    y_ln = y0 + f.x * k
    y_as = y0 + geo.d * k

    # zona comprimida
    p.add(f'<rect x="{x0}" y="{y0}" width="{bw_px}" height="{f.x * k:.1f}" '
          f'fill="{PRINCIPAL}" opacity="0.10"/>')
    p.linha(x0 - 26, y_ln, x0 + bw_px + 26, y_ln, cor=PRINCIPAL, w=2.0,
            tracejado="12 5")
    p.texto(x0 - 32, y_ln - 8, "LN", 15, PRINCIPAL, "end", negrito=True)
    p.texto(x0 + bw_px / 2, y0 + f.x * k / 2 + 5, "concreto comprimido",
            13, PRINCIPAL, "middle")

    # barras da armadura
    for i in range(6):
        p.circulo(x0 + 34 + i * (bw_px - 68) / 5, y_as, 7.5, preenche=PRINCIPAL)
    p.texto(x0 + bw_px / 2, y_as + 30, f"As = {num(f.As_por_metro, 2)} cm²/m",
            14, PRINCIPAL, "middle", negrito=True)

    p.cota_v(y0, y0 + h_px, x0 - 66, f"h = {num(geo.h)}", chamada_de=x0)
    p.cota_v(y0, y_as, x0 - 118, f"d = {num(geo.d, 1)}", chamada_de=x0)
    p.cota_v(y0, y_ln, x0 + bw_px + 70, f"x = {num(f.x, 2)}",
             chamada_de=x0 + bw_px)

    # ---------------- 2. diagrama de deformações -------------------------
    xd = x0 + bw_px + 250
    larg_d = 330.0
    p.texto(xd, y0 - 42, "DEFORMAÇÕES (‰)", 15, TINTA, negrito=True)
    p.linha(xd, y0 - 14, xd, y0 + h_px + 14, cor=TINTA, w=1.4)
    p.linha(xd - 30, y_ln, xd + larg_d + 40, y_ln, cor=PRINCIPAL, w=1.6,
            tracejado="12 5")

    esc = larg_d / max(f.eps_cu, f.eps_s)
    xc = xd - f.eps_cu * esc          # encurtamento, para a esquerda
    xs = xd + f.eps_s * esc           # alongamento, para a direita
    p.poligonal([(xc, y0), (xs, y_as)], cor=EIXO, w=2.6)
    p.linha(xc, y0, xd, y0, cor=EIXO, w=1.0, tracejado="4 3")
    p.linha(xd, y_as, xs, y_as, cor=EIXO, w=1.0, tracejado="4 3")
    p.circulo(xc, y0, 5, preenche=EIXO)
    p.circulo(xs, y_as, 5, preenche=PRINCIPAL)
    p.texto(xc - 10, y0 - 12, f"εcu = {num(f.eps_cu, 1)}‰", 14, EIXO, "end",
            negrito=True)
    p.texto(xs + 12, y_as + 6, f"εs = {num(f.eps_s, 2)}‰", 14, PRINCIPAL,
            negrito=True)
    p.texto(xd + 6, y0 + h_px + 34, "alongamento →", 13, COTA)
    p.texto(xd - 6, y0 + h_px + 34, "← encurtamento", 13, COTA, "end")

    if r.normas.tem_Es():
        eps_yd = f.fyd * 10.0 / r.normas.Es_MPa() * 1000.0
        xy = xd + eps_yd * esc
        p.linha(xy, y0 - 6, xy, y0 + h_px + 6, cor=OLIVA, w=1.3, tracejado="6 4")
        p.texto(xy, y0 - 16, f"εyd = {num(eps_yd, 2)}‰", 13, OLIVA, "middle")
    else:
        p.texto(xd, y0 + h_px + 58,
                "εyd não marcado: falta Es em config/normas.yaml.", 12, COTA)

    # ---------------- 3. faixa de domínios -------------------------------
    yb = y0 + h_px + 138
    xb0, xb1 = 150.0, largura - 150.0
    lim23 = f.lim_dom_23
    lim34 = f.kx_lim

    def bx(kx: float) -> float:
        return xb0 + kx * (xb1 - xb0)

    p.texto(xb0, yb - 30, "DOMÍNIOS DE DEFORMAÇÃO  (Kx = x / d)", 15, TINTA,
            negrito=True)
    faixas = [
        (0.0, lim23, "#e1f5ee", VERDE, "Domínio 2", "muito dúctil, pouco econômico"),
        (lim23, lim34, "#eaf3de", OLIVA, "Domínio 3", "faixa ideal"),
        (lim34, 1.0, "#fcebeb", VERMELHO, "Domínio 4", "ruptura frágil - proibido"),
    ]
    for a, b, fundo, cor, nome, leg in faixas:
        p.add(f'<rect x="{bx(a):.1f}" y="{yb}" width="{bx(b) - bx(a):.1f}" '
              f'height="54" rx="5" fill="{fundo}" stroke="{cor}" stroke-width="1.1"/>')
        p.texto((bx(a) + bx(b)) / 2, yb + 23, nome, 14, cor, "middle", negrito=True)
        p.texto((bx(a) + bx(b)) / 2, yb + 42, leg, 12, cor, "middle")

    p.linha(xb0, yb + 88, xb1, yb + 88, cor=COTA, w=1.0)
    for kx in (0.0, lim23, lim34, 1.0):
        p.linha(bx(kx), yb + 83, bx(kx), yb + 93, cor=COTA, w=1.1)
        p.texto(bx(kx), yb + 110, num(kx, 3), 13, COTA, "middle")

    # onde caiu o exemplo
    p.add(f'<path d="M {bx(f.kx):.1f} {yb - 6:.1f} l -9 -14 l 18 0 z" '
          f'fill="{PRINCIPAL}"/>')
    p.texto(bx(f.kx), yb - 28,
            f"este exemplo: Kx = {num(f.kx, 3)}  →  domínio {f.dominio}",
            14, PRINCIPAL, "middle", negrito=True)

    limite = ("fck ≤ 50 MPa" if float(r.cfg["materiais"]["fck"]) <= 50
              else "fck > 50 MPa")
    p.texto(bx(lim34), yb + 72,
            f"limite dúctil para {limite}: Kx ≤ {num(lim34, 2)}", 13, VERMELHO,
            "middle")

    p.carimbo(
        "DIAGRAMA DE DEFORMAÇÕES E DOMÍNIOS",
        [
            f"C{num(float(r.cfg['materiais']['fck']))} · "
            f"{r.cfg['materiais']['aco_principal']} · h = {num(geo.h)} cm · "
            f"d = {num(geo.d, 1)} cm · λ = {num(f.lam, 3)} · αc = {num(f.alpha_c, 3)}",
            f"x = {num(f.x, 2)} cm · Kx = {num(f.kx, 3)} · "
            f"εs = {num(f.eps_s, 2)}‰ (limite {num(f.eps_su, 0)}‰) · "
            f"domínio {f.dominio}",
            "O limite do domínio 2/3 é εcu/(εcu+εsu); ambos vem de "
            "config/normas.yaml e mudam com o fck.",
        ],
    )
    return p.render()
