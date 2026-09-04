"""Formatos de barra: o adotado em cada posição e as alternativas válidas.

Duas famílias de figura:
  posições(r)      - cada N-x desenhada com suas cotas reais e sua descrição
  alternativas(r,f)- todos os formatos possíveis daquela família, lado a lado

Nenhuma coordenada de rótulo é escrita a mao: as cotas saem do comprimento
calculado e o texto sai do catalogo em engine/formatos.py.
"""
from __future__ import annotations

from engine import formatos as cat
from engine.api import Resultado

from .prancha import COR_FAMILIA, COTA, Prancha, TINTA, num


def _desenha_forma(p, x0, y0, larg, alt, poly, cor, lw=4.0):
    """Desenha uma poly normalizada dentro da caixa dada."""
    pts = [(x0 + u * larg, y0 - v * alt) for u, v in poly]
    p.poligonal(pts, cor=cor, w=lw, cap="round")
    return pts


# ===========================================================================
def posicoes(r: Resultado, largura: float = 1500) -> str:
    """Uma linha por posição: forma, cotas e a descrição do que ela e'."""
    det = r.detalhamento
    linha_h = 118.0
    altura = 150 + linha_h * len(det.posicoes) + 190
    p = Prancha(largura, altura, 70, 70, 60, 190)

    x_forma, larg_forma = 600.0, 560.0
    p.texto(70, 92, "FORMATOS DAS BARRAS", 17, TINTA, negrito=True)
    p.texto(70, 116,
            "Cada posição vem com a descrição do que ela e'. O comprimento C "
            "é medido no eixo da barra e já inclui os ganchos.", 14, COTA)

    y = 168.0
    for b in det.posicoes:
        cor = COR_FAMILIA[b.familia]
        forma = next(f for f in b.formatos_alternativos if f.id == b.formato_adotado)

        p.texto(70, y + 4, b.codigo, 17, cor, negrito=True)
        p.texto(70, y + 26, b.descricao, 13.5, COTA)
        p.texto(70, y + 46,
                f"{b.quantidade} Ø{num(b.bitola_mm, 1)}"
                + (f" c/ {num(b.espacamento_cm, 1)} cm" if b.espacamento_cm else "")
                + f" · formato {forma.id}: {forma.nome.lower()}", 13, COTA)

        # forma, com o trecho reto em escala relativa ao maior comprimento
        maior = max(x.comprimento_cm for x in det.posicoes)
        w = larg_forma * b.trecho_reto_cm / maior
        # gancho desenhado PARA CIMA: é para dentro da laje que ele dobra
        alt_g = 34.0 * (det.gancho_cm / r.geo.h) if b.ganchos_cm else 0.0
        poly = list(forma.poly) if b.ganchos_cm else [(0.0, 0.0), (1.0, 0.0)]
        pts = _desenha_forma(p, x_forma, y + 34, w, alt_g or 1.0, poly, cor)

        # cota do trecho reto; o gancho recebe rótulo curto ao lado
        retos = [q[0] for q in pts]
        p.cota_h(min(retos), max(retos), y + 64, f"{num(b.trecho_reto_cm)} cm")
        if b.ganchos_cm:
            p.texto(pts[0][0] - 8, y + 34 - alt_g - 6,
                    f"gancho {num(det.gancho_cm)}", 12, cor, "end")

        p.texto(largura - 70, y + 4, f"C = {num(b.comprimento_cm)} cm", 15, cor,
                "end", negrito=True)
        p.texto(largura - 70, y + 26,
                f"total {num(b.comprimento_total_m, 1)} m", 13, COTA, "end")
        y += linha_h

    p.carimbo(
        "QUADRO DE FORMATOS",
        [
            f"Gancho de {num(det.gancho_cm)} cm = h - 2c (limite geométrico). "
            f"Mínimo normativo para o gancho adotado: "
            f"{num(det.gancho_normativo_cm)} cm.",
            "Comprimentos no eixo da barra; a barra dobrada sai ligeiramente "
            "mais curta no corte, porque a dobra tem raio.",
            "As alternativas de cada formato estão nas figuras seguintes.",
        ],
    )
    return p.render()


# ===========================================================================
TITULOS = {
    "principal": "ARMADURA PRINCIPAL - formatos possíveis",
    "distribuicao": "ARMADURA DE DISTRIBUIÇÃO - formatos possíveis",
    "borda": "ARMADURA DE BORDA - formatos possíveis",
    "canto": "ANCORAGEM DO CANTO REENTRANTE - soluções possíveis",
    "lance": "BARRA DO LANCE - inteira ou dividida",
}


def alternativas(r: Resultado, familia: str, largura: float = 1400) -> str:
    """Todos os formatos válidos de uma família, lado a lado.

    A figura mostra só o DESENHO de cada opção; o texto de quando-usar,
    a favor e contra vai na tabela do documento, logo abaixo - assim o
    mesmo texto não aparece duas vezes e o desenho fica grande o bastante
    para ser lido na página.
    """
    opcoes = cat.CATALOGO[familia]
    cor = COR_FAMILIA[familia]
    por_formato: dict[str, list[str]] = {}
    for b in r.detalhamento.posicoes:
        if b.familia == familia:
            por_formato.setdefault(b.formato_adotado, []).append(b.codigo)

    bloco = 132.0
    altura = 150 + bloco * len(opcoes) + 96
    p = Prancha(largura, altura, 60, 60, 46, 96)

    p.texto(60, 74, TITULOS[familia], 20, TINTA, negrito=True)
    p.texto(60, 102,
            "Nenhum destes está errado: a escolha é decisão de projeto e de "
            "obra. A tabela ao lado diz quando cada um compensa.", 16, COTA)
    p.linha(60, 122, largura - 60, 122, cor=COTA, w=0.9, opacidade=0.5)

    y = 178.0
    for f in opcoes:
        quais = por_formato.get(f.id, [])
        usado = bool(quais)
        if usado:
            p.add(f'<rect x="48" y="{y - 40:.0f}" width="{largura - 96:.0f}" '
                  f'height="{bloco - 16:.0f}" rx="7" fill="{cor}" opacity="0.06"/>')
        p.texto(70, y, f"Opção {f.id}", 19, cor if usado else TINTA, negrito=True)
        p.texto(70, y + 26, f.nome, 16, TINTA if usado else COTA)
        if usado:
            p.texto(70, y + 50, f"adotado em {', '.join(quais)}", 15, cor,
                    negrito=True)
        _desenha_forma(p, 620, y + 22, largura - 760, 46, f.poly,
                       cor, lw=6.0 if usado else 4.0)
        y += bloco

    p.carimbo(
        "FORMATOS ALTERNATIVOS",
        ["O formato realçado é o adotado no exemplo desta apostila.",
         "Trocar de formato muda o comprimento de corte e o lb,nec "
         "(alpha = 0,7 com gancho, 1,0 reto), nunca a área de aço calculada."],
    )
    return p.render()
