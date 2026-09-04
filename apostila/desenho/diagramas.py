"""Diagramas de momento fletor e de força cortante do conjunto.

Era o buraco da Seção 4: só havia formula, sem desenho. Os valores saem do
mesmo `Esforços` que dimensiona a armadura, então o desenho não pode discordar
do texto. Momento positivo desenhado PARA BAIXO (convenção brasileira: o
diagrama fica do lado tracionado).
"""
from __future__ import annotations

from engine.api import Resultado

from .prancha import COTA, DISTRIBUICAO, EIXO, PRINCIPAL, Prancha, TINTA, num


def desenhar(r: Resultado, largura: float = 1720, altura: float = 1080) -> str:
    geo, esf = r.geo, r.esforcos
    me, md, ms, mi = 120.0, 150.0, 60.0, 150.0
    p = Prancha(largura, altura, me, md, ms, mi)
    util = largura - me - md
    kx = util / esf.vao

    def px(x_m: float) -> float:
        return me + x_m * kx

    amostras = esf.amostrar(320)

    # ================= 1. esquema de carga ==============================
    y_viga = ms + 148
    p.texto(me, ms + 22, "ESQUEMA ESTRUTURAL E CARREGAMENTO", 16, TINTA,
            negrito=True)
    p.texto(me, ms + 44,
            f"Faixa de 1 m de largura, biapoiada no vão de {num(esf.vao, 2)} m. "
            f"Cargas de servico (g + q).", 14, COTA)

    # a peca, esquematica
    p.linha(px(0), y_viga, px(esf.vao), y_viga, cor=TINTA, w=3.0)
    for x_m, rot in ((0.0, "A"), (esf.vao, "B")):
        p.add(f'<path d="M {px(x_m):.1f} {y_viga:.1f} l -13 22 l 26 0 z" '
              f'fill="none" stroke="{TINTA}" stroke-width="1.8"/>')
        p.linha(px(x_m) - 20, y_viga + 24, px(x_m) + 20, y_viga + 24, cor=TINTA, w=1.6)
        p.texto(px(x_m), y_viga + 46, rot, 15, TINTA, "middle", negrito=True)

    # setas de carga por trecho
    for t in esf.trechos:
        alt = 26 + 30 * (t.q / max(x.q for x in esf.trechos))
        p.linha(px(t.x_ini), y_viga - alt, px(t.x_fim), y_viga - alt,
                cor=DISTRIBUICAO, w=1.6)
        n = max(3, int((t.x_fim - t.x_ini) * kx / 26))
        for i in range(n + 1):
            xx = px(t.x_ini + (t.x_fim - t.x_ini) * i / n)
            p.add(f'<path d="M {xx:.1f} {y_viga - alt:.1f} L {xx:.1f} '
                  f'{y_viga - 5:.1f}" stroke="{DISTRIBUICAO}" stroke-width="1.1" '
                  f'marker-end="url(#setaVerde)"/>')
        p.texto((px(t.x_ini) + px(t.x_fim)) / 2, y_viga - alt - 10,
                f"{num(t.q, 2)} kN/m²", 14, DISTRIBUICAO, "middle", negrito=True)
    p._defs.append(
        f'<marker id="setaVerde" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto">'
        f'<path d="M0 1 L9 5 L0 9 z" fill="{DISTRIBUICAO}"/></marker>'
    )
    for x_m, val, lado in ((0.0, esf.R_a, "start"), (esf.vao, esf.R_b, "end")):
        p.texto(px(x_m) + (10 if lado == "start" else -10), y_viga + 68,
                f"R = {num(val, 2)} kN", 14, TINTA, lado)

    # cotas dos trechos
    y_cota = y_viga + 96
    for t, rot in zip(esf.trechos, ("patamar inf.", "lance", "patamar sup.")):
        p.cota_h(px(t.x_ini), px(t.x_fim), y_cota, f"{num(t.comprimento * 100)} cm")
        p.texto((px(t.x_ini) + px(t.x_fim)) / 2, y_cota + 30, rot, 13, COTA, "middle")

    # ================= 2. cortante ======================================
    p.texto(me, y_cota + 76, "FORÇA CORTANTE  V(x)", 16, TINTA, negrito=True)
    p.texto(me, y_cota + 98,
            f"Valores caracteristicos. Vd = γf × Vk = {num(esf.Vd, 2)} kN.",
            14, COTA)
    y0_v = y_cota + 108 + 96
    esc_v = 90.0 / max(abs(v) for _, _, v in amostras)
    pts = [(px(x), y0_v - v * esc_v) for x, _, v in amostras]
    corpo = ("M " + f"{px(0):.1f} {y0_v:.1f} L " +
             " L ".join(f"{a:.1f} {b:.1f}" for a, b in pts) +
             f" L {px(esf.vao):.1f} {y0_v:.1f} Z")
    p.add(f'<path d="{corpo}" fill="{DISTRIBUICAO}" opacity="0.16" stroke="none"/>')
    p.caminho(corpo, cor=DISTRIBUICAO, w=2.0)
    p.linha(px(0), y0_v, px(esf.vao), y0_v, cor=TINTA, w=1.4)
    p.texto(px(0) + 14, y0_v - esf.R_a * esc_v + 24,
            f"+{num(esf.R_a, 2)} kN", 14, DISTRIBUICAO, "start", negrito=True)
    p.texto(px(esf.vao) - 12, y0_v + esf.R_b * esc_v + 22,
            f"−{num(esf.R_b, 2)} kN", 14, DISTRIBUICAO, "end", negrito=True)
    p.eixo(px(esf.x_Mk_max), y0_v - 96, px(esf.x_Mk_max), y0_v + 96, folga=0)
    p.texto(px(esf.x_Mk_max) + 10, y0_v - 8, "V = 0", 13, EIXO)

    # ================= 3. momento =======================================
    p.texto(me, y0_v + 138, "MOMENTO FLETOR  M(x)", 16, TINTA, negrito=True)
    p.texto(me, y0_v + 160,
            "Desenhado do lado tracionado (para baixo): toda a face inferior "
            "traciona, por isso a armadura principal é toda inferior.",
            14, COTA)
    y0_m = y0_v + 208
    esc_m = 112.0 / max(m for _, m, _ in amostras)
    p.linha(px(0), y0_m, px(esf.vao), y0_m, cor=TINTA, w=1.4)
    ptm = [(px(x), y0_m + m * esc_m) for x, m, _ in amostras]
    p.add(f'<path d="M {px(0):.1f} {y0_m:.1f} L ' +
          " L ".join(f"{a:.1f} {b:.1f}" for a, b in ptm) +
          f' L {px(esf.vao):.1f} {y0_m:.1f} Z" fill="{PRINCIPAL}" opacity="0.13"/>')
    p.poligonal(ptm, cor=PRINCIPAL, w=2.2)

    xm = px(esf.x_Mk_max)
    ym = y0_m + esf.Mk_max * esc_m
    p.linha(xm, y0_m, xm, ym, cor=PRINCIPAL, w=1.1, tracejado="5 4")
    p.circulo(xm, ym, 4.4, preenche=PRINCIPAL)
    p.texto(xm, ym + 26, f"Mk = {num(esf.Mk_max, 2)} kN·m", 15, PRINCIPAL,
            "middle", negrito=True)
    p.texto(xm, ym + 46,
            f"Md = γf × Mk = {num(esf.gamma_f, 1)} × {num(esf.Mk_max, 2)} "
            f"= {num(esf.Md, 2)} kN·m", 14, COTA, "middle")

    # onde ficam as emendas, para o leitor ver que estão fora do pico
    det = r.detalhamento
    for i, xe in enumerate(det.emendas_x):
        xx = px(xe / 100.0)
        p.linha(xx, y0_m - 16, xx, y0_m + 16, cor=EIXO, w=1.6)
        p.texto(xx, y0_m - 24, "emenda", 12, EIXO, "middle")

    p.carimbo(
        "DIAGRAMAS DE ESFORÇOS DO CONJUNTO",
        [
            f"Esquema biapoiado, vão {num(esf.vao, 2)} m, faixa de 1 m. "
            f"γf = {num(esf.gamma_f, 1)}.",
            f"Carga total {num(esf.carga_total, 2)} kN por metro de largura; "
            f"momento máximo a {num(esf.x_Mk_max, 2)} m do apoio A.",
            "As emendas por traspasse foram levadas para as quebras do "
            "intradorso, onde o momento já caiu.",
        ],
    )
    return p.render()
