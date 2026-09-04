# Apostila de cálculo e detalhamento da armadura de escadas

Gerador paramétrico da apostila: você edita **um** arquivo de configuração e
todas as figuras e todos os números do texto se atualizam sozinhos.

```
make                                        # apostila do exemplo padrão
make CONFIG=config/exemplo_escola.yaml      # apostila de outro exemplo
make teste                                  # testes do motor de cálculo
```

`config/exemplo_escola.yaml` existe para provar o ponto: outra escada (11
degraus de 30 × 17, patamares desiguais, C30, laje de 15 cm, cobrimento 3 cm,
carga de escola), zero linha de código alterada, e as 14 figuras se redesenham
com as chamadas de ferro reposicionadas sozinhas.

Saída em `out/`: `Apostila_Armadura_Escadas.docx`, o `.pdf` correspondente,
o Markdown intermediário e as 14 figuras em SVG (editável) e PNG.

## Como está organizado

```
config/
  exemplo_padrao.yaml   O ÚNICO arquivo que você edita: geometria, materiais,
                        ações, armaduras adotadas.
  normas.yaml           Constantes e tabelas normativas. Cada bloco traz o
                        campo `fonte`. O que não consta nas fontes está
                        marcado PENDENTE e o motor RECUSA usar.

engine/                 Motor de cálculo. Não desenha e não escreve texto.
  normas.py             Acesso ao normas.yaml, com as guardas de PENDENTE.
  geometria.py          Blondel, inclinação, h1/hm, contorno real da peça.
  cargas.py             Ações permanentes e variáveis por trecho.
  esforcos.py           Viga biapoiada com carga uniforme por trechos;
                        M(x) e V(x) analíticos.
  flexao.py             Linha neutra, Kx, domínios, As. λ e αc variáveis.
  ancoragem.py          fctd, fbd, lb, lb,nec, lb,min.
  formatos.py           Catálogo de formatos alternativos de barra.
  barras.py             Posições N1..N7: extensão, corte, quantidade.
  api.py                calcular(config) -> Resultado com tudo.

desenho/                Desenho técnico em SVG. Lê o Resultado, não recalcula.
  prancha.py            Biblioteca de prancha: hachura, cotas com linha de
                        chamada, linhas de eixo, marca de corte, carimbo e o
                        posicionador automático de chamadas de ferro.
  base.py               Offset perpendicular ao intradorso (cobrimento real
                        numa laje inclinada), caminho das barras.
  corte.py              Corte longitudinal A-A' com toda a armadura.
  plantas.py            Plantas separadas: face inferior e face superior.
  diagramas.py          Carregamento, cortante e momento fletor.
  deformacoes.py        Seção, linha neutra, deformações e domínios.
  formatos.py           Quadro de formatos e as alternativas de cada família.
  detalhes.py           Geometria do degrau, canto reentrante, N2 dividida.
  render.py             Gera todas as figuras e devolve o manifesto.

doc/
  apostila.md.j2        O CONTEÚDO: prosa em Markdown, números por interpolação.
  referencia.docx       A APRESENTAÇÃO do .docx (fontes, cores, A4, margens).
  gerar_referencia.py   Regenera a referência acima.
  impressao.css         A apresentação do PDF de reserva (WeasyPrint).

tests/                  63 testes em pytest.
build.py                Orquestra: motor -> figuras -> Markdown -> docx -> pdf.
_legado/                Os scripts originais, guardados para comparação.
```

## Dependências

```
pip install -r requirements.txt
apt install pandoc libreoffice-writer
```

`pandoc` é obrigatório. `libreoffice-writer` gera o PDF a partir do `.docx`
(saída idêntica); sem ele o build cai no WeasyPrint, que produz o mesmo
conteúdo com layout próprio.

## Regra do arquivo de normas

`config/normas.yaml` não contém nenhum valor inventado. Cada bloco declara sua
origem:

- **`fonte: "arquivos originais"`** — o valor veio dos scripts originais.
- **`fonte: "derivado"`** — fórmula ajustada aos pontos tabelados dos arquivos
  originais, com teste provando que ela reproduz cada linha da tabela.
- **`valor: PENDENTE`** — não consta nas fontes. O motor levanta
  `DadoNormativoAusente` com a mensagem dizendo o que preencher e onde.
  **Ele nunca interpola nem estima um PENDENTE.**

Hoje estão pendentes: ρ~min~ para C35 e C45, o módulo E~s~ do aço e a tabela
de massa linear das barras (kg/m).

A expressão de ε~cu~ para fck > 50 MPa já está preenchida:
`2,6 + 35·((90 − fck)/100)⁴ ‰`. Ela foi aceita porque emenda com o dado que já
existia: em fck = 50 MPa a fórmula dá 3,496‰, ou seja, o mesmo 3,5‰ do ramo
de baixo, arredondado. Há teste para essa continuidade.

## Faixa de fck coberta

`faixa_fck_MPa` em `config/normas.yaml` declara o escopo do projeto: **C20 a
C60**. Fora dela o motor recusa com mensagem dizendo o que ampliar. É escolha
de escopo, não limite normativo — concreto acima de C60 não aparece nos
exemplos que esta apostila atende.

Dentro da faixa, ρ~min~ está tabelado para C20–C30, C40, C50, C55 e C60.
C55 e C60 vieram de fonte secundária e estão marcados como tal no YAML: batem
com a razão ρ~min~/f~ctm~ dos pontos dos arquivos originais dentro de 1,7 %,
mas convém conferir na Tabela 17.3 quando você tiver o PDF à mão.

## O que o motor verifica sozinho

Além de calcular, ele recusa ou avisa:

| Situação | O que acontece |
|---|---|
| fck fora de C20–C60 | erro, dizendo o que ampliar no normas.yaml |
| fck sem ρ~min~ tabelado (C35, C45) | erro, com o nome da linha a preencher |
| Armadura adotada não cobre a calculada | erro, dizendo quanto falta |
| Md acima do limite da seção | erro, sugerindo aumentar h ou fck |
| Blondel fora de 60–64 cm | aviso no documento |
| Gancho h−2c menor que o mínimo normativo | aviso no documento |
| Kx acima do limite de ductilidade | aviso no documento |
| Emenda perto do momento máximo | aviso no documento |
| Espaçamento da secundária acima de 33 cm | aviso no documento |

Os avisos aparecem na Seção 11 da apostila gerada.

## Espaçamento automático

Em `armaduras.*.espacamento_cm` você pode escrever `auto` no lugar do número:
o motor escolhe o maior espaçamento (múltiplo de 0,5 cm) que ainda cobre a área
necessária. Útil para gerar a apostila de outra geometria sem ter de
redimensionar a ferragem na mão.
