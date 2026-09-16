# Controle de Entrega de EPI

Aplicativo web para registrar a entrega de EPI e uniformes aos funcionários, com
banco de dados **SQLite** (dados persistentes de verdade, não `localStorage`) e
geração da **Ficha de Entrega de EPI em PDF** em um clique.

Feito em Python + Flask + SQLite + reportlab, com captura de assinatura no
próprio navegador (canvas, dedo ou mouse) — pensado para uso em campo, no celular.

## Como rodar

```bash
cd epi
pip install -r requirements.txt
python app.py
```

Abra <http://localhost:5000>. O banco é criado sozinho na primeira execução em
`instance/epi.sqlite3`, já com a lista de EPI pré-carregada.

Para usar do celular na mesma rede, o servidor já escuta em `0.0.0.0` —
acesse `http://IP-DO-COMPUTADOR:5000`.

Em produção, use um servidor WSGI e defina uma chave de sessão própria:

```bash
pip install gunicorn
SECRET_KEY="uma-chave-secreta-longa" gunicorn -w 2 -b 0.0.0.0:8000 "app:app"
```

Variáveis de ambiente: `SECRET_KEY`, `EPI_DATABASE` (caminho do arquivo do banco),
`PORT`.

## Telas

| Rota | O que faz |
|---|---|
| `/funcionarios` | Lista de funcionários, com busca por nome, registro, cargo ou setor |
| `/funcionarios/novo`, `/funcionarios/<id>/editar` | Cadastro: nome, nº de registro, cargo, setor, data do “ciente” e assinatura de admissão |
| `/funcionarios/<id>` | Ficha individual: dados + histórico completo de entregas |
| `/funcionarios/<id>/entregas/nova` | Registro de entrega (itens, CA, quantidade, tamanho, assinatura, devolução) |
| `/entregas/<id>/editar` | Edita uma entrega |
| `/entregas/<id>/devolucao` | Registra data e assinatura de devolução |
| `/funcionarios/<id>/pdf` | **Gera o PDF da ficha** |
| `/epis` | Lista mestre de EPI/uniformes (adicionar, editar, ativar/desativar, excluir) |
| `/configuracoes` | Nome da empresa, CNPJ e logo |

## Configuração da empresa

Nada de nome ou logo fixos no código: em **Configurações** você define o nome da
empresa, o CNPJ (opcional) e faz upload da logo. Esses dados ficam no banco
(tabela `empresa`) e são usados no cabeçalho do aplicativo e no cabeçalho do PDF.
Qualquer empresa pode usar a mesma instalação.

## Lista mestre de EPI

Vem pré-carregada com os itens da ficha tradicional, já com o CA padrão quando
existe (calçado de segurança 28513, protetor auricular concha 14235, óculos
34653, luva vaqueta 16059, luva PU 48827, máscara PFF1 38944, capacete 25883,
talabarte 46206) e em branco nos uniformes, que não têm CA.

Cada item guarda **nome**, **CA** (opcional) e a marca de **pede tamanho**, que
faz o campo de tamanho (P/M/G/GG/EXG ou numeração, como 41 no calçado) aparecer
na hora da entrega.

Um EPI que não está na lista pode ser incluído de dois jeitos:

- em **Lista de EPI**, no formulário “Adicionar item à lista”; ou
- direto na entrega, escolhendo **“+ Outro item (digitar agora)”** — com a opção
  *Salvar este item na lista mestre para uso futuro* marcada, ele passa a
  aparecer para as próximas entregas.

## Registro de entrega

Cada entrega guarda a data de início do preenchimento da ficha, a data de entrega e os
materiais (nome, CA, quantidade e tamanho). **Cada material tem a sua própria
assinatura**, como na ficha em papel: o formulário mostra um bloco de assinatura por
item, e ao salvar o aplicativo avisa quais materiais ainda estão sem assinar.

A assinatura é colhida em **tela cheia**: o botão abre uma tela em que o funcionário
assina usando o aparelho inteiro, sobre uma linha de apoio, e o traço é recortado
antes de ser gravado.

Em **Registrar devolução** a tela lista os materiais daquela entrega: você marca o que
está voltando, informa a data e colhe a assinatura de devolução de cada um.

O nome do item é copiado para a entrega no momento do registro: alterar ou
excluir um item da lista mestre depois **não muda o histórico já assinado**.

## PDF

O botão **Gerar PDF** na ficha do funcionário reproduz a ficha tradicional, em
**A4 paisagem**:

- faixa do título **FICHA DE ENTREGA DE EPI** com a logo à esquerda;
- linha com EMPRESA | NOME DO FUNCIONÁRIO | Nº REGISTRO e linha com CNPJ | CARGO | SETOR
  (empresa e logo vêm das configurações — é a única parte que muda de empresa para empresa);
- texto de declaração de responsabilidade (itens A a D), citando a NR-6, item
  6.7.1, e o art. 158 da CLT (Lei 6.514/77);
- campo **“Ciente em ___/___/___”** com a linha e a assinatura de admissão;
- tabela **Data de Entrega | EPI/Uniforme | CA | Qtde | Assinatura | Data de
  Devolução | Assinatura de Devolução**, preenchida com todo o histórico e com as
  assinaturas desenhadas dentro da célula. Os uniformes saem com os tamanhos marcados
  entre parênteses — `CAMISA: P ( ) M ( ) G ( ) GG ( X ) EXG ( )` — e o calçado com a
  numeração, como na ficha em papel.

## Banco de dados

| Tabela | Conteúdo |
|---|---|
| `empresa` | Linha única (id = 1): nome, CNPJ e logo (blob) |
| `funcionarios` | Nome, registro, cargo, setor, data do ciente e assinatura de admissão |
| `epi_master` | Lista mestre: nome, CA, pede tamanho, ativo |
| `entregas` | Ficha de entrega: FK do funcionário, datas e observações (agrupa os materiais entregues na mesma data) |
| `entrega_itens` | Materiais de cada entrega: FK da entrega, FK do EPI, nome, CA, qtde, tamanho, **assinatura de recebimento, data e assinatura de devolução** |
| `assinaturas` | Imagens PNG das assinaturas (blob), referenciadas pelas demais tabelas |

O esquema completo está em `schema.sql`.

## Teste rápido

```bash
python teste_smoke.py
```

Cria um banco temporário, cadastra empresa, funcionário e entregas, confere que cada
material guardou a sua própria assinatura, que o item novo foi para a lista mestre,
registra a devolução material a material e gera o PDF.

Bancos criados antes desta mudança são migrados sozinhos na primeira execução: a
assinatura que valia para a entrega inteira é copiada para cada material.
