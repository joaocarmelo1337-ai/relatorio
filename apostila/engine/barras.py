"""Posições de armadura: extensão, comprimento de corte, quantidade e formato.

Duas regras do projeto valem aqui e são verificadas em teste:
  1. TODA posição carrega `descrição` - o código N1 nunca viaja sozinho.
  2. TODA posição aponta para um catalogo de formatos alternativos
     (engine/formatos.py), com o motivo de escolha de cada um.

Esquema de corte adotado para a armadura positiva (documentado, não herdado):
o aço de face inferior cobre o vão inteiro e é cortado em três barras, com as
emendas nas duas quebras do intradorso - longe do momento máximo, que fica no
meio do lance. Cada emenda vale lb,nec para cada lado.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import formatos as fmt
from .ancoragem import Ancoragem
from .geometria import Geometria, comprimento
from .normas import Normas


@dataclass(frozen=True)
class Posicao:
    codigo: str                 # "N1"
    descricao: str              # "principal do patamar inferior, face inferior"
    bitola_mm: float
    quantidade: int
    espacamento_cm: float | None
    trecho_reto_cm: float
    ganchos_cm: tuple[float, ...]
    face: str                   # "inferior" | "superior"
    direcao: str                # "longitudinal" | "transversal"
    familia: str                # chave do CATALOGO de formatos
    formato_adotado: str        # id dentro da familia
    # extensão no corte longitudinal, em abscissa da seção (cm)
    x_ini: float | None = None
    x_fim: float | None = None
    offset_cm: float | None = None   # distância do intradorso ao eixo da barra
    # Poligonal da barra em coordenadas do projeto (cm), ganchos inclusos.
    # Só as longitudinais têm: são as que aparecem no corte. O desenho apenas
    # projeta estes pontos - ele não recalcula traçado nenhum.
    vertices: tuple[tuple[float, float], ...] = ()
    nota: str = ""

    @property
    def comprimento_cm(self) -> float:
        return self.trecho_reto_cm + sum(self.ganchos_cm)

    @property
    def rotulo(self) -> str:
        """Nunca só o código: é esta string que vai para desenho e tabela."""
        return f"{self.codigo} - {self.descricao}"

    @property
    def chamada(self) -> str:
        """Texto da chamada de ferro na prancha."""
        esp = f" c/ {_num(self.espacamento_cm)}" if self.espacamento_cm else ""
        return (
            f"{self.codigo} - {self.quantidade} Ø{_num(self.bitola_mm)}{esp} - "
            f"C={_num(self.comprimento_cm)} - {self.descricao}"
        )

    @property
    def formatos_alternativos(self) -> tuple[fmt.Formato, ...]:
        return fmt.CATALOGO[self.familia]

    @property
    def comprimento_total_m(self) -> float:
        return self.quantidade * self.comprimento_cm / 100.0


def num_cm(v: float) -> str:
    """Número curto para mensagens de aviso."""
    return f"{v:.0f}".replace(".", ",")


def _num(v: float) -> str:
    return f"{v:.1f}".replace(".0", "").replace(".", ",") if v else "0"


def _n_barras(largura: float, cobrimento: float, espacamento: float) -> int:
    """Barras cabendo numa faixa, com barra em cada extremidade.

    n = ceil(largura_util / espaçamento) + 1, com largura_util = b - 2c.
    O arredondamento é para cima porque o espaçamento é um MÁXIMO.
    """
    util = largura - 2 * cobrimento
    return int(math.ceil(util / espacamento)) + 1


def _dev(geo: Geometria, xa: float, xb: float) -> float:
    """Comprimento desenvolvido do intradorso entre duas abscissas."""
    pontos = sorted({xa, xb} | {k for k in (geo.xk1, geo.xk2) if xa < k < xb})
    total = 0.0
    for p, q in zip(pontos, pontos[1:]):
        dy = geo.intradorso(q) - geo.intradorso(p)
        total += math.hypot(q - p, dy)
    return total


def abscissas_espacadas(
    geo: Geometria, x_ini: float, x_fim: float, espacamento: float
) -> list[float]:
    """Abscissas das barras transversais, espaçadas sobre o intradorso.

    O espaçamento é medido no comprimento DESENVOLVIDO (a barra segue a laje
    inclinada), não na projeção em planta. É está lista que o desenho usa e
    é o seu tamanho que vira a quantidade no quadro de ferro - por construção
    não há como o desenho e a tabela discordarem.
    """
    total = _dev(geo, x_ini, x_fim)
    n = int(math.ceil(total / espacamento)) + 1
    passo = total / (n - 1) if n > 1 else 0.0
    return [_avancar(geo, x_ini, i * passo, +1) for i in range(n)]


def _avancar(geo: Geometria, x0: float, desenvolvido: float, sentido: int) -> float:
    """Abscissa alcancada ao percorrer `desenvolvido` cm sobre o intradorso."""
    x, restante = x0, desenvolvido
    passo = 0.05 * sentido
    while restante > 0:
        prox = x + passo
        if not (geo.x0 <= prox <= geo.x3):
            return max(geo.x0, min(geo.x3, prox))
        restante -= math.hypot(passo, geo.intradorso(prox) - geo.intradorso(x))
        x = prox
    return x


def _gancho_no_ponto(pts, ponta: str, comprimento: float, sentido: int,
                     phi: float):
    """Gancho perpendicular à barra na ponta indicada.

    `sentido` é declarado por quem chama, +1 para cima e -1 para baixo: numa
    barra de face inferior o gancho sobe, numa de face superior ele desce.
    Inferir isso da geometria local dá errado justamente onde importa - dentro
    do bloco do último degrau, onde a barra do patamar termina.

    O comprimento agendado é h - 2c (a folga livre entre cobrimentos, que é o
    que a Seção 8 explica). No traçado ele é medido no eixo da barra, então
    desconta-se phi para o gancho não furar o cobrimento no desenho.
    """
    if comprimento <= 0:
        return list(pts)
    (x, y) = pts[0] if ponta == "inicio" else pts[-1]
    L = max(0.0, comprimento - phi)
    ponto = (x, y + sentido * L)
    return [ponto] + list(pts) if ponta == "inicio" else list(pts) + [ponto]


def _emergir_na_face_superior(geo: Geometria, off: float, lb: float):
    """Traçado da N2 atravessando o canto reentrante superior.

    A barra NÃO dobra sobre a face tracionada: segue reta na direção do lance
    até emergir junto à face superior do patamar, e só ali muda de direção -
    numa dobra cujo lado côncavo é a massa de concreto, não o cobrimento.

    Devolve None quando o patamar superior é curto demais para caber a
    travessia mais o lb,nec de ancoragem; aí o detalhe cruzado não tem onde
    existir e o motor cai no de barra contínua, avisando.
    """
    y_topo = geo.subida - off
    reta = geo.paralela_ao_intradorso(geo.xk2 - 20.0, geo.xk2, off)
    px, py = reta[-1]
    subir = y_topo - py
    if subir <= 0:
        return None
    emerge = (px + subir / math.tan(geo.alpha_rad), y_topo)
    fim = (emerge[0] + lb, y_topo)
    if fim[0] > geo.x3 - geo.c:
        return None
    return emerge, fim


@dataclass(frozen=True)
class Detalhamento:
    posicoes: tuple[Posicao, ...]
    gancho_cm: float
    gancho_normativo_cm: float
    gancho_cabe: bool
    emendas_x: tuple[float, ...]
    emenda_longe_do_maximo: bool
    x_momento_maximo: float
    xs_distribuicao: tuple[float, ...] = ()
    xs_borda: tuple[float, ...] = ()
    xs_principal: tuple[float, ...] = ()
    detalhe_canto: str = "cruzadas"
    penetracao_n3_cm: float = 0.0
    avisos: tuple[str, ...] = ()

    def por_codigo(self, codigo: str) -> Posicao:
        for p in self.posicoes:
            if p.codigo == codigo:
                return p
        raise KeyError(codigo)

    @property
    def resumo_por_bitola(self) -> dict[float, float]:
        out: dict[float, float] = {}
        for p in self.posicoes:
            out[p.bitola_mm] = out.get(p.bitola_mm, 0.0) + p.comprimento_total_m
        return out


def montar(
    cfg: dict,
    geo: Geometria,
    normas: Normas,
    anc_principal: Ancoragem,
    anc_gancho: Ancoragem,
    x_momento_maximo_cm: float,
) -> Detalhamento:
    arm = cfg["armaduras"]
    det = cfg["detalhamento"]
    c = geo.c
    phi_p = arm["principal"]["bitola_mm"] / 10.0
    phi_d = arm["distribuicao"]["bitola_mm"] / 10.0
    phi_b = arm["borda"]["bitola_mm"] / 10.0
    phi_c = arm["ancoragem_canto"]["bitola_mm"] / 10.0

    # Gancho: limite geométrico (cabe na espessura) x mínimo normativo.
    gancho = geo.h - 2 * c
    gancho_norm = normas.ponta_reta_gancho(
        arm["principal"]["tipo_gancho"], arm["principal"]["bitola_mm"]
    )
    avisos: list[str] = []
    if gancho < gancho_norm:
        avisos.append(
            f"O gancho cabe em h - 2c = {gancho:.1f} cm, mas o mínimo normativo "
            f"para {arm['principal']['tipo_gancho']} em Ø"
            f"{arm['principal']['bitola_mm']:g} é {gancho_norm:.1f} cm. "
            f"Aumente h, reduza a bitola ou use gancho semicircular (2ø)."
        )

    lb_nec = anc_gancho.lb_nec if arm["principal"]["ancoragem"] == "com_gancho" else anc_principal.lb_nec

    # ---- extensoes da armadura positiva --------------------------------
    x_ini_total, x_fim_total = c, geo.x3 - c
    x_emenda_1 = geo.xk1
    x_emenda_2 = geo.xk2
    n1_fim = _avancar(geo, x_emenda_1, lb_nec, +1)
    n2_ini = _avancar(geo, x_emenda_1, lb_nec, -1)
    n2_fim = _avancar(geo, x_emenda_2, lb_nec, +1)
    n3_ini = _avancar(geo, x_emenda_2, lb_nec, -1)

    off_p = c + phi_p / 2.0
    off_d = c + phi_p + phi_d / 2.0
    off_sup = geo.h - c - phi_c / 2.0

    n_princ = _n_barras(geo.largura, c, arm["principal"]["espacamento_cm"])
    dev_total = _dev(geo, x_ini_total, x_fim_total)
    xs_dist = abscissas_espacadas(
        geo, x_ini_total, x_fim_total, arm["distribuicao"]["espacamento_cm"]
    )
    xs_borda = abscissas_espacadas(
        geo, x_ini_total, x_fim_total, arm["borda"]["espacamento_cm"]
    )
    largura_util = geo.largura - 2 * c

    # ---- traçado das barras longitudinais ------------------------------
    # N1 dobra na quebra INFERIOR: ali o lado côncavo da dobra é a massa de
    # concreto, então a resultante aperta a barra contra a laje. É a quebra
    # segura, e a barra pode acompanhá-la.
    reto_n1 = geo.paralela_ao_intradorso(x_ini_total, n1_fim, off_p)
    v_n1 = _gancho_no_ponto(reto_n1, "inicio", gancho, +1, phi_p)

    # Na quebra SUPERIOR nenhuma barra tracionada muda de direção sobre a face
    # de tração. As duas viram para CIMA, para longe do cobrimento, e se
    # cruzam no vértice.
    trav = _emergir_na_face_superior(geo, off_p, lb_nec)
    y_patamar = geo.intradorso(geo.x3) + off_p
    # Até onde a N3 avança lance adentro sem sair pelo espelho do último degrau
    penetracao = geo.penetracao_horizontal(y_patamar, geo.xk2, c + phi_p / 2)
    n3_ini_real = geo.xk2 - penetracao

    if trav is not None:
        emerge, fim_topo = trav
        reto_n2 = list(geo.paralela_ao_intradorso(n2_ini, geo.xk2, off_p))
        reto_n2 += [emerge, fim_topo]
        # ponta apoiada na face SUPERIOR do patamar: o gancho desce
        v_n2 = _gancho_no_ponto(reto_n2, "fim", gancho, -1, phi_p)
        n2_fim_real, fmt_n2, ganchos_n2 = fim_topo[0], "E", (gancho,)
        detalhe_canto = "cruzadas"
    else:
        reto_n2 = list(geo.paralela_ao_intradorso(n2_ini, n2_fim, off_p))
        v_n2 = reto_n2
        n2_fim_real, fmt_n2, ganchos_n2 = n2_fim, "B", ()
        detalhe_canto = "continua"
        avisos.append(
            f"O patamar superior ({num_cm(geo.patamar_sup)} cm) é curto demais "
            f"para a N2 atravessar o canto e ainda ancorar {num_cm(lb_nec)} cm "
            f"na face superior. O canto voltou ao detalhe de barra contínua, "
            f"que depende inteiramente da costura transversal no vértice."
        )

    reto_n3 = [(n3_ini_real, y_patamar), (x_fim_total, y_patamar)]
    v_n3 = _gancho_no_ponto(reto_n3, "inicio", gancho, +1, phi_p)
    v_n3 = _gancho_no_ponto(v_n3, "fim", gancho, +1, phi_p)

    if detalhe_canto == "cruzadas" and penetracao < lb_nec:
        avisos.append(
            f"A N3 só entra {num_cm(penetracao)} cm lance adentro antes de sair "
            f"pelo espelho do último degrau, contra os {num_cm(lb_nec)} cm de "
            f"lb,nec. O gancho e a N2, que passa pelo vértice, cobrem a "
            f"diferença; um piso maior no último degrau resolveria de vez."
        )

    pos: list[Posicao] = [
        Posicao(
            codigo="N1",
            descricao="principal do patamar inferior, face inferior",
            bitola_mm=arm["principal"]["bitola_mm"],
            quantidade=n_princ,
            espacamento_cm=arm["principal"]["espacamento_cm"],
            trecho_reto_cm=comprimento(reto_n1),
            ganchos_cm=(gancho,),
            face="inferior",
            direcao="longitudinal",
            familia="principal",
            formato_adotado="D",
            x_ini=x_ini_total,
            x_fim=n1_fim,
            offset_cm=off_p,
            vertices=tuple(v_n1),
            nota="Gancho no apoio inferior; a outra ponta emenda com a N2 por "
                 "traspasse. A dobra na quebra inferior é segura: a resultante "
                 "aperta a barra contra a massa de concreto.",
        ),
        Posicao(
            codigo="N2",
            descricao="principal do lance, face inferior",
            bitola_mm=arm["principal"]["bitola_mm"],
            quantidade=n_princ,
            espacamento_cm=arm["principal"]["espacamento_cm"],
            trecho_reto_cm=comprimento(reto_n2),
            ganchos_cm=ganchos_n2,
            face="inferior",
            direcao="longitudinal",
            familia="principal",
            formato_adotado=fmt_n2,
            x_ini=n2_ini,
            x_fim=n2_fim_real,
            offset_cm=off_p,
            vertices=tuple(v_n2),
            nota="Atravessa o canto reentrante superior sem dobrar sobre a face "
                 "tracionada: segue reta até emergir na face superior do patamar "
                 "e ancora ali, cruzando com a N3.",
        ),
        Posicao(
            codigo="N3",
            descricao="principal do patamar superior, face inferior",
            bitola_mm=arm["principal"]["bitola_mm"],
            quantidade=n_princ,
            espacamento_cm=arm["principal"]["espacamento_cm"],
            trecho_reto_cm=comprimento(reto_n3),
            ganchos_cm=(gancho, gancho),
            face="inferior",
            direcao="longitudinal",
            familia="principal",
            formato_adotado="A",
            x_ini=n3_ini_real,
            x_fim=x_fim_total,
            offset_cm=off_p,
            vertices=tuple(v_n3),
            nota="Entra reta no lance e termina em gancho para CIMA, longe do "
                 "cobrimento. É a outra metade do cruzamento com a N2.",
        ),
        Posicao(
            codigo="N4",
            descricao="distribuição, face inferior, ao longo de todo o percurso",
            bitola_mm=arm["distribuicao"]["bitola_mm"],
            quantidade=len(xs_dist),
            espacamento_cm=arm["distribuicao"]["espacamento_cm"],
            trecho_reto_cm=largura_util,
            ganchos_cm=(),
            face="inferior",
            direcao="transversal",
            familia="distribuicao",
            formato_adotado="A",
            x_ini=x_ini_total,
            x_fim=x_fim_total,
            offset_cm=off_d,
            nota="Fica POR CIMA da principal: quem precisa ficar longe da linha neutra é a principal.",
        ),
    ]

    if det["reforco_divisa"]["incluir"]:
        pos.append(
            Posicao(
                codigo="N5",
                descricao="reforço na divisa patamar/lance, face inferior",
                bitola_mm=det["reforco_divisa"]["bitola_mm"],
                quantidade=int(det["reforco_divisa"]["quantidade"]),
                espacamento_cm=None,
                trecho_reto_cm=largura_util,
                ganchos_cm=(),
                face="inferior",
                direcao="transversal",
                familia="distribuicao",
                formato_adotado="A",
                x_ini=geo.x1,
                x_fim=geo.x1,
                offset_cm=off_p,
                nota="Barra única sobre a quebra do intradorso, onde a geometria muda.",
            )
        )

    n_por_canto = int(arm["ancoragem_canto"]["barras_por_canto"])
    pos.append(
        Posicao(
            codigo="N6",
            descricao="ancoragem dos cantos reentrantes, junto a face superior",
            bitola_mm=arm["ancoragem_canto"]["bitola_mm"],
            quantidade=n_por_canto * 2,
            espacamento_cm=None,
            trecho_reto_cm=largura_util,
            ganchos_cm=(),
            face="superior",
            direcao="transversal",
            familia="distribuicao",
            formato_adotado="A",
            x_ini=geo.xk1,
            x_fim=geo.xk2,
            offset_cm=off_sup,
            nota=f"{n_por_canto} barras em cada um dos 2 cantos reentrantes "
                 f"(encontro do lance com cada patamar).",
        )
    )

    ext_borda = normas["armadura_borda"]["extensao_fracao_vao_menor"] * min(
        geo.largura, geo.x3
    )
    perna_borda = max(ext_borda, anc_gancho.lb_nec)
    pos.append(
        Posicao(
            codigo="N7",
            descricao="borda, ao longo das duas laterais livres",
            bitola_mm=arm["borda"]["bitola_mm"],
            quantidade=2 * len(xs_borda),
            espacamento_cm=arm["borda"]["espacamento_cm"],
            trecho_reto_cm=perna_borda,
            ganchos_cm=(gancho,),
            face="superior",
            direcao="transversal",
            familia="borda",
            formato_adotado="A",
            x_ini=x_ini_total,
            x_fim=x_fim_total,
            offset_cm=off_sup,
            nota=f"Perna de {perna_borda:.0f} cm = maior entre 0,15 do vão menor "
                 f"({ext_borda:.0f} cm) e lb,nec ({anc_gancho.lb_nec:.0f} cm).",
        )
    )

    constr = arm["ancoragem_canto"].get("construtiva", {})
    if constr.get("incluir"):
        phi_k = constr["bitola_mm"] / 10.0
        pos.append(
            Posicao(
                codigo="N8",
                descricao="barra construtiva no vértice dos cantos reentrantes",
                bitola_mm=constr["bitola_mm"],
                quantidade=int(constr["por_canto"]) * 2,
                espacamento_cm=None,
                trecho_reto_cm=largura_util,
                ganchos_cm=(),
                face="superior",
                direcao="transversal",
                familia="distribuicao",
                formato_adotado="A",
                x_ini=geo.xk1,
                x_fim=geo.xk2,
                offset_cm=geo.h - c - phi_k / 2.0,
                nota="Não entra no cálculo: é apoio de montagem para a malha e "
                     "para amarrar o cruzamento das principais no vértice.",
            )
        )

    emendas = (x_emenda_1, x_emenda_2)
    folga = min(abs(e - x_momento_maximo_cm) for e in emendas)
    longe = folga >= lb_nec
    if not longe:
        avisos.append(
            f"As emendas por traspasse caem a {folga:.0f} cm do momento máximo "
            f"(x = {x_momento_maximo_cm:.0f} cm). Leve-as para região de esforço menor."
        )

    passo_p = arm["principal"]["espacamento_cm"]
    util_p = geo.largura - 2 * c
    xs_princ = [c + i * util_p / (n_princ - 1) for i in range(n_princ)] if n_princ > 1 else [c]

    return Detalhamento(
        posicoes=tuple(pos),
        xs_distribuicao=tuple(xs_dist),
        xs_borda=tuple(xs_borda),
        xs_principal=tuple(xs_princ),
        detalhe_canto=detalhe_canto,
        penetracao_n3_cm=penetracao,
        gancho_cm=gancho,
        gancho_normativo_cm=gancho_norm,
        gancho_cabe=gancho >= gancho_norm,
        emendas_x=emendas,
        emenda_longe_do_maximo=longe,
        x_momento_maximo=x_momento_maximo_cm,
        avisos=tuple(avisos),
    )
