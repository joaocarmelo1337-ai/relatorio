// Receptor do formulário da pesquisa de TCC. Grava cada resposta como uma linha na planilha.
const NOME_ABA = 'Respostas';
const CABECALHOS = [
  'data_hora', 'nome', 'whatsapp', 'email', 'bairro', 'tipo_imovel',
  'construtora', 'ano_entrega', 'problemas', 'problema_outro',
  'acionou_construtora', 'aceita_visita', 'melhor_horario',
  'consent_dados', 'consent_fotos'
];

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    const dados = JSON.parse(e.postData.contents);

    // Sem consentimento de dados, não grava nada.
    if (dados.consent_dados !== true) {
      return resposta({ ok: false, erro: 'consentimento_ausente' });
    }

    const planilha = SpreadsheetApp.getActiveSpreadsheet();
    let aba = planilha.getSheetByName(NOME_ABA);
    if (!aba) aba = planilha.insertSheet(NOME_ABA);

    // Cria o cabeçalho na primeira vez.
    if (aba.getLastRow() === 0) {
      aba.appendRow(CABECALHOS);
      aba.getRange(1, 1, 1, CABECALHOS.length)
        .setFontWeight('bold').setBackground('#14532d').setFontColor('#ffffff');
      aba.setFrozenRows(1);
    }

    const linha = CABECALHOS.map(function (campo) { return limpar(dados[campo]); });
    aba.appendRow(linha);
    return resposta({ ok: true });
  } catch (erro) {
    return resposta({ ok: false, erro: 'falha_interna' });
  } finally {
    lock.releaseLock();
  }
}

// Teste rápido: abrir a URL /exec no navegador deve mostrar "ok".
function doGet() {
  return resposta({ ok: true, servico: 'pesquisa-tcc' });
}

// Limita o tamanho e neutraliza fórmulas (=, +, -, @) para evitar injeção na planilha.
function limpar(valor) {
  if (valor === undefined || valor === null) return '';
  let texto = String(valor).trim().slice(0, 1000);
  if (/^[=+\-@]/.test(texto)) texto = "'" + texto;
  return texto;
}

function resposta(objeto) {
  return ContentService.createTextOutput(JSON.stringify(objeto))
    .setMimeType(ContentService.MimeType.JSON);
}
