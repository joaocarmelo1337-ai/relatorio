# Registro de Campo — Obra de pavimentação asfáltica

Aplicativo web de campo com duas abas, cada uma com o seu relatório em PDF:

- **Esgoto** — registro fotográfico de **hidrômetros** e **ligações de esgoto** que serão
  modificados pela obra, para entrega à concessionária **Águas Guariroba** (Campo Grande/MS).
  Identidade em azul-petróleo.
- **Árvores** — registro fotográfico das **árvores cortadas** por estarem no traçado do
  pavimento ou interferirem na calçada, com a foto da árvore antes do corte e a foto da
  etiqueta de identificação. Identidade em marrom, e o destinatário é você quem
  escreve em "Dados da obra".

- **Mensal** — relatório fotográfico mensal de obra, no formato entregue à Prefeitura:
  A4 **paisagem**, 4 fotos por página com a descrição do serviço em tarja cinza, moldura
  verde, cabeçalho com brasão de quem recebe, logo da empresa, obra, empresa e período,
  e assinaturas no rodapé de todas as páginas. Aqui **não se pede rua nem data** — elas já
  vêm carimbadas na própria foto pelo aplicativo de câmera. Cada foto pode ser posta na
  página que você quiser (seletor no cadastro) e reordenada com as setas na listagem;
  uma página pode ficar com menos de 4 fotos.

- **Ramal** — ramais de água, com a foto do ramal (obrigatória), uma foto complementar
  opcional, a rua e o ajuste de nível (**Rebaixar**, **Elevar** ou **Sem ajuste**).
  Identidade em cinza; no PDF as fichas saem duas por linha.

A cor da tela inteira muda conforme a aba, para não haver dúvida sobre onde se está
cadastrando.

## Como usar

1. Baixe o arquivo `index.html` para o celular (ou envie por e-mail/WhatsApp para você mesmo).
2. Abra o arquivo no navegador. Depois de aberto, **funciona totalmente offline** —
   não há nenhuma requisição externa (a biblioteca jsPDF está embutida no próprio arquivo).
3. Toque em **Dados da obra e da empresa** e preencha o nome da obra, o nome da empresa e a logo
   (uma vez só — fica salvo no aparelho).
4. Escolha a aba (**Esgoto** ou **Árvores**) e toque no botão **+** para cadastrar.
5. Ao final do levantamento, toque em **Gerar PDF** — cada aba gera o seu próprio relatório.

Dica: no Android/iOS, use "Adicionar à tela de início" para abrir como um aplicativo.

## O que o aplicativo faz

- **Abas**: *Esgoto* e *Árvores*, com listas, filtros, contadores e PDFs independentes.
  O backup e os dados da obra são comuns às duas.
- **Cadastro por árvore** (aba Árvores): rua, número/referência (opcional), data, foto da
  árvore antes do corte (obrigatória), foto da etiqueta (obrigatória), número da etiqueta e
  observações. Toda árvore registrada é, por definição, uma árvore cortada.
- **Cadastro por casa**: rua (com autocomplete das ruas já usadas), número/lote
  (opcional), data (preenchida com o dia de hoje), foto do hidrômetro, número do
  hidrômetro, situação do hidrômetro, foto da ligação de esgoto, situação do esgoto
  e observações. São exatamente **2 fotos por casa** — sem foto de fachada.
- **Fotos**: os campos aceitam tanto tirar a foto na hora quanto escolher uma imagem
  já existente na galeria. As fotos são comprimidas automaticamente (redução
  progressiva de qualidade e depois de dimensão) até caberem em ~900 KB, evitando o
  erro de "foto grande demais".
- **Listagem**: registros agrupados por rua, com contagem de casas, filtro por rua e
  badges coloridos por situação (verde = Mantido, laranja = A remanejar,
  vermelho = Danificado, cinza = Já remanejado, roxo = Não localizado,
  azul-ardósia = Não instalado — estas duas só para o hidrômetro). Permite editar e excluir.
- **Dados do relatório**: nome da obra, contrato/processo, município, concessionária,
  destinatário do relatório de árvores, empresa executora, CNPJ e logo da empresa. Só a
  obra e a empresa são obrigatórias; o resto aparece no PDF apenas se estiver preenchido.
- **Mês de referência e brasão do destinatário**: usados pelo relatório mensal — o mês
  vira o período `01/07/2026 - 31/07/2026` no cabeçalho.
- **Assinaturas**: até três, todas opcionais — responsável técnico, representante/dono da
  empresa e fiscal da obra, cada uma com nome e CREA/CAU. Entram no fim do PDF apenas as
  preenchidas, lado a lado.
- **Planilha `.xlsx`**: uma aba por módulo com dados, mais uma aba de resumo por rua —
  escrita pelo próprio app, sem biblioteca externa. Abre no Excel e no Google Planilhas.
  Não leva as fotos.
- **PDF**: um único arquivo A4 estruturado como documento técnico —
  1. **capa** com a logo, a empresa, o quadro de identificação da obra e os quantitativos;
  2. **1. Apresentação** (texto formal citando obra, empresa, município e concessionária);
  3. **2. Classificação adotada** (o que significa cada situação);
  4. **3. Critério de quantificação** (o que entra e o que não entra na contagem);
  5. **4. Registro fotográfico por rua** (4.1, 4.2, …), cada rua com o total de ligações a
     modificar e as duas fotos lado a lado por casa;
  6. **5. Resumo geral**, com o total por rua, o total geral, o quadro por situação
     encontrada e as assinaturas preenchidas.

  Todas as páginas trazem cabeçalho com a logo e o nome da obra e rodapé com a numeração.
  A paginação é calculada bloco a bloco, de modo que nenhuma casa é cortada ao meio.
- **Contagem de ligações a modificar**: considera apenas os registros cuja situação do
  **esgoto** seja *A remanejar* ou *Danificado* (não conta *Mantido* nem *Já remanejado*).

## Interface

- **Lista em sanfona**: a tela mostra os cards das ruas com o nome, o contador e a seta;
  tocar abre a rua e revela os registros, tocar de novo recolhe. Uma rua aberta por vez, e a
  rua que você acabou de usar já fica aberta. Não vale para a aba Mensal, agrupada por página.
- **Exportações**: dois cards com ícone — **PDF** (relatório formal) e **Planilha Excel**
  (dados para conferência). Exportar/Importar backup ficam como ações secundárias.
- **Descrições reutilizáveis**: no cadastro, chips acima do campo preenchem a descrição com
  um toque. Vêm de uma lista padrão de serviços (aba Mensal) e do que você já escreveu antes.
  O botão *Gerenciar* apaga o que não serve mais.
- **Indicador de salvamento** no cabeçalho: *Salvo no aparelho* / *Salvando…* / *Não gravado*.
  Tocar nele explica onde os dados estão. Não há sincronização com servidor — por isso o
  indicador fala em aparelho, e não em nuvem.

## Armazenamento

Os dados ficam **no próprio navegador do aparelho**. Ao abrir, o aplicativo faz um
teste real de gravação e leitura e mostra no topo qual modo está ativo:

| Modo | Faixa | Significado |
| --- | --- | --- |
| IndexedDB | verde | Armazenamento permanente (situação normal). |
| localStorage | laranja | Alternativa com espaço limitado (~5 MB). |
| Somente memória | vermelha | Nada é gravado; os dados se perdem ao fechar a página. |

Como os dados ficam presos ao aparelho, use **Exportar backup** (gera um `.json` com
todos os registros, as fotos e os dados da obra, inclusive a logo) e **Importar backup**
(restaura ou mescla a partir do `.json`) para transferir entre aparelhos ou guardar cópia
de segurança.

## Detalhes técnicos

- Arquivo único, autocontido: HTML + CSS + JavaScript puro, sem framework e **sem CDN**.
- jsPDF 2.5.2 (UMD) embutida no próprio arquivo.
- Downloads: além do download automático, o aplicativo sempre exibe um bloco com os
  links **Baixar arquivo** e **Abrir em nova aba** (blob URL), porque o download
  automático pode ser bloqueado pelo navegador.
- Todas as operações de salvar, carregar, importar e gerar PDF têm tratamento de erro
  com mensagem visível e específica na tela.

---

## Controle de Entrega de EPI

Além do registro de campo acima, este repositório traz o **controle de entrega de EPI e
uniformes**: cadastro de funcionários, lista de EPI com CA, registro de entregas com a
assinatura colhida na tela, controle de devolução e a **Ficha de Entrega de EPI em PDF**.

Ele existe em duas versões, com o mesmo layout de ficha e a mesma lógica:

### 1. `epi.html` — versão de campo (é a que se usa no dia a dia)

Arquivo único, igual ao `index.html`: abre no celular, **funciona offline** e grava tudo
no próprio aparelho. Sem servidor, sem senha, sem mensalidade.

1. Baixe o `epi.html` para o celular (ou envie por e-mail/WhatsApp para você mesmo).
2. Abra o arquivo no navegador e use "Adicionar à tela de início" para virar ícone.
3. Em **Configurações**, informe o nome da empresa e envie a logo — eles vão para o
   cabeçalho da ficha em PDF. Nada de nome fixo no código.
4. Cadastre o funcionário, toque em **+ Nova entrega**, marque os itens, colha a
   assinatura com o dedo e salve. Depois, **Gerar PDF** monta a ficha completa.

**Os dados ficam só neste aparelho.** Não existe cópia em servidor: a única cópia fora do
celular é o arquivo que sai em **Configurações → Exportar backup** (um `.json` com
funcionários, entregas, assinaturas, lista de EPI e a logo). Guarde-o no Drive ou mande
para você mesmo. Para trocar de aparelho, ou para voltar depois de um acidente, use
**Importar backup**. O aplicativo avisa quando faz mais de 7 dias que você não exporta.

### 2. `epi/` — versão com servidor (Flask + SQLite)

Mesma ficha, mas com banco central: várias pessoas registram, os dados não somem se o
celular sumir e o PDF pode ser gerado do escritório. Precisa de hospedagem e de internet.
É o caminho para quando a empresa adotar o controle.

```bash
cd epi
pip install -r requirements.txt
python app.py     # http://localhost:5000
```

As instruções completas estão em [`epi/README.md`](epi/README.md).

### O que as duas versões fazem

- **Empresa configurável**: nome, CNPJ e logo definidos na interface, usados no cabeçalho
  do aplicativo e do PDF.
- **Funcionários**: nome, nº de registro, cargo, setor, data do “ciente” e assinatura de
  admissão.
- **Lista de EPI** já carregada com os itens da ficha em papel e os CAs padrão (calçado
  28513, concha 14235, óculos 34653, vaqueta 16059, PU 48827, PFF1 38944, capacete 25883,
  talabarte 46206); uniforme fica sem CA. Cada item marca se pede tamanho (P/M/G/GG/EXG ou
  numeração, como 41 no calçado).
- **Item fora da lista** pode ser criado na tela da lista ou na hora da entrega, com a
  opção de guardá-lo para as próximas fichas.
- **Entrega**: data de início da ficha, data de entrega, itens com CA/quantidade/tamanho,
  assinatura no canvas e devolução (data + assinatura) que pode ficar em branco e ser
  preenchida depois.
- **PDF** reproduzindo a ficha tradicional: cabeçalho com logo e empresa, dados do
  funcionário, declaração de responsabilidade (NR-6 item 6.7.1 e art. 158 da CLT), campo
  “Ciente em ___/___/___” e a tabela Data de Entrega | EPI/Uniforme | CA | Qtde |
  Assinatura | Data de Devolução | Ass. Devolução, com as assinaturas desenhadas dentro
  das células e o cabeçalho repetido a cada página.
- O nome do item é copiado para a entrega no momento do registro: mexer na lista de EPI
  depois **não altera o histórico já assinado**.
