"""Gera todas as figuras a partir de um Resultado do motor.

Cada figura sai em SVG (fonte editável) e PNG (usado no documento). O manifesto
devolvido traz caminho, dimensões e legenda de cada uma - é ele que o
gerador do documento consome, então não existe lista de figuras digitada duas
vezes.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cairosvg

from engine.api import Resultado

from . import corte, deformacoes, detalhes, diagramas, formatos, plantas

ESCALA_PNG = 1.6


@dataclass
class Figura:
    chave: str
    titulo: str
    legenda: str
    svg: Path
    png: Path
    largura_px: int
    altura_px: int

    @property
    def proporcao(self) -> float:
        return self.altura_px / self.largura_px


def _emitir(chave, titulo, legenda, svg_txt, destino: Path) -> Figura:
    destino.mkdir(parents=True, exist_ok=True)
    svg = destino / f"{chave}.svg"
    png = destino / f"{chave}.png"
    svg.write_text(svg_txt, encoding="utf-8")
    cairosvg.svg2png(bytestring=svg_txt.encode(), write_to=str(png),
                     scale=ESCALA_PNG)
    import re
    w = int(float(re.search(r'width="([\d.]+)"', svg_txt).group(1)) * ESCALA_PNG)
    h = int(float(re.search(r'height="([\d.]+)"', svg_txt).group(1)) * ESCALA_PNG)
    return Figura(chave, titulo, legenda, svg, png, w, h)


def todas(r: Resultado, destino: Path) -> dict[str, Figura]:
    det = r.detalhamento
    lb = r.anc_gancho.lb_nec
    especificacoes = [
        ("geometria", "Geometria do lance",
         "Piso, espelho, inclinação e as espessuras h, h₁ e hm. A espessura "
         "que entra no peso próprio é hm, não h.",
         lambda: detalhes.geometria(r)),
        ("diagramas", "Diagramas de esforços",
         "Carregamento, força cortante e momento fletor do conjunto patamar + "
         "lance + patamar. Mk e Md saem daqui.",
         lambda: diagramas.desenhar(r)),
        ("dominios", "Deformações e domínios",
         "Seção, linha neutra na posição calculada, diagrama de deformações e "
         "a faixa de domínios em que o Kx caiu.",
         lambda: deformacoes.desenhar(r)),
        ("formatos_posicoes", "Formatos das barras",
         "Cada posição desenhada com suas cotas e a descrição do que ela e'.",
         lambda: formatos.posicoes(r)),
        ("alt_principal", "Armadura principal - alternativas",
         "Os quatro formatos válidos para a armadura principal.",
         lambda: formatos.alternativas(r, "principal")),
        ("alt_distribuicao", "Distribuição - alternativas",
         "Os dois formatos válidos para a armadura de distribuição.",
         lambda: formatos.alternativas(r, "distribuicao")),
        ("alt_borda", "Borda - alternativas",
         "Em L ou em grampo U, conforme a borda tenha uma ou duas faces livres.",
         lambda: formatos.alternativas(r, "borda")),
        ("alt_canto", "Canto reentrante - alternativas",
         "Barra dobrada com ancoragem no vértice, ou barras cruzadas.",
         lambda: formatos.alternativas(
             r, "canto",
             adotado="A" if det.detalhe_canto == "cruzadas" else "B")),
        ("alt_lance", "Barra do lance - inteira ou dividida",
         "As duas maneiras de executar a barra principal do lance.",
         lambda: formatos.alternativas(r, "lance")),
        ("corte", "Corte longitudinal com armadura",
         "Corte A-A' com todas as posições. N4, N5 e N6 correm perpendiculares "
         "ao papel e por isso aparecem como pontos.",
         lambda: corte.desenhar(r)),
        ("planta_inferior", "Planta - face inferior",
         "Escada desenrolada, só com a armadura de face inferior: a que "
         "resiste ao momento fletor.",
         lambda: plantas.inferior(r)),
        ("planta_superior", "Planta - face superior",
         "Escada desenrolada, só com a armadura de face superior: ancoragem "
         "de canto e borda.",
         lambda: plantas.superior(r)),
        ("canto", "Canto reentrante",
         "O mecanismo que empurra o cobrimento para fora e as barras que "
         "seguram a armadura principal.",
         lambda: detalhes.canto(r)),
        ("n2_dividida", "Divisão da barra do lance",
         f"Arranque (N2a) e barra do lance (N2b) unidas por traspasse de no "
         f"mínimo lb,nec = {lb:.1f} cm.".replace(".", ","),
         lambda: detalhes.n2_dividida(r)),
    ]
    saida: dict[str, Figura] = {}
    for chave, titulo, legenda, fn in especificacoes:
        saida[chave] = _emitir(chave, titulo, legenda, fn(), destino)
    return saida
