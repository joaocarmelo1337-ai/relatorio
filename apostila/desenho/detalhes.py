"""Figuras de detalhe: geometria do degrau, canto reentrante e divisão da N2.

Todas partem da geometria real do config - o zoom é recorte da mesma peca
desenhada no corte geral, não um desenho a parte que pode divergir.
"""
from __future__ import annotations

import math

from engine.api import Resultado

from .base import caminho_barra, contorno_peca, offset_intradorso, ponto_na_barra
from .prancha import (ANCORAGEM, BORDA, COTA, CONCRETO, DISTRIBUICAO, EIXO,
                      Escala, PRINCIPAL, Prancha, TINTA, num, rail_para)


def _recorte(geo, xa, xb, ya, yb, largura, altura, me, md, ms, mi):
    util_x, util_y = largura - me - md, altura - ms - mi
    k = min(util_x / (xb - xa), util_y / (yb - ya))
    return Escala(x0=xa, y0=ya, k=k,
                  origem_px=(me + (util_x - (xb - xa) * k) / 2,
                             altura - mi - (util_y - (yb - ya) * k) / 2))


def _janela(p, e, xa, xb, ya, yb):
    """Abre o recorte correspondente a janela em coordenadas de projeto."""
    p.abrir_recorte(e.px(xa), e.py(yb), (xb - xa) * e.k, (yb - ya) * e.k)


# ===========================================================================
def geometria(r: Resultado, largura: float = 1420, altura: float = 860) -> str:
    """Piso, espelho, inclinação e as três espessuras h, h1 e hm."""
    geo = r.geo
    p = Prancha(largura, altura, 190, 300, 70, 215)
    xa, xb = geo.x1 - 30, geo.x1 + 2.7 * geo.s
    ya, yb = -geo.h - 8, 2.7 * geo.e
    e = _recorte(geo, xa, xb, ya, yb, largura, altura, 190, 300, 70, 215)

    _janela(p, e, xa, xb, ya, yb)
    p.concreto(contorno_peca(geo, e))
    p.fechar_recorte()

    # degrau em destaque
    x0 = geo.x1 + geo.s
    y0 = geo.e
    p.linha(e.px(x0), e.py(y0), e.px(x0 + geo.s), e.py(y0), cor=PRINCIPAL, w=3.0)
    p.linha(e.px(x0 + geo.s), e.py(y0), e.px(x0 + geo.s), e.py(y0 + geo.e),
            cor=PRINCIPAL, w=3.0)
    p.cota_h(e.px(x0), e.px(x0 + geo.s), e.py(y0) - 40,
             f"piso s = {num(geo.s, 1)} cm", chamada_de=e.py(y0))
    p.cota_v(e.py(y0 + geo.e), e.py(y0), e.px(x0 + geo.s) + 52,
             f"espelho e = {num(geo.e, 1)} cm", chamada_de=e.px(x0 + geo.s))

    # inclinacao
    ang = geo.alpha_rad
    xa_ang = geo.x1 + 0.25 * geo.s
    pa = ponto_na_barra(geo, xa_ang, 0.0)
    rr = 62.0
    p.linha(e.px(pa[0]), e.py(pa[1]), e.px(pa[0]) + 150, e.py(pa[1]),
            cor=EIXO, w=1.0, tracejado="8 5")
    p.add(f'<path d="M {e.px(pa[0]) + rr:.1f} {e.py(pa[1]):.1f} '
          f'A {rr} {rr} 0 0 0 {e.px(pa[0]) + rr * math.cos(ang):.1f} '
          f'{e.py(pa[1]) - rr * math.sin(ang):.1f}" fill="none" '
          f'stroke="{EIXO}" stroke-width="1.4"/>')
    p.texto(e.px(pa[0]) + rr + 12, e.py(pa[1]) - 16,
            f"α = {num(geo.alpha_graus, 1)}°", 15, EIXO, negrito=True)

    # h perpendicular, h1 vertical, hm média
    x_med = geo.x1 + 0.45 * geo.s
    a = ponto_na_barra(geo, x_med, 0.0)
    b = ponto_na_barra(geo, x_med, geo.h)
    p.linha(e.px(a[0]), e.py(a[1]), e.px(b[0]), e.py(b[1]), cor=COTA, w=1.4)
    for cx, cy in ((e.px(a[0]), e.py(a[1])), (e.px(b[0]), e.py(b[1]))):
        p.linha(cx - 6, cy + 6, cx + 6, cy - 6, cor=COTA, w=1.4)
    p.texto(e.px(a[0]) - 16, e.py(a[1]) + 6,
            f"h = {num(geo.h)} cm", 14, COTA, "end")
    p.texto(e.px(a[0]) - 16, e.py(a[1]) + 24, "(perpendicular a face)", 12,
            COTA, "end")

    xv = geo.x1 + 2.35 * geo.s
    yv_b = geo.intradorso(xv)
    p.cota_v(e.py(yv_b + geo.h1), e.py(yv_b), e.px(xv) + 96,
             f"h₁ = h/cos α = {num(geo.h1, 2)} cm", chamada_de=e.px(xv))

    p.carimbo(
        "GEOMETRIA DO LANCE",
        [
            f"Blondel: s + 2e = {num(geo.s + 2 * geo.e, 1)} cm "
            f"(faixa recomendada 60 a 64 cm)"
            + ("" if geo.blondel(r.normas)["atende"] else "  ← FORA DA FAIXA"),
            f"h₁ = h / cos α = {num(geo.h1, 2)} cm  ·  "
            f"hm = h₁ + e/2 = {num(geo.hm_exato, 2)} cm"
            + (f"  (adotado {num(geo.hm)} cm, arredondado ao cm)"
               if geo.hm != geo.hm_exato else ""),
            "hm é a espessura média na vertical: é ela que entra no peso "
            "próprio, não h.",
        ],
    )
    return p.render()


# ===========================================================================
def canto(r: Resultado, largura: float = 1420, altura: float = 900) -> str:
    """Canto reentrante: a resultante que empurra o cobrimento para fora."""
    geo, det = r.geo, r.detalhamento
    n6_, n1_ = det.por_codigo("N6"), det.por_codigo("N1")
    rail = rail_para([
        (f"{n6_.codigo} · {n6_.quantidade} Ø{num(n6_.bitola_mm, 1)} · "
         f"C = {num(n6_.comprimento_cm)} cm", n6_.descricao),
        (f"{n1_.codigo} · principal dobrando no canto", n1_.descricao),
    ])
    p = Prancha(largura, altura, rail, rail, 80, 210)
    xa, xb = geo.x1 - 62, geo.x1 + 1.9 * geo.s
    ya, yb = -geo.h - 10, 2.0 * geo.e
    e = _recorte(geo, xa, xb, ya, yb, largura, altura, rail, rail, 80, 210)

    _janela(p, e, xa, xb, ya, yb)
    p.concreto(contorno_peca(geo, e))
    p.fechar_recorte()

    n1 = det.por_codigo("N1")
    p.caminho(caminho_barra(geo, e, xa + 10, geo.x1 + 1.7 * geo.s, n1.offset_cm),
              cor=PRINCIPAL, w=5.0)

    # resultante no vértice
    vx, vy = ponto_na_barra(geo, geo.xk1, n1.offset_cm)
    bis = (geo.alpha_rad) / 2 + math.pi
    dx, dy = math.cos(bis), math.sin(bis)
    p._defs.append(
        f'<marker id="setaR" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0 1 L9 5 L0 9 z" fill="{PRINCIPAL}"/></marker>')
    p.add(f'<line x1="{e.px(vx):.1f}" y1="{e.py(vy):.1f}" '
          f'x2="{e.px(vx) + dx * 130:.1f}" y2="{e.py(vy) - dy * 130:.1f}" '
          f'stroke="{PRINCIPAL}" stroke-width="3.0" marker-end="url(#setaR)"/>')
    p.texto(e.px(vx) + dx * 140, e.py(vy) - dy * 140 + 6,
            "resultante: empurra o cobrimento para fora", 14, PRINCIPAL, "end",
            negrito=True)

    # barras N6
    n6 = det.por_codigo("N6")
    for i in range(int(r.cfg["armaduras"]["ancoragem_canto"]["barras_por_canto"])):
        cx, cy = ponto_na_barra(geo, geo.xk1 + i * 15 - 6, n6.offset_cm)
        p.circulo(e.px(cx), e.py(cy), 9, preenche="#ffffff", cor=ANCORAGEM, w=3.2)
    cx, cy = ponto_na_barra(geo, geo.xk1 + 4, n6.offset_cm)
    p.chamada(e.px(cx), e.py(cy),
              f"{n6.codigo} · {n6.quantidade} Ø{num(n6.bitola_mm, 1)} · "
              f"C = {num(n6.comprimento_cm)} cm", n6.descricao, ANCORAGEM)
    px_, py_ = ponto_na_barra(geo, geo.x1 - 34, n1.offset_cm)
    p.chamada(e.px(px_), e.py(py_), f"{n1.codigo} · principal dobrando no canto",
              n1.descricao, PRINCIPAL)

    p.carimbo(
        "CANTO REENTRANTE — mecanismo e ancoragem",
        [
            "Ao dobrar no vértice, as trações das duas pernas da barra geram "
            "uma resultante dirigida para fora da peca.",
            f"Ela tende a arrancar a camada de cobrimento ({num(geo.c, 1)} cm). "
            f"As barras {n6.codigo} atravessam o vértice e seguram a principal.",
            "Existem DOIS cantos reentrantes na escada (um por patamar); "
            "os dois precisam das barras de ancoragem.",
        ],
    )
    return p.render()


# ===========================================================================
def n2_dividida(r: Resultado, largura: float = 1720, altura: float = 900) -> str:
    """Ideia construtiva: arranque (N2a) + barra do lance (N2b)."""
    geo, det = r.geo, r.detalhamento
    lb_ = r.anc_gancho.lb_nec
    n1_ = det.por_codigo("N1")
    rail = rail_para([
        (f"traspasse ≥ lb,nec = {num(lb_, 1)} cm", "a força passa de uma barra a outra"),
        ("N2a · arranque", "sai do patamar e entra no lance"),
        ("N2b · barra do lance", "montada com a forma do lance pronta"),
        ("N1 · principal do patamar", n1_.descricao),
    ])
    p = Prancha(largura, altura, rail, rail, 80, 220)
    xa, xb = geo.x0, geo.x1 + 2.6 * geo.s
    ya, yb = -geo.h - 8, 2.8 * geo.e
    e = _recorte(geo, xa, xb, ya, yb, largura, altura, rail, rail, 80, 220)

    _janela(p, e, xa, xb, ya, yb)
    p.concreto(contorno_peca(geo, e))
    p.fechar_recorte()

    n1, n2 = det.por_codigo("N1"), det.por_codigo("N2")
    lb = r.anc_gancho.lb_nec
    off = n1.offset_cm

    # N1, como referência
    p.caminho(caminho_barra(geo, e, geo.c, n1.x_fim, off, det.gancho_cm, 0),
              cor=PRINCIPAL, w=3.4, opacidade=0.35)

    # arranque (sai do patamar e sobe um trecho do lance)
    x_arr_fim = min(n2.x_ini + 2.4 * lb, geo.x2)
    p.caminho(caminho_barra(geo, e, geo.x1 * 0.42, x_arr_fim, off + 0.9,
                            det.gancho_cm, 0),
              cor=BORDA, w=4.2)
    # barra do lance, comecando com traspasse sobre o arranque
    x_b_ini = x_arr_fim - _dev_inverso(geo, x_arr_fim, lb)
    p.caminho(caminho_barra(geo, e, x_b_ini, xb - 6, off), cor=PRINCIPAL, w=4.2)
    p.caminho(caminho_barra(geo, e, x_b_ini, x_arr_fim, off + 0.45),
              cor=DISTRIBUICAO, w=16, opacidade=0.24, cap="round")

    tx, ty = ponto_na_barra(geo, (x_b_ini + x_arr_fim) / 2, off + 0.45)
    p.chamada(e.px(tx), e.py(ty), f"traspasse ≥ lb,nec = {num(lb, 1)} cm",
              "a força passa de uma barra a outra", DISTRIBUICAO)
    ax, ay = ponto_na_barra(geo, geo.x1 * 0.75, off + 0.9)
    p.chamada(e.px(ax), e.py(ay), "N2a · arranque",
              "sai do patamar e entra no lance", BORDA)
    bx, by = ponto_na_barra(geo, xb - 40, off)
    p.chamada(e.px(bx), e.py(by), "N2b · barra do lance",
              "montada com a forma do lance pronta", PRINCIPAL)
    cx, cy = ponto_na_barra(geo, geo.x1 * 0.25, off)
    p.chamada(e.px(cx), e.py(cy), "N1 · principal do patamar",
              n1.descricao, PRINCIPAL)

    p.carimbo(
        "DIVISÃO DA N2 EM ARRANQUE + BARRA DO LANCE",
        [
            "Melhoria construtiva, não correção de cálculo: as duas opções "
            "atendem ao mesmo As.",
            f"A sobreposição vale no mínimo lb,nec = {num(lb, 1)} cm e fica "
            f"fora do ponto de momento máximo.",
            "Emendas de barras vizinhas devem ser escalonadas, nunca todas na "
            "mesma seção.",
        ],
    )
    return p.render()


def _dev_inverso(geo, x_fim: float, desenvolvido: float) -> float:
    """Quanto recuar em x para percorrer `desenvolvido` cm até x_fim."""
    from engine.barras import _avancar
    return x_fim - _avancar(geo, x_fim, desenvolvido, -1)
