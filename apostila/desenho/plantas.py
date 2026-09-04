"""Plantas de armadura, inferior e superior, em estilo de prancha.

Separadas de proposito: o leitor ve primeiro só o que traciona por flexão
(face inferior) e depois só o que segura canto e borda (face superior).
As duas plantas mostram a escada desenrolada - patamar, lance e patamar em
verdadeira grandeza no comprimento desenvolvido, que é como o armador ve a
ferragem na forma.
"""
from __future__ import annotations

from engine.api import Resultado
from engine.barras import _dev

from .prancha import (COR_FAMILIA, COTA, CONCRETO, EIXO, Escala, Prancha,
                      TINTA, num)


def _titulo(b) -> str:
    esp = f" c/ {num(b.espacamento_cm, 1)}" if b.espacamento_cm else ""
    return (f"{b.codigo} · {b.quantidade} Ø{num(b.bitola_mm, 1)}{esp} · "
            f"C = {num(b.comprimento_cm)} cm")


def _quadro(r: Resultado, face: str, largura: float, altura: float, rail: float):
    geo, det = r.geo, r.detalhamento
    me = md = rail
    ms, mi = 100.0, 285.0
    p = Prancha(largura, altura, me, md, ms, mi)

    dev = _dev(geo, geo.x0, geo.x3)
    util_x = largura - me - md
    util_y = altura - ms - mi
    k = min(util_x / dev, util_y / geo.largura)
    ox = me + (util_x - dev * k) / 2
    oy = ms + (util_y - geo.largura * k) / 2

    def sx(s: float) -> float:            # s = comprimento desenvolvido
        return ox + s * k

    def sy(y: float) -> float:            # y = posição na largura
        return oy + (geo.largura - y) * k

    def s_de_x(x: float) -> float:
        return _dev(geo, geo.x0, x)

    # ---- contorno da laje desenrolada -----------------------------------
    p.add(f'<rect x="{sx(0):.1f}" y="{sy(geo.largura):.1f}" '
          f'width="{dev * k:.1f}" height="{geo.largura * k:.1f}" '
          f'fill="{CONCRETO}" stroke="{TINTA}" stroke-width="1.9"/>')

    # limites patamar / lance / patamar
    for x, rot in ((geo.x1, "inicio do lance"), (geo.x2, "fim do lance")):
        xs = sx(s_de_x(x))
        p.linha(xs, sy(geo.largura), xs, sy(0), cor=EIXO, w=1.2,
                tracejado="12 5")
        p.texto(xs, sy(geo.largura) - 14, rot, 13, EIXO, "middle")
    for rot, xa, xb in (("PATAMAR INFERIOR", geo.x0, geo.x1),
                        ("LANCE (desenvolvido)", geo.x1, geo.x2),
                        ("PATAMAR SUPERIOR", geo.x2, geo.x3)):
        p.texto((sx(s_de_x(xa)) + sx(s_de_x(xb))) / 2, sy(0) + 30, rot, 13,
                COTA, "middle")

    # eixo longitudinal
    p.eixo(sx(0), sy(geo.largura / 2), sx(dev), sy(geo.largura / 2))

    # ---- marca do corte A-A' --------------------------------------------
    xs_corte = sx(s_de_x(geo.x1 + geo.projecao_lance * 0.30))
    p.marca_corte(xs_corte, sy(geo.largura) - 46, sy(0) + 46, "A")

    # ---- barras ----------------------------------------------------------
    alvos = [b for b in det.posicoes if b.face == face]
    for b in alvos:
        cor = COR_FAMILIA[b.familia]
        if b.direcao == "longitudinal":
            # correm no sentido da subida: uma linha por barra, ao longo da largura
            for y in det.xs_principal:
                p.linha(sx(s_de_x(b.x_ini)), sy(y), sx(s_de_x(b.x_fim)), sy(y),
                        cor=cor, w=1.9)
        else:
            xs = {
                "N4": det.xs_distribuicao,
                "N7": det.xs_borda,
                "N6": (geo.xk1 - 6, geo.xk1 + 6, geo.xk2 - 6, geo.xk2 + 6),
                "N8": (geo.xk1, geo.xk2),
            }.get(b.codigo, (b.x_ini,))
            for x in xs:
                if not (geo.x0 <= x <= geo.x3):
                    continue
                xx = sx(s_de_x(x))
                if b.codigo == "N7":
                    perna = min(b.trecho_reto_cm, geo.largura / 2 - geo.c) * k
                    p.linha(xx, sy(geo.largura - geo.c),
                            xx, sy(geo.largura - geo.c) + perna, cor=cor, w=2.1)
                    p.linha(xx, sy(geo.c), xx, sy(geo.c) - perna, cor=cor, w=2.1)
                else:
                    p.linha(xx, sy(geo.c), xx, sy(geo.largura - geo.c),
                            cor=cor, w=1.9)

    # ---- chamadas --------------------------------------------------------
    ancoras = {
        "N1": (geo.x1 * 0.5, geo.largura * 0.80),
        "N2": (geo.x1 + geo.projecao_lance * 0.45, geo.largura * 0.22),
        "N3": (geo.x2 + (geo.x3 - geo.x2) * 0.5, geo.largura * 0.80),
        "N4": (det.xs_distribuicao[len(det.xs_distribuicao) // 4], geo.largura * 0.5),
        "N5": (geo.x1, geo.largura * 0.35),
        "N6": (geo.xk1, geo.largura * 0.5),
        "N8": (geo.xk2, geo.largura * 0.32),
        "N7": (det.xs_borda[len(det.xs_borda) // 3], geo.largura - geo.c),
    }
    for b in alvos:
        a = ancoras.get(b.codigo)
        if a is None:
            continue
        p.chamada(sx(s_de_x(a[0])), sy(a[1]), _titulo(b), b.descricao,
                  COR_FAMILIA[b.familia])

    # ---- cotas -----------------------------------------------------------
    y_cota = sy(0) + 132
    for xa, xb in ((geo.x0, geo.x1), (geo.x1, geo.x2), (geo.x2, geo.x3)):
        p.cota_h(sx(s_de_x(xa)), sx(s_de_x(xb)), y_cota,
                 f"{num(_dev(geo, xa, xb))} desenv.", chamada_de=sy(0))
    p.cota_h(sx(0), sx(dev), y_cota + 46, f"{num(dev)} (comprimento desenvolvido)")
    p.cota_v(sy(geo.largura), sy(0), sx(dev) + 62, f"{num(geo.largura)}",
             chamada_de=sx(dev))
    return p


def inferior(r: Resultado, largura: float = 1900, altura: float = 1080) -> str:
    rail = _rail(r, "inferior")
    p = _quadro(r, "inferior", largura, altura, rail)
    det = r.detalhamento
    p.carimbo(
        "PLANTA DE ARMADURA - FACE INFERIOR",
        [
            "Escada desenrolada, vista de cima. Cotas em cm.",
            "Barras longitudinais (sentido da subida) resistem ao momento "
            "fletor; as transversais distribuem a carga e controlam fissura.",
            f"A distribuição (N4) fica POR CIMA da principal: quem precisa "
            f"ficar longe da linha neutra é a principal.",
        ],
        escala="Corte A-A' na figura do corte longitudinal",
    )
    return p.render()


def superior(r: Resultado, largura: float = 1900, altura: float = 1080) -> str:
    rail = _rail(r, "superior")
    p = _quadro(r, "superior", largura, altura, rail)
    p.carimbo(
        "PLANTA DE ARMADURA - FACE SUPERIOR",
        [
            "Escada desenrolada, vista de cima. Cotas em cm.",
            "Neste esquema (biapoiado) NÃO há momento negativo sobre os apoios: "
            "a face superior recebe só ancoragem de canto (N6) e borda (N7).",
            "Se os apoios reais oferecerem engastamento parcial, é preciso "
            "acrescentar armadura negativa sobre eles - reveja o esquema.",
        ],
    )
    return p.render()


def _rail(r: Resultado, face: str) -> float:
    sonda = Prancha(10, 10)
    for b in r.detalhamento.posicoes:
        if b.face == face:
            sonda.chamada(0, 0, _titulo(b), b.descricao, "#000")
    return max(210.0, min(430.0, sonda.largura_rail()))
