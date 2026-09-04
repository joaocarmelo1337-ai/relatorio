"""Corte longitudinal da escada, em estilo de prancha.

Traz o que faltava no desenho antigo: hachura de concreto, apoios hachurados,
linhas de eixo, marca de corte transversal, cadeia de cotas com linha de
chamada, e chamadas de ferro posicionadas pelo algoritmo de `prancha`, sem
nenhuma coordenada de rótulo escrita a mao.
"""
from __future__ import annotations

from engine.api import Resultado
from engine.barras import Posicao

from .base import caminho_barra, contorno_peca, offset_intradorso, ponto_na_barra
from .prancha import (COR_FAMILIA, COTA, EIXO, Escala, Prancha, TINTA, num)


BANDA_COTA = 116.0   # faixa reservada para a cota vertical, à direita da peça


def _escala(geo, largura, altura, me, md, ms, mi):
    """Escala única para os dois eixos, com o desenho centrado no quadro."""
    util_x = largura - me - md
    util_y = altura - ms - mi
    alt_peca = geo.subida + geo.h
    k = min(util_x / geo.x3, util_y / alt_peca)
    sobra_x = util_x - geo.x3 * k
    sobra_y = util_y - alt_peca * k
    return Escala(
        x0=0.0, y0=-geo.h, k=k,
        origem_px=(me + sobra_x / 2, altura - mi - sobra_y / 2),
    )


def desenhar(r: Resultado, largura: float = 2100, altura: float = 1080) -> str:
    """Duas passadas: a primeira só mede o texto das chamadas para dimensionar
    as margens laterais; a segunda desenha de fato. Assim nenhum rótulo sai do
    quadro, seja qual for a geometria do config."""
    rail = _medir_rail(r)
    return _montar(r, largura, altura, rail)


def _medir_rail(r: Resultado) -> float:
    sonda = Prancha(10, 10)
    for b in r.detalhamento.posicoes:
        sonda.chamada(0, 0, _titulo(b), b.descricao, "#000")
    sonda.chamada(0, 0, "N6 - repetida no canto superior",
                  "ancoragem do canto reentrante superior", "#000")
    return max(200.0, min(430.0, sonda.largura_rail()))


def _titulo(b: Posicao) -> str:
    esp = f" c/ {num(b.espacamento_cm, 1)}" if b.espacamento_cm else ""
    return (f"{b.codigo} · {b.quantidade} Ø{num(b.bitola_mm, 1)}{esp} · "
            f"C = {num(b.comprimento_cm)} cm")


def _montar(r: Resultado, largura: float, altura: float, rail: float) -> str:
    geo, det = r.geo, r.detalhamento
    me = md = rail
    ms, mi = 80.0, 220.0
    p = Prancha(largura, altura, me, md, ms, mi)
    # Reserva uma faixa entre a peça e o trilho de chamadas só para a cota
    # vertical. Sem ela, uma escada alta e estreita joga o texto da cota em
    # cima dos rótulos de ferro.
    e = _escala(geo, largura, altura, me, md + BANDA_COTA, ms, mi)

    # ---------------- concreto -------------------------------------------
    p.concreto(contorno_peca(geo, e))

    # arestas verticais das extremidades
    for x in (geo.x0, geo.x3):
        p.linha(e.px(x), e.py(geo.intradorso(x)), e.px(x),
                e.py(0.0 if x == geo.x0 else geo.subida), cor=TINTA, w=1.9)

    # ---------------- apoios ---------------------------------------------
    lv, hv = 26.0, 34.0
    for x, topo, alinha_dir in ((geo.x0, -geo.h, False), (geo.x3, geo.subida - geo.h, True)):
        x_ini = x - lv if alinha_dir else x
        p.add(
            f'<rect x="{e.px(x_ini):.1f}" y="{e.py(topo):.1f}" '
            f'width="{lv * e.k:.1f}" height="{hv * e.k:.1f}" fill="#eceae5" '
            f'stroke="{TINTA}" stroke-width="1.3"/>'
        )
        p.add(
            f'<rect x="{e.px(x_ini):.1f}" y="{e.py(topo):.1f}" '
            f'width="{lv * e.k:.1f}" height="{hv * e.k:.1f}" '
            f'fill="url(#hachuraApoio)" stroke="none" opacity="0.55"/>'
        )
        p.texto(e.px(x_ini) + lv * e.k / 2, e.py(topo) + hv * e.k + 22,
                "Vesc2" if alinha_dir else "Vesc1", 14, COTA, "middle")
        p.eixo(e.px(x_ini) + lv * e.k / 2, e.py(topo) - 24,
               e.px(x_ini) + lv * e.k / 2, e.py(topo) + hv * e.k + 4)

    # ---------------- linha de eixo do lance -----------------------------
    meio = offset_intradorso(geo, geo.x1 - 18, geo.x2 + 18, geo.h / 2)
    p.poligonal([e.p(x, y) for x, y in meio], cor=EIXO, w=0.9,
                tracejado="16 5 3 5", opacidade=0.8)

    # ---------------- marca de corte transversal B-B ---------------------
    x_corte = geo.x1 + geo.projecao_lance * 0.42
    p.marca_corte(e.px(x_corte), e.py(geo.intradorso(x_corte) + geo.h) - 54,
                  e.py(geo.intradorso(x_corte)) + 54, "B")

    # ---------------- barras ---------------------------------------------
    longitudinais = [b for b in det.posicoes if b.direcao == "longitudinal"]
    transversais = [b for b in det.posicoes if b.direcao == "transversal"]

    for b in longitudinais:
        cor = COR_FAMILIA[b.familia]
        g_ini = det.gancho_cm if b.codigo == "N1" and b.ganchos_cm else 0.0
        g_fim = det.gancho_cm if b.codigo == "N3" and b.ganchos_cm else 0.0
        p.caminho(
            caminho_barra(geo, e, b.x_ini, b.x_fim, b.offset_cm, g_ini, g_fim),
            cor=cor, w=3.4,
        )

    # traspasses destacados
    lb = r.anc_gancho.lb_nec
    n1, n2, n3 = (det.por_codigo(c) for c in ("N1", "N2", "N3"))
    for xa, xb in ((n2.x_ini, n1.x_fim), (n3.x_ini, n2.x_fim)):
        p.caminho(
            caminho_barra(geo, e, xa, xb, n1.offset_cm),
            cor="#1f8a70", w=13, opacidade=0.22, cap="round",
        )
    xm = (n3.x_ini + n2.x_fim) / 2
    px, py = ponto_na_barra(geo, xm, n1.offset_cm)
    p.chamada(e.px(px), e.py(py), f"traspasse ≥ lb,nec = {num(lb, 1)} cm",
              "emenda de N2 com N3, fora do momento máximo", "#1f8a70")

    # transversais aparecem como seção: pontinhos
    for b in transversais:
        cor = COR_FAMILIA[b.familia]
        if b.codigo == "N4":
            xs = det.xs_distribuicao
        elif b.codigo == "N6":
            xs = [geo.xk1 + i * 14 - 7 for i in range(2)] + \
                 [geo.xk2 + i * 14 - 7 for i in range(2)]
        else:
            xs = [b.x_ini]
        for x in xs:
            if not (geo.x0 <= x <= geo.x3):
                continue
            cx, cy = ponto_na_barra(geo, x, b.offset_cm)
            p.circulo(e.px(cx), e.py(cy), 4.6 if b.codigo != "N4" else 3.9,
                      preenche="#ffffff" if b.face == "superior" else cor,
                      cor=cor if b.face == "superior" else None, w=2.4)

    # ---------------- chamadas de ferro ----------------------------------
    ancoras = {
        "N1": (geo.x1 * 0.45, n1.offset_cm),
        "N2": ((n2.x_ini + n2.x_fim) / 2, n2.offset_cm),
        "N3": (geo.x2 + (geo.x3 - geo.x2) * 0.55, n3.offset_cm),
        "N4": (det.xs_distribuicao[len(det.xs_distribuicao) // 3],
               det.por_codigo("N4").offset_cm),
        "N5": (geo.x1, det.por_codigo("N5").offset_cm) if any(
            b.codigo == "N5" for b in det.posicoes) else None,
        "N6": (geo.xk1, det.por_codigo("N6").offset_cm),
    }
    for b in det.posicoes:
        alvo = ancoras.get(b.codigo)
        if alvo is None:
            continue
        cx, cy = ponto_na_barra(geo, alvo[0], alvo[1])
        p.chamada(e.px(cx), e.py(cy), _titulo(b), b.descricao,
                  COR_FAMILIA[b.familia])
    # N6 aparece nos dois cantos reentrantes
    cx, cy = ponto_na_barra(geo, geo.xk2, det.por_codigo("N6").offset_cm)
    p.chamada(e.px(cx), e.py(cy), "N6 · repetida no canto superior",
              "ancoragem do canto reentrante superior", COR_FAMILIA["canto"])

    # ---------------- cotas ----------------------------------------------
    y_lin1 = e.py(-geo.h) + 66
    y_lin2 = y_lin1 + 44
    p.cota_h(e.px(geo.x0), e.px(geo.x1), y_lin1, num(geo.patamar_inf),
             chamada_de=e.py(-geo.h))
    p.cota_h(e.px(geo.x1), e.px(geo.x2), y_lin1,
             f"{num(geo.projecao_lance)}  ({geo.n} × {num(geo.s, 1)})",
             chamada_de=e.py(-geo.h))
    p.cota_h(e.px(geo.x2), e.px(geo.x3), y_lin1, num(geo.patamar_sup),
             chamada_de=e.py(geo.subida - geo.h))
    p.cota_h(e.px(geo.x0), e.px(geo.x3), y_lin2, num(geo.vao_total))

    # A cota vertical fica na sobra entre a peça e o trilho de chamadas;
    # sem isso, uma escada curta e alta empurraria o texto para cima do rótulo.
    x_ver = e.px(geo.x3) + BANDA_COTA * 0.40
    p.cota_v(e.py(geo.subida), e.py(0.0), x_ver,
             f"{num(geo.subida)}  ({geo.n} × {num(geo.e, 1)})",
             chamada_de=e.px(geo.x3))

    # espessura da laje: cota perpendicular a face, com chamada para fora
    x_esp = geo.x1 + geo.projecao_lance * 0.30
    pa = ponto_na_barra(geo, x_esp, 0.0)
    pb = ponto_na_barra(geo, x_esp, geo.h)
    ax, ay, bx, by = e.px(pa[0]), e.py(pa[1]), e.px(pb[0]), e.py(pb[1])
    p.linha(ax, ay, bx, by, cor=COTA, w=1.2)
    for cx, cy in ((ax, ay), (bx, by)):
        p.linha(cx - 5, cy + 5, cx + 5, cy - 5, cor=COTA, w=1.3)
    dx, dy = bx - ax, by - ay
    p.linha(bx, by, bx - dy * 1.7, by + dx * 1.7, cor=COTA, w=0.7, opacidade=0.9)
    p.texto(bx - dy * 1.7 - 8, by + dx * 1.7 + 4, f"h = {num(geo.h)} cm",
            14, COTA, "end")

    # ---------------- carimbo --------------------------------------------
    p.carimbo(
        "CORTE A-A'  ·  armadura completa",
        [
            f"Cotas em cm  ·  laje h = {num(geo.h)} cm  ·  cobrimento "
            f"c = {num(geo.c, 1)} cm  ·  inclinação α = {num(geo.alpha_graus, 1)}°",
            f"Concreto C{num(r.cfg['materiais']['fck'])}  ·  aço "
            f"{r.cfg['materiais']['aco_principal']} (principal) e "
            f"{r.cfg['materiais']['aco_distribuicao']} (distribuição)",
            "N4, N5 e N6 correm perpendiculares ao papel: aparecem em seção, como pontos.",
        ],
        escala=f"Corte B-B na Figura seguinte",
    )
    return p.render()
