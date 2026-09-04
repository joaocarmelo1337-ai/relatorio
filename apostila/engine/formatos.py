"""Catalogo de formatos alternativos de barra.

Requisito do projeto: toda armadura aparece desenhada e, quando existe mais de
um formato válido, TODOS aparecem, com uma tabela dizendo quando cada um é boa
escolha. Este módulo é a fonte única desse catalogo - o desenho e o texto leem
daqui, ninguem redigita.

`poly` é a barra em coordenadas normalizadas: u de 0 a 1 no comprimento reto,
v positivo para CIMA no desenho - que é o lado para onde o gancho de uma barra
de face inferior dobra (para dentro da laje).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Formato:
    id: str
    nome: str
    poly: tuple[tuple[float, float], ...]
    quando_usar: str
    vantagem: str
    desvantagem: str
    n_ganchos: int


# --- armadura principal ----------------------------------------------------
PRINCIPAL = (
    Formato(
        id="A",
        nome="Ganchos em 90 graus nas duas pontas",
        poly=((0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)),
        quando_usar="Falta comprimento reto para ancorar nos dois apoios.",
        vantagem="Ancora em menos espaço: o gancho reduz lb,nec em 30% (alpha = 0,7).",
        desvantagem="Duas dobras por barra; o gancho tem de caber em h - 2c.",
        n_ganchos=2,
    ),
    Formato(
        id="B",
        nome="Reta, sem gancho",
        poly=((0.0, 0.0), (1.0, 0.0)),
        quando_usar="Há espaço para o lb,nec inteiro, ou a ponta é emenda por traspasse.",
        vantagem="Mais barata: sem custo de dobra e sem risco de gancho fora de esquadro.",
        desvantagem="Exige o comprimento de ancoragem cheio (alpha = 1,0).",
        n_ganchos=0,
    ),
    Formato(
        id="C",
        nome="Levantada (cavalete)",
        poly=((0.0, 0.0), (0.30, 0.0), (0.50, 0.62), (1.0, 0.62)),
        quando_usar="O momento inverte de sinal ao longo do vão.",
        vantagem="A mesma barra atende a tração inferior no vão e a superior no apoio.",
        desvantagem="Dobra em ângulo, mais trabalhosa de posicionar e de conferir em obra.",
        n_ganchos=0,
    ),
    Formato(
        id="D",
        nome="Um gancho só, na ponta do apoio",
        poly=((0.0, 1.0), (0.0, 0.0), (1.0, 0.0)),
        quando_usar="Só uma das pontas chega a um apoio; a outra é emenda por traspasse.",
        vantagem="Ancora onde precisa e evita dobra inutil na ponta emendada.",
        desvantagem="Exige atenção na montagem para não inverter a barra.",
        n_ganchos=1,
    ),
)

# --- armadura de distribuição ----------------------------------------------
DISTRIBUICAO = (
    Formato(
        id="A",
        nome="Reta",
        poly=((0.0, 0.0), (1.0, 0.0)),
        quando_usar="A barra morre dentro da laje, longe de borda livre.",
        vantagem="Mais simples e mais barata de executar.",
        desvantagem="Não ancora nada nas pontas; depende do concreto ao redor.",
        n_ganchos=0,
    ),
    Formato(
        id="B",
        nome="Com ganchos nas pontas",
        poly=((0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)),
        quando_usar="A barra termina perto de borda livre e precisa ancorar em trecho curto.",
        vantagem="Melhor ancoragem junto a bordas livres; segura a malha no lugar.",
        desvantagem="Duas dobras por barra, num aço que nem sempre precisa disso.",
        n_ganchos=2,
    ),
)

# --- armadura de borda ------------------------------------------------------
BORDA = (
    Formato(
        id="A",
        nome="Em L",
        poly=((0.0, 1.0), (0.0, 0.0), (1.0, 0.0)),
        quando_usar="Caso mais comum: há apoio de um lado da borda.",
        vantagem="Gancho no apoio e ponta reta dentro da laje; pouca dobra.",
        desvantagem="Protege só a face onde está; não abraca a borda.",
        n_ganchos=1,
    ),
    Formato(
        id="B",
        nome="Grampo em U",
        poly=((1.0, 1.0), (0.0, 1.0), (0.0, 0.0), (1.0, 0.0)),
        quando_usar="Borda livre com as duas faces expostas (escada em balanço, lateral livre).",
        vantagem="Abraca as duas faces: é o melhor contra fissura de canto.",
        desvantagem="Mais aço e mais amarração; ocupa espaço na borda.",
        n_ganchos=2,
    ),
)

# --- ancoragem do canto reentrante ------------------------------------------
CANTO = (
    Formato(
        id="A",
        nome="Barra principal dobrada + barras de ancoragem no vértice",
        poly=((0.0, 0.0), (1.0, 0.0)),
        quando_usar="Solução padrão quando a principal atravessa o canto dobrando.",
        vantagem="Menos pecas e montagem mais simples.",
        desvantagem="Depende do posicionamento correto das transversais no vértice.",
        n_ganchos=0,
    ),
    Formato(
        id="B",
        nome="Barras cruzadas no vértice (principal interrompida)",
        poly=((0.0, 0.8), (0.0, 0.0), (1.0, 0.0)),
        quando_usar="Canto muito solicitado, ou quando se quer eliminar a resultante na origem.",
        vantagem="Elimina a força de arrancamento na origem, em vez de resisti-la.",
        desvantagem="Mais aço, mais corte e mais amarração.",
        n_ganchos=1,
    ),
)

# --- divisão da barra do lance ----------------------------------------------
LANCE_INTEIRA_OU_DIVIDIDA = (
    Formato(
        id="1",
        nome="Barra inteira",
        poly=((0.0, 0.0), (1.0, 0.0)),
        quando_usar="Patamares curtos e armadura pouco congestionada.",
        vantagem="Menos emendas e nenhum aço gasto em traspasse.",
        desvantagem="Dificil enfiar dentro do patamar; esbarra na forma e nos arranques de pilar.",
        n_ganchos=0,
    ),
    Formato(
        id="2",
        nome="Arranque + barra do lance, unidas por traspasse",
        poly=((0.0, 0.0), (0.58, 0.0), (0.42, 0.22), (1.0, 0.22)),
        quando_usar="O caso mais comum na prática.",
        vantagem="Muito mais fácil de posicionar em obra.",
        desvantagem="Gasta o comprimento extra do traspasse (>= lb,nec).",
        n_ganchos=0,
    ),
)

CATALOGO = {
    "principal": PRINCIPAL,
    "distribuicao": DISTRIBUICAO,
    "borda": BORDA,
    "canto": CANTO,
    "lance": LANCE_INTEIRA_OU_DIVIDIDA,
}
