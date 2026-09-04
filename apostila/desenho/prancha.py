"""Mini-biblioteca de desenho técnico em SVG.

O que ela resolve, e que o código antigo fazia na mao:
  * hachura de concreto e preenchimento de corte;
  * linhas de eixo (traco-ponto) e marca de corte A-A';
  * cotas com linha de chamada, extensão e ticks a 45 graus;
  * posicionamento AUTOMATICO das chamadas de ferro, sem sobreposição.

O posicionador de chamadas usa "pool adjacent violators": é a colocação 1D
que minimiza o deslocamento quadrático total sujeita a não haver sobreposição.
Resultado: rótulos na ordem dos ancoras (linhas-guia nunca se cruzam) e
espaçamento mínimo garantido.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

# --- paleta ---------------------------------------------------------------
TINTA = "#23201d"        # contorno de peca
CONCRETO = "#f2efe9"     # miolo de concreto em corte
HACHURA = "#b9b2a6"
COTA = "#6c6459"
EIXO = "#7d8fa3"
PRINCIPAL = "#c0392b"
DISTRIBUICAO = "#1f8a70"
ANCORAGEM = "#6c5ce7"
BORDA = "#b9770e"
APOIO = "#8d857a"
FUNDO = "#ffffff"
FONTE = "Liberation Sans, Helvetica, Arial, sans-serif"

COR_FAMILIA = {
    "principal": PRINCIPAL,
    "distribuicao": DISTRIBUICAO,
    "canto": ANCORAGEM,
    "borda": BORDA,
    "lance": PRINCIPAL,
}


def esc(t: str) -> str:
    return (
        str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def num(v: float, casas: int = 0) -> str:
    """Número no formato brasileiro, sem zero decimal inutil."""
    s = f"{v:.{casas}f}"
    if casas:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


def largura_texto(texto: str, tamanho: float) -> float:
    """Estimativa da largura de um texto em px (Liberation Sans ~0,52 em)."""
    estreitos = sum(texto.count(c) for c in "iljItf.,:;'|()[] ")
    largos = sum(texto.count(c) for c in "mwMW@")
    normal = len(texto) - estreitos - largos
    return tamanho * (0.30 * estreitos + 0.52 * normal + 0.85 * largos)


# ===========================================================================
def distribuir(desejadas: list[float], passo: float, lo: float, hi: float) -> list[float]:
    """Colocacao 1D sem sobreposição, mantendo a ordem dos ancoras.

    Recebe as posições IDEAIS (a do ancora de cada rótulo) e devolve posições
    finais separadas por pelo menos `passo`, dentro de [lo, hi], minimizando a
    soma dos deslocamentos ao quadrado. Algoritmo: pool adjacent violators.
    """
    if not desejadas:
        return []
    ordem = sorted(range(len(desejadas)), key=lambda i: desejadas[i])
    alvo = [desejadas[i] for i in ordem]

    # blocos: (soma dos alvos deslocados, quantidade, indice inicial)
    blocos: list[list[float]] = []
    for k, a in enumerate(alvo):
        blocos.append([a - k * passo, 1.0, float(k)])
        while len(blocos) > 1:
            b, ant = blocos[-1], blocos[-2]
            if ant[0] / ant[1] <= b[0] / b[1]:
                break
            blocos.pop()
            ant[0] += b[0]
            ant[1] += b[1]

    saida = [0.0] * len(alvo)
    k = 0
    for soma, qtd, _ in blocos:
        base = soma / qtd
        for j in range(int(qtd)):
            saida[k] = base + k * passo
            k += 1

    # respeita os limites do quadro sem quebrar o espaçamento
    total = (len(saida) - 1) * passo
    if saida[0] < lo:
        saida = [lo + i * passo for i in range(len(saida))]
    if saida[-1] > hi:
        inicio = max(lo, hi - total)
        saida = [inicio + i * passo for i in range(len(saida))]

    final = [0.0] * len(desejadas)
    for pos, i in zip(saida, ordem):
        final[i] = pos
    return final


def rail_para(pares, minimo=200.0, maximo=460.0, tamanho=14.5) -> float:
    """Margem lateral necessária para uma lista de (titulo, descrição).

    Usada nas duas passadas de cada figura: mede primeiro, desenha depois.
    Assim nenhum rótulo sai do quadro, seja qual for a geometria do config.
    """
    if not pares:
        return minimo
    larg = max(
        max(largura_texto(a, tamanho), largura_texto(b, tamanho - 1.5))
        for a, b in pares
    )
    return max(minimo, min(maximo, larg + 44))


# ===========================================================================
@dataclass
class Chamada:
    """Uma chamada de ferro: duas linhas + o ponto que ela aponta.

    A primeira linha é a identificação técnica (posição, bitola, espaçamento,
    comprimento). A segunda é a descrição do que a barra É - regra do projeto:
    o código N-x nunca aparece sozinho, nem no desenho.
    """
    ancora: tuple[float, float]     # px, no espaço do desenho
    titulo: str
    descricao: str
    cor: str
    lado: str = "auto"              # "esq" | "dir" | "auto"

    def largura(self, tamanho: float) -> float:
        return max(
            largura_texto(self.titulo, tamanho),
            largura_texto(self.descricao, tamanho - 1.5),
        )


@dataclass
class Prancha:
    largura: float
    altura: float
    margem_esq: float = 190.0
    margem_dir: float = 190.0
    margem_sup: float = 70.0
    margem_inf: float = 120.0
    fundo: str = FUNDO

    _defs: list[str] = field(default_factory=list)
    _corpo: list[str] = field(default_factory=list)
    _cotas: list[str] = field(default_factory=list)
    _chamadas: list[Chamada] = field(default_factory=list)

    # -- primitivas -------------------------------------------------------
    def add(self, svg: str) -> None:
        self._corpo.append(svg)

    def linha(self, x1, y1, x2, y2, cor=TINTA, w=1.0, tracejado=None, opacidade=1.0, cap="butt"):
        d = f' stroke-dasharray="{tracejado}"' if tracejado else ""
        self.add(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{cor}" stroke-width="{w}" stroke-linecap="{cap}"'
            f' opacity="{opacidade}"{d}/>'
        )

    def caminho(self, d, cor=TINTA, w=1.0, preenche="none", tracejado=None,
                opacidade=1.0, cap="round"):
        dd = f' stroke-dasharray="{tracejado}"' if tracejado else ""
        self.add(
            f'<path d="{d}" fill="{preenche}" stroke="{cor}" stroke-width="{w}" '
            f'stroke-linejoin="round" stroke-linecap="{cap}" opacity="{opacidade}"{dd}/>'
        )

    def poligonal(self, pts, **kw):
        d = "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts)
        self.caminho(d, **kw)

    def texto(self, x, y, t, tamanho=15, cor=TINTA, ancora="start", negrito=False,
              italico=False, rotacao=None, opacidade=1.0):
        peso = ' font-weight="600"' if negrito else ""
        it = ' font-style="italic"' if italico else ""
        rot = f' transform="rotate({rotacao} {x:.2f} {y:.2f})"' if rotacao else ""
        self.add(
            f'<text x="{x:.2f}" y="{y:.2f}" font-size="{tamanho}" fill="{cor}" '
            f'text-anchor="{ancora}" font-family="{FONTE}" opacity="{opacidade}"'
            f'{peso}{it}{rot}>{esc(t)}</text>'
        )

    def circulo(self, x, y, r, preenche=TINTA, cor=None, w=1.0):
        borda = f' stroke="{cor}" stroke-width="{w}"' if cor else ""
        self.add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{preenche}"{borda}/>')

    def retangulo(self, x, y, w, h, preenche="none", cor=TINTA, lw=1.0, raio=0):
        r = f' rx="{raio}"' if raio else ""
        self.add(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'fill="{preenche}" stroke="{cor}" stroke-width="{lw}"{r}/>'
        )

    # -- recorte (para figuras de detalhe) --------------------------------
    _n_clip: int = 0

    def abrir_recorte(self, x, y, w, h, moldura=True):
        """Tudo desenhado até `fechar_recorte` fica limitado a está janela.

        As figuras de detalhe desenham a peca inteira e mostram só um pedaco;
        sem isto o resto da escada vaza para fora do quadro.
        """
        self._n_clip += 1
        cid = f"corte{self._n_clip}"
        self._defs.append(
            f'<clipPath id="{cid}"><rect x="{x:.1f}" y="{y:.1f}" '
            f'width="{w:.1f}" height="{h:.1f}"/></clipPath>'
        )
        self.add(f'<g clip-path="url(#{cid})">')
        self._moldura = (x, y, w, h) if moldura else None

    def fechar_recorte(self):
        self.add("</g>")
        if getattr(self, "_moldura", None):
            x, y, w, h = self._moldura
            self.retangulo(x, y, w, h, cor=COTA, lw=1.0)
            self._moldura = None

    # -- elementos de prancha ---------------------------------------------
    def concreto(self, d: str) -> None:
        """Peca em corte: miolo claro + hachura a 45 graus + contorno."""
        self.add(f'<path d="{d}" fill="{CONCRETO}" stroke="none"/>')
        self.add(f'<path d="{d}" fill="url(#hachura)" stroke="none"/>')
        self.add(
            f'<path d="{d}" fill="none" stroke="{TINTA}" stroke-width="1.9" '
            f'stroke-linejoin="round"/>'
        )

    def eixo(self, x1, y1, x2, y2, folga=14.0):
        """Linha de eixo traco-ponto, estendida `folga` px além das pontas."""
        dx, dy = x2 - x1, y2 - y1
        c = math.hypot(dx, dy) or 1.0
        ux, uy = dx / c, dy / c
        self.linha(
            x1 - ux * folga, y1 - uy * folga, x2 + ux * folga, y2 + uy * folga,
            cor=EIXO, w=0.9, tracejado="14 4 2 4", opacidade=0.85,
        )

    def marca_corte(self, x: float, y_ini: float, y_fim: float, rotulo: str,
                    sentido: int = 1):
        """Indicacao de corte: linha grossa interrompida + setas + letra."""
        b = 26.0
        for y in (y_ini, y_fim):
            yy = y - b if y == y_ini else y + b
            self.linha(x, y, x, yy, cor=TINTA, w=2.6)
        for y, s in ((y_ini - b, -1), (y_fim + b, 1)):
            # as duas setas apontam para o MESMO lado: é a direção de vista
            self.add(
                f'<path d="M {x:.1f} {y:.1f} l {14 * sentido:.1f} -9 '
                f'l 0 18 z" fill="{TINTA}"/>'
            )
            self.circulo(x, y + s * 26, 13, preenche=FUNDO, cor=TINTA, w=2.0)
            self.texto(x, y + s * 26 + 5, rotulo, 15, TINTA, "middle", negrito=True)
        self.linha(x, y_ini - b, x, y_fim + b, cor=TINTA, w=0.8,
                   tracejado="10 6", opacidade=0.5)

    def cota_h(self, x1, x2, y, texto, chamada_de=None, acima=True):
        """Cota horizontal com linhas de chamada e ticks a 45 graus."""
        for x in (x1, x2):
            if chamada_de is not None:
                y0 = chamada_de
                folga = 6 if y > y0 else -6
                self._cotas.append(
                    f'<line x1="{x:.2f}" y1="{y0 + folga:.2f}" x2="{x:.2f}" '
                    f'y2="{y + (10 if y > y0 else -10):.2f}" stroke="{COTA}" '
                    f'stroke-width="0.7" opacity="0.9"/>'
                )
            self._cotas.append(
                f'<line x1="{x - 5:.2f}" y1="{y + 5:.2f}" x2="{x + 5:.2f}" '
                f'y2="{y - 5:.2f}" stroke="{COTA}" stroke-width="1.3"/>'
            )
        self._cotas.append(
            f'<line x1="{x1:.2f}" y1="{y:.2f}" x2="{x2:.2f}" y2="{y:.2f}" '
            f'stroke="{COTA}" stroke-width="0.9"/>'
        )
        dy = -7 if acima else 17
        self._cotas.append(
            f'<text x="{(x1 + x2) / 2:.2f}" y="{y + dy:.2f}" font-size="15" '
            f'fill="{COTA}" text-anchor="middle" font-family="{FONTE}">'
            f'{esc(texto)}</text>'
        )

    def cota_v(self, y1, y2, x, texto, chamada_de=None, direita=True,
               onde="meio"):
        """Cota vertical com linhas de chamada e ticks a 45 graus."""
        for y in (y1, y2):
            if chamada_de is not None:
                x0 = chamada_de
                folga = 6 if x > x0 else -6
                self._cotas.append(
                    f'<line x1="{x0 + folga:.2f}" y1="{y:.2f}" '
                    f'x2="{x + (10 if x > x0 else -10):.2f}" y2="{y:.2f}" '
                    f'stroke="{COTA}" stroke-width="0.7" opacity="0.9"/>'
                )
            self._cotas.append(
                f'<line x1="{x - 5:.2f}" y1="{y + 5:.2f}" x2="{x + 5:.2f}" '
                f'y2="{y - 5:.2f}" stroke="{COTA}" stroke-width="1.3"/>'
            )
        self._cotas.append(
            f'<line x1="{x:.2f}" y1="{y1:.2f}" x2="{x:.2f}" y2="{y2:.2f}" '
            f'stroke="{COTA}" stroke-width="0.9"/>'
        )
        alto, baixo = min(y1, y2), max(y1, y2)
        ym = (y1 + y2) / 2 if onde == "meio" else \
            alto + min(0.22 * (baixo - alto), 0.5 * largura_texto(texto, 15))
        xt = x + (13 if direita else -13)
        self._cotas.append(
            f'<text x="{xt:.2f}" y="{ym:.2f}" '
            f'font-size="15" fill="{COTA}" text-anchor="middle" '
            f'font-family="{FONTE}" transform="rotate(-90 '
            f'{xt:.2f} {ym:.2f})">{esc(texto)}</text>'
        )

    # -- chamadas de ferro -------------------------------------------------
    def chamada(self, x, y, titulo, descricao, cor=PRINCIPAL, lado="auto"):
        self._chamadas.append(Chamada((x, y), titulo, descricao, cor, lado))

    def largura_rail(self, tamanho: float = 14.5) -> float:
        """Largura que as chamadas exigem de margem lateral."""
        if not self._chamadas:
            return 0.0
        return max(c.largura(tamanho) for c in self._chamadas) + 44

    def _resolver_chamadas(self, tamanho=14.5, altura_linha=40.0) -> None:
        if not self._chamadas:
            return
        meio_x = (self.margem_esq + self.largura - self.margem_dir) / 2

        grupos: dict[str, list[Chamada]] = {"esq": [], "dir": []}
        for c in self._chamadas:
            lado = c.lado
            if lado == "auto":
                lado = "esq" if c.ancora[0] < meio_x else "dir"
            grupos[lado].append(c)

        for lado, itens in grupos.items():
            if not itens:
                continue
            ys = distribuir(
                [c.ancora[1] for c in itens],
                altura_linha,
                self.margem_sup + 12,
                self.altura - self.margem_inf - 12,
            )
            for c, y in zip(itens, ys):
                if lado == "esq":
                    x_texto = self.margem_esq - 26
                    ancora_txt = "end"
                    x_dobra = x_texto + 8
                else:
                    x_texto = self.largura - self.margem_dir + 26
                    ancora_txt = "start"
                    x_dobra = x_texto - 8
                ax, ay = c.ancora
                # sublinha sob o rótulo, depois diagonal única até o ancora
                self.add(
                    f'<path d="M {x_dobra:.1f} {y + 7:.1f} L '
                    f'{(x_dobra * 0.35 + ax * 0.65):.1f} {y + 7:.1f} L '
                    f'{ax:.1f} {ay:.1f}" fill="none" stroke="{COTA}" '
                    f'stroke-width="0.8" opacity="0.8" marker-end="url(#seta)"/>'
                )
                self.circulo(ax, ay, 3.0, preenche=c.cor)
                self.texto(x_texto, y, c.titulo, tamanho, c.cor, ancora_txt,
                           negrito=True)
                self.texto(x_texto, y + 17, c.descricao, tamanho - 1.5, COTA,
                           ancora_txt)

    # -- carimbo -----------------------------------------------------------
    def carimbo(self, titulo: str, linhas: list[str], escala: str = ""):
        y0 = self.altura - self.margem_inf + 34
        self.linha(self.margem_esq * 0.35, y0 - 22,
                   self.largura - self.margem_dir * 0.35, y0 - 22,
                   cor=COTA, w=1.2, opacidade=0.6)
        self.texto(self.margem_esq * 0.35, y0, titulo, 19, TINTA, negrito=True)
        y = y0 + 22
        for ln in linhas:
            self.texto(self.margem_esq * 0.35, y, ln, 14, COTA)
            y += 19
        if escala:
            self.texto(self.largura - self.margem_dir * 0.35, y0, escala, 14,
                       COTA, "end")

    # -- saída -------------------------------------------------------------
    def render(self) -> str:
        self._resolver_chamadas()
        defs = f'''<defs>
<pattern id="hachura" width="9" height="9" patternTransform="rotate(45)"
         patternUnits="userSpaceOnUse">
  <line x1="0" y1="0" x2="0" y2="9" stroke="{HACHURA}" stroke-width="0.85"/>
</pattern>
<pattern id="hachuraApoio" width="6" height="6" patternTransform="rotate(45)"
         patternUnits="userSpaceOnUse">
  <line x1="0" y1="0" x2="0" y2="6" stroke="{APOIO}" stroke-width="1.1"/>
</pattern>
<marker id="seta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7"
        markerHeight="7" orient="auto"><path d="M0 1 L9 5 L0 9 z" fill="{COTA}"/></marker>
<marker id="setaCheia" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8"
        markerHeight="8" orient="auto"><path d="M0 1 L9 5 L0 9 z" fill="{PRINCIPAL}"/></marker>
{''.join(self._defs)}</defs>'''
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.largura:.0f}" '
            f'height="{self.altura:.0f}" viewBox="0 0 {self.largura:.0f} '
            f'{self.altura:.0f}">{defs}'
            f'<rect width="{self.largura:.0f}" height="{self.altura:.0f}" '
            f'fill="{self.fundo}"/>'
            f'{"".join(self._corpo)}{"".join(self._cotas)}</svg>'
        )


# ===========================================================================
@dataclass
class Escala:
    """Converte cm do projeto em px do desenho."""
    x0: float
    y0: float
    k: float
    origem_px: tuple[float, float]

    def px(self, x: float) -> float:
        return self.origem_px[0] + (x - self.x0) * self.k

    def py(self, y: float) -> float:
        return self.origem_px[1] - (y - self.y0) * self.k

    def p(self, x: float, y: float) -> tuple[float, float]:
        return self.px(x), self.py(y)

    @property
    def denominador(self) -> float:
        """1:N considerando 96 px por polegada."""
        return 2.54 / (self.k / 96.0 * 2.54) / 100.0 * 100.0
