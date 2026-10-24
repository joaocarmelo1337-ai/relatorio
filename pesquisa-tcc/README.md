# Pesquisa de TCC – Patologias em imóveis novos (Campo Grande/MS)

Site de página única (`index.html`) com formulário de 4 etapas. As respostas são gravadas em uma planilha do Google por meio de um Google Apps Script.

```
pesquisa-tcc/
├── index.html           # o site completo (Tailwind, Inter e Lucide via CDN)
├── apps-script/Code.gs  # receptor que grava as respostas na planilha
└── README.md
```

## 1. Criar a planilha e implantar o Apps Script

1. Acesse [sheets.google.com](https://sheets.google.com) e crie uma planilha em branco (ex.: "Pesquisa TCC – Respostas"). Não precisa criar abas nem cabeçalhos: o script cria a aba **Respostas** sozinho na primeira resposta.
2. Na planilha, abra **Extensões → Apps Script**.
3. Apague o conteúdo do arquivo `Código.gs` e cole todo o conteúdo de `apps-script/Code.gs`. Salve (Ctrl+S).
4. Clique em **Implantar → Nova implantação**.
5. Na engrenagem ao lado de "Selecionar tipo", escolha **App da Web** e configure:
   - **Executar como:** Eu (seu e-mail)
   - **Quem pode acessar:** **Qualquer pessoa**
6. Clique em **Implantar** e autorize o acesso quando o Google pedir (em "Avançado → Acessar … (não seguro)", pois o script é seu).
7. Copie a **URL do app da Web** (termina em `/exec`).
8. Teste: abra essa URL no navegador. Deve aparecer `{"ok":true,"servico":"pesquisa-tcc"}`.

> Se você alterar o `Code.gs` depois, é preciso **Implantar → Gerenciar implantações → editar → Nova versão** para a mudança valer. A URL continua a mesma.

## 2. Colar a URL em `APPS_SCRIPT_URL`

Abra o `index.html` e procure (Ctrl+F) por `APPS_SCRIPT_URL`. Está no início do último bloco `<script>`:

```js
const APPS_SCRIPT_URL = 'COLE_AQUI_A_URL_DO_APPS_SCRIPT';
```

Troque o texto entre aspas pela URL copiada no passo anterior. Enquanto o placeholder estiver lá, o formulário avisa que não está configurado e não envia nada.

Outras edições comuns:
- **Cores:** bloco `tailwind.config` no `<head>` (`verde.50`, `verde.500`, `verde.900` e `cinza-texto`).
- **Textos da introdução:** dentro do `<header>`.
- **Opções das perguntas:** objeto `OPCOES` no início do script.

## 3. Publicar de graça

### GitHub Pages
1. Crie um repositório no GitHub e envie o conteúdo desta pasta (o `index.html` precisa ficar na raiz do que for publicado).
2. No repositório: **Settings → Pages**.
3. Em **Build and deployment**, escolha **Deploy from a branch**, selecione a branch `main` e a pasta `/ (root)` (ou `/docs`, se você colocou o site lá). Salve.
4. Em cerca de 1 minuto o site fica em `https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/`.

### Netlify
1. Acesse [app.netlify.com/drop](https://app.netlify.com/drop) (crie uma conta gratuita).
2. Arraste a pasta `pesquisa-tcc` (ou só o `index.html`) para a área indicada.
3. Em segundos você recebe um endereço `https://nome-aleatorio.netlify.app`. Em **Site configuration → Change site name** dá para trocar o nome.

Depois de publicar, divulgue o link (WhatsApp, grupos de condomínio etc.).

## 4. Checklist de teste

Antes de divulgar, teste **no site publicado**, de preferência pelo celular:

- [ ] A URL do Apps Script aberta no navegador mostra `"ok":true`.
- [ ] `APPS_SCRIPT_URL` foi trocada no `index.html`.
- [ ] O botão "Quero participar" rola até o formulário.
- [ ] As 4 etapas avançam e voltam; a barra de progresso vai de 25% a 100%.
- [ ] Etapa 1: deixar nome ou WhatsApp vazio bloqueia o avanço e mostra o erro em português.
- [ ] A máscara do WhatsApp formata como `(67) 99999-9999`.
- [ ] Etapa 2: bairro e tipo de imóvel vazios bloqueiam o avanço.
- [ ] Etapa 3: marcar "Outro" mostra o campo de descrição; "Melhor dia e horário" só aparece com "Sim" ou "Talvez"; "Nenhum" desmarca as outras opções.
- [ ] Etapa 4: tentar enviar sem a Caixa 1 é bloqueado.
- [ ] Envio completo: a tela de agradecimento aparece e surge **uma linha nova** na aba `Respostas`, com as colunas na ordem certa.
- [ ] Com a Caixa 2 desmarcada, `consent_fotos` aparece como `FALSE` na planilha.
- [ ] Sem internet (modo avião), o envio mostra a mensagem de erro e permite tentar de novo sem perder o que foi digitado.
- [ ] Um texto começando com `=` (ex.: `=1+1`) aparece na planilha como texto, não como fórmula.
- [ ] Depois dos testes, apague as linhas de teste da planilha.

## Privacidade

A planilha contém dados pessoais (nome, WhatsApp, e-mail). Não compartilhe o link de edição, use só para a pesquisa e apague os dados quando o TCC terminar, conforme prometido no formulário.
