# Registro de Interferências — Águas Guariroba

Aplicativo web de campo para registro fotográfico de **hidrômetros** e **ligações de
esgoto** que serão modificados por causa de obra de pavimentação asfáltica, com
geração de um relatório PDF único para entrega à concessionária **Águas Guariroba**
(Campo Grande/MS).

## Como usar

1. Baixe o arquivo `index.html` para o celular (ou envie por e-mail/WhatsApp para você mesmo).
2. Abra o arquivo no navegador. Depois de aberto, **funciona totalmente offline** —
   não há nenhuma requisição externa (a biblioteca jsPDF está embutida no próprio arquivo).
3. Toque no botão **+** para cadastrar cada casa.
4. Ao final do levantamento, toque em **Gerar PDF completo**.

Dica: no Android/iOS, use "Adicionar à tela de início" para abrir como um aplicativo.

## O que o aplicativo faz

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
- **PDF**: um único arquivo A4 com título, parágrafo introdutório formal, data de
  emissão, uma seção por rua (em ordem alfabética) com o total de ligações de esgoto
  a modificar, as duas fotos lado a lado por casa e a página final de **Resumo geral**
  com o total por rua e o total geral. A paginação é calculada bloco a bloco, de modo
  que nenhuma casa é cortada ao meio.
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
todos os registros e as fotos) e **Importar backup** (restaura ou mescla a partir do
`.json`) para transferir entre aparelhos ou guardar cópia de segurança.

## Detalhes técnicos

- Arquivo único, autocontido: HTML + CSS + JavaScript puro, sem framework e **sem CDN**.
- jsPDF 2.5.2 (UMD) embutida no próprio arquivo.
- Downloads: além do download automático, o aplicativo sempre exibe um bloco com os
  links **Baixar arquivo** e **Abrir em nova aba** (blob URL), porque o download
  automático pode ser bloqueado pelo navegador.
- Todas as operações de salvar, carregar, importar e gerar PDF têm tratamento de erro
  com mensagem visível e específica na tela.
