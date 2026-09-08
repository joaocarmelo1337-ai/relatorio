# JOÃO CARMELO — TCC

**Sistema de Vistoria, Garantias e Manutenção de Residências**

> Vistoriar antes para não descobrir depois.

Apoio à vistoria técnica de residências, com foco em imóveis de até 3 anos
contados do Habite-se: registro de manifestações patológicas, ambientes,
fotografias, classificação GUT, situação das garantias e histórico de manutenção.

Acadêmico: João Carmelo · Curso: Engenharia Civil · Instituição: UFMS ·
Orientador: Sidiclei Formangini · Ano: 2026.

---

## Arquitetura em duas metades

A vistoria acontece dentro de casa, muitas vezes sem sinal. Streamlit é um
servidor — não abre no celular sem rede. Por isso o sistema é dividido:

| | Onde roda | Para quê |
|---|---|---|
| **App de campo** | Arquivo HTML único no celular, **offline** | Capturar ambiente, item, conforme/não conforme, foto e GUT |
| **Plataforma** | Streamlit no notebook | Banco, dashboard, garantias, Gantt, dados do TCC, relatórios |

As duas conversam por um **pacote de vistoria** (um `.zip`) — ver abaixo.
Nenhuma das duas depende de internet.

### O pacote de vistoria (troca de fotos e dados)

O celular exporta **um zip por vistoria**:

```
vistoria_casa-silva_2026-09-08.zip
├── manifesto.json        residência, vistoria, ambientes, ocorrências, fotos
└── fotos/
    ├── 8f3a…c1.jpg       nome do arquivo = uuid da foto
    └── 2b90…7e.jpg
```

Você move esse zip para o notebook do jeito que for mais prático — cabo USB,
Google Drive, ou WhatsApp **enviado como documento** (nunca como imagem: como
imagem o WhatsApp recomprime e destrói o detalhe da fissura). Na plataforma,
`Excel / Banco de Dados → Importar vistoria` lê o zip.

Três garantias do formato, todas cobertas por teste:

- **Importação idempotente.** Cada ocorrência e cada foto carregam um `uuid`
  gerado no celular. Reimportar o mesmo zip não duplica nada — então o celular
  nunca precisa apagar dados para exportar, e você pode exportar quantas vezes
  quiser durante a vistoria.
- **A foto não vai para dentro do banco.** O arquivo vai para
  `uploads/fotos/<residência>/`; o SQLite guarda o caminho e o SHA-256. O banco
  fica pequeno, o backup fica simples, e a foto continua sendo um `.jpg` comum.
- **O zip é tratado como não confiável.** Nome de arquivo de dentro do zip nunca
  é usado como caminho (não há como escapar da pasta de destino), e só entram
  extensões de imagem.

Ordem de grandeza: 5 a 15 casas × 30–60 fotos comprimidas ≈ 10–25 MB por
vistoria. Passa tranquilo em qualquer um dos meios acima.

---

## Como rodar

```bash
pip install -r tcc/requirements.txt
streamlit run tcc/app.py
```

Usuário inicial `admin` / senha `admin` (a senha é gravada com PBKDF2-SHA256 +
salt; troque em Configurações antes de usar com dados reais).

Testes — não precisam de nenhuma dependência externa:

```bash
python3 -m unittest discover -s tcc/tests -t .
```

---

## Estrutura

```
tcc/
├── app.py                      casca Streamlit: login, navegação, páginas
├── config.py                   identidade, paleta, menu, aviso de responsabilidade
├── database/
│   ├── schema.sql              15 tabelas, SQL portável (SQLite → PostgreSQL)
│   ├── db.py                   conexão e criação idempotente
│   └── seed.py                 carga inicial + hash de senha
├── services/                   REGRA DE NEGÓCIO — sem Streamlit, 100% testável
│   ├── gut.py                  matriz GUT e faixas de prioridade
│   ├── garantias.py            relógio de garantias
│   ├── edificacao.py           idade da edificação e faixas etárias
│   └── pacote_campo.py         leitura e validação do pacote de vistoria
├── data/                       CSV de partida (sistemas, ambientes, prazos)
├── tests/                      46 testes
└── uploads/{fotos,documentos}/
```

A regra de negócio ficou deliberadamente fora do Streamlit: o cálculo de
vencimento de garantia e a classificação GUT são testados sem subir a interface,
e continuam válidos se um dia a interface mudar.

---

## Decisões que valem registrar na monografia

**Prazos de garantia — nada foi presumido.** A tabela `regras_garantia` foi
criada com as linhas (sistema, componente, tipo de falha) mas com **prazo em
branco** e `conferido = 0`. Enquanto um prazo não for preenchido por você com a
NBR 17170:2022 na mão, aquela garantia aparece como **⚪ SEM PRAZO TIPIFICADO** —
o sistema não inventa prazo. Em caso de divergência entre a planilha do TCC e a
norma, **prevalece a NBR 17170**.

**GUT.** `GUT = G × U × T`, com G, U e T restritos a {1, 3, 6, 8, 10}. Faixas:
P1 ≥ 512 · P2 de 108 a 511 · P3 de 1 a 107. A classificação é sempre uma
proposta: `classificacoes_gut.confirmada_por` registra o engenheiro que
confirmou ou alterou.

**Idade da edificação.** O mês só conta quando o dia chega (15/03/2024 →
14/04/2024 é 0 mês; 15/04/2024 é 1 mês). Confere com o exemplo do TCC:
Habite-se 15/03/2024, vistoria em 20/08/2026 → *2 anos e 5 meses*.

**Datas de vencimento.** Somadas em meses com ajuste de fim de mês
(31/01 + 1 mês → 28 ou 29/02, conforme o ano). Sem isso, garantias com
data-base em dia 29, 30 ou 31 dariam vencimento errado.

**Responsabilidade.** O sistema nunca afirma que um problema é responsabilidade
da construtora. Ele apresenta *situação técnica indicativa de garantia* e remete
ao Termo de Garantia, Manual da Edificação, histórico de manutenção, reformas,
contrato e legislação. Nenhuma automação substitui a avaliação profissional.

**Dados pessoais.** O banco guarda nome, endereço e telefone de proprietários
reais. O sistema roda apenas no notebook do autor. Para a monografia, use a
identificação anônima (`RESIDÊNCIA 001`, `Casa A`).

---

## Ordem de trabalho

Pronto e testado:

- [x] Esquema do banco (15 tabelas, relacional, preparado para PostgreSQL)
- [x] Motor de garantias: vencimento, dias restantes, os 5 status, alerta preventivo
- [x] Matriz GUT e faixas de prioridade
- [x] Idade da edificação e faixas etárias dos gráficos
- [x] Formato do pacote de vistoria (validação, extração, idempotência)
- [x] Login com senha em hash e navegação lateral
- [x] Cadastro e listagem de residências

A fazer, nesta ordem:

- [ ] Importação do Excel do TCC (aguardando o arquivo)
- [ ] Ambientes por residência
- [ ] Nova vistoria e registro de patologias
- [ ] Catálogo fotográfico e comparação temporal
- [ ] Tela de classificação GUT
- [ ] Garantias por residência e relógio de garantias
- [ ] Dashboard com os 5 gráficos
- [ ] App de campo (HTML offline) e a tela de importação do pacote
- [ ] Plano de manutenção e Gantt de 10 anos
- [ ] Protocolos, documentos, histórico
- [ ] Dados da pesquisa (consolidação da amostra)
- [ ] Relatório em PDF — **fase 2**, conforme combinado
