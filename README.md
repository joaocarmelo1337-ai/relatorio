# Registro de Campo — Obra de pavimentação asfáltica

Aplicativo web de campo com duas abas, cada uma com o seu relatório em PDF:

- **Esgoto** — registro fotográfico de **hidrômetros** e **ligações de esgoto** que serão
  modificados pela obra, para entrega à concessionária **Águas Guariroba** (Campo Grande/MS).
  Identidade em azul-petróleo.
- **Árvores** — registro fotográfico das **árvores cortadas** por estarem no traçado do
  pavimento ou interferirem na calçada, com a foto da árvore antes do corte e a foto da
  etiqueta de identificação. Identidade em marrom, e o destinatário é você quem
  escreve em "Dados da obra".

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
  vermelho = Danificado, cinza = Já remanejado). Permite editar e excluir.
- **Dados do relatório**: nome da obra, contrato/processo, município, concessionária,
  destinatário do relatório de árvores, empresa executora, CNPJ e logo da empresa. Só a
  obra e a empresa são obrigatórias; o resto aparece no PDF apenas se estiver preenchido.
- **Assinaturas**: até três, todas opcionais — responsável técnico, representante/dono da
  empresa e fiscal da obra, cada uma com nome e CREA/CAU. Entram no fim do PDF apenas as
  preenchidas, lado a lado.
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
