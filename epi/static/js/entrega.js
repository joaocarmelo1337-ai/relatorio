/* Linhas de itens do formulário de entrega: escolher da lista mestre, adicionar
   item novo na hora (com opção de salvar na lista mestre), CA e tamanho por item. */
(function () {
  var EPIS = [];
  var TAMANHOS = [];
  var container, modelo, contador = 0;

  function opcoesSelect(selecionado) {
    var html = '<option value="">— escolha o EPI/uniforme —</option>';
    EPIS.forEach(function (e) {
      html += '<option value="' + e.id + '"' + (String(selecionado) === String(e.id) ? ' selected' : '') +
        ' data-ca="' + (e.ca || '') + '" data-tamanho="' + (Number(e.tem_tamanho) || 0) + '">' +
        e.nome + (e.ca ? ' (CA ' + e.ca + ')' : '') + '</option>';
    });
    html += '<option value="__novo__">+ Outro item (digitar agora)</option>';
    return html;
  }

  function criarLinha(dados) {
    dados = dados || {};
    var i = contador++;
    var chave = 'item_assin_' + i;          // cada material assina em separado
    var no = document.createElement('div');
    no.className = 'item';
    no.dataset.chave = chave;
    no.innerHTML =
      '<div class="item-topo">' +
        '<div class="campo"><label>EPI / Uniforme</label>' +
          '<select class="sel-epi">' + opcoesSelect(dados.epi_id) + '</select></div>' +
        '<button type="button" class="btn perigo pequeno remover" title="Remover item">✕</button>' +
      '</div>' +
      '<div class="campo campo-nome" style="display:none;margin-top:10px">' +
        '<label>Nome do item novo</label>' +
        '<input type="text" class="in-nome" placeholder="Ex.: LUVA NITRÍLICA">' +
        '<div class="linha-check"><input type="checkbox" class="ck-salvar" id="ck' + i + '" checked>' +
        '<label for="ck' + i + '">Salvar este item na lista mestre para uso futuro</label></div>' +
      '</div>' +
      '<div class="grade" style="margin-top:10px">' +
        '<div class="campo"><label>CA</label><input type="text" class="in-ca" name="item_ca[]" ' +
          'inputmode="numeric" placeholder="opcional" value="' + (dados.ca || '') + '"></div>' +
        '<div class="campo"><label>Quantidade</label><input type="text" class="in-qtde" name="item_qtde[]" ' +
          'inputmode="decimal" value="' + (dados.quantidade != null ? dados.quantidade : '1') + '"></div>' +
        '<div class="campo campo-tamanho"><label class="rotulo-tamanho">Tamanho</label>' +
          '<select class="sel-tamanho"><option value="">—</option>' +
          TAMANHOS.map(function (t) { return '<option value="' + t + '">' + t + '</option>'; }).join('') +
          '</select>' +
          '<input type="text" class="in-numero" placeholder="Ex.: 41" hidden>' +
          '<input type="hidden" class="hd-tamanho" name="item_tamanho[]" value=""></div>' +
        '<button type="button" class="btn pequeno link-tamanho" hidden>+ informar tamanho / numeração</button>' +
      '</div>' +
      '<div class="assin-item">' +
        '<label>Assinatura de quem recebeu este material</label>' +
        '<div class="previa-assin" data-previa="' + chave + '" data-rotulo="Assinatura do material">' +
          (dados.assinatura_url
            ? '<img src="' + dados.assinatura_url + '" alt="Assinatura já registrada">'
            : '<span class="sem">Nenhuma assinatura ainda — toque para assinar</span>') +
        '</div>' +
        '<div class="acoes">' +
          '<button type="button" class="btn primario pequeno" data-assinar="' + chave + '">Assinar em tela cheia</button>' +
          '<button type="button" class="btn pequeno" data-apagar="' + chave + '">Apagar</button>' +
        '</div>' +
      '</div>' +
      '<input type="hidden" class="hd-nome" name="item_nome[]" value="">' +
      '<input type="hidden" class="hd-epi" name="item_epi_id[]" value="">' +
      '<input type="hidden" class="hd-salvar" name="item_salvar[]" value="0">' +
      '<input type="hidden" id="' + chave + '" name="item_assinatura[]" value="">' +
      '<input type="hidden" id="' + chave + '_apagar" name="item_assinatura_apagar[]" value="">' +
      '<input type="hidden" name="item_assinatura_id[]" value="' +
        (dados.assinatura_id != null ? dados.assinatura_id : '') + '">' +
      '<input type="hidden" name="item_data_devolucao[]" value="' + (dados.data_devolucao || '') + '">' +
      '<input type="hidden" name="item_assinatura_devolucao_id[]" value="' +
        (dados.assinatura_devolucao_id != null ? dados.assinatura_devolucao_id : '') + '">';

    var sel = no.querySelector('.sel-epi');
    var campoNome = no.querySelector('.campo-nome');
    var inNome = no.querySelector('.in-nome');
    var inCa = no.querySelector('.in-ca');
    var campoTam = no.querySelector('.campo-tamanho');
    var selTam = no.querySelector('.sel-tamanho');
    var inNumero = no.querySelector('.in-numero');
    var hdTam = no.querySelector('.hd-tamanho');
    var rotuloTam = no.querySelector('.rotulo-tamanho');
    var linkTam = no.querySelector('.link-tamanho');

    /* O campo segue a ficha em papel: letra só para camisa, camisa polo, calça
       e jaleco; numeração só para calçado; o resto não tem tamanho. */
    function ajustarTamanho(tipo) {
      campoTam.hidden = (tipo === 0);
      selTam.hidden = (tipo !== 1);
      inNumero.hidden = (tipo !== 2);
      rotuloTam.textContent = (tipo === 2) ? 'Numeração' : 'Tamanho';
      if (tipo === 2) {
        inNumero.setAttribute('inputmode', 'numeric');
        inNumero.removeAttribute('list');
        inNumero.placeholder = 'Ex.: 41';
      }
      // item sem tamanho não mostra campo, mas deixa o atalho caso precise digitar
      linkTam.hidden = (tipo !== 0);
      if (tipo === 0) { selTam.value = ''; inNumero.value = ''; }
      guardarTamanho();
    }

    /* Escape para qualquer item: campo livre, onde cabe tanto GG quanto 41. */
    function liberarTamanho() {
      campoTam.hidden = false;
      selTam.hidden = true;
      inNumero.hidden = false;
      inNumero.setAttribute('list', 'lista-tamanhos');
      inNumero.removeAttribute('inputmode');
      inNumero.placeholder = 'Ex.: GG ou 41';
      rotuloTam.textContent = 'Tamanho / numeração';
      linkTam.hidden = true;
      inNumero.focus();
    }

    function guardarTamanho() {
      var v = campoTam.hidden ? '' : (selTam.hidden ? inNumero.value : selTam.value);
      hdTam.value = (v || '').trim().toUpperCase();
    }

    function aplicar(preservarCa) {
      var novo = sel.value === '__novo__';
      campoNome.style.display = novo ? '' : 'none';
      var op = sel.selectedOptions[0];
      if (novo) {
        liberarTamanho();                     // item digitado na hora: campo livre
        rotuloTam.textContent = 'Tamanho / numeração (se tiver)';
      } else if (!sel.value) {
        ajustarTamanho(0);
      } else {
        if (!preservarCa) { inCa.value = op.dataset.ca || ''; }
        ajustarTamanho(Number(op.dataset.tamanho) || 0);
      }
      sincronizar();
    }

    function sincronizar() {
      var novo = sel.value === '__novo__';
      var previa = no.querySelector('[data-previa]');
      no.querySelector('.hd-epi').value = novo || !sel.value ? '' : sel.value;
      no.querySelector('.hd-nome').value = novo
        ? (inNome.value || '')
        : (sel.value ? sel.selectedOptions[0].textContent.replace(/\s*\(CA .*\)$/, '').trim() : '');
      no.querySelector('.hd-salvar').value = novo && no.querySelector('.ck-salvar').checked ? '1' : '0';
      if (previa) {
        previa.dataset.rotulo = 'Assinatura — ' + (no.querySelector('.hd-nome').value || 'material');
      }
    }

    sel.addEventListener('change', function () { aplicar(false); });
    selTam.addEventListener('change', guardarTamanho);
    inNumero.addEventListener('input', guardarTamanho);
    linkTam.addEventListener('click', liberarTamanho);
    inNome.addEventListener('input', sincronizar);
    no.querySelector('.ck-salvar').addEventListener('change', sincronizar);
    no.querySelector('.remover').addEventListener('click', function () {
      no.remove();
      if (!container.querySelector('.item')) { criarLinha(); }
    });

    container.appendChild(no);
    if (window.Assinatura) { window.Assinatura.ligar(no); }

    if (dados.epi_id) {
      sel.value = String(dados.epi_id);
    } else if (dados.nome) {
      sel.value = '__novo__';
      inNome.value = dados.nome;
      no.querySelector('.ck-salvar').checked = false;
    }
    aplicar(true);
    if (dados.tamanho) {                      // recoloca o tamanho já gravado
      if (TAMANHOS.indexOf(String(dados.tamanho).toUpperCase()) >= 0 && !selTam.hidden) {
        selTam.value = String(dados.tamanho).toUpperCase();
      } else {
        if (inNumero.hidden) { liberarTamanho(); }
        inNumero.value = dados.tamanho;
      }
      guardarTamanho();
    }
    return no;
  }

  document.addEventListener('DOMContentLoaded', function () {
    container = document.getElementById('itens');
    if (!container) { return; }
    EPIS = JSON.parse(document.getElementById('dados-epis').textContent);
    TAMANHOS = JSON.parse(document.getElementById('dados-tamanhos').textContent);
    var iniciais = JSON.parse(document.getElementById('dados-itens').textContent);

    if (iniciais.length) { iniciais.forEach(criarLinha); } else { criarLinha(); }

    document.getElementById('add-item').addEventListener('click', function () {
      var no = criarLinha();
      no.scrollIntoView({ behavior: 'smooth', block: 'center' });
      no.querySelector('.sel-epi').focus();
    });

    document.getElementById('form-entrega').addEventListener('submit', function (ev) {
      var vazio = true;
      var semAssinatura = [];
      container.querySelectorAll('.item').forEach(function (it) {
        var nome = it.querySelector('.hd-nome').value.trim();
        if (!nome) { return; }
        vazio = false;
        var chave = it.dataset.chave;
        var nova = document.getElementById(chave).value;
        var antiga = it.querySelector('[name="item_assinatura_id[]"]').value;
        var apagada = document.getElementById(chave + '_apagar').value === '1';
        if (!nova && (!antiga || apagada)) {
          semAssinatura.push(nome);
          it.classList.add('sem-assinatura');
        } else {
          it.classList.remove('sem-assinatura');
        }
      });
      if (vazio) {
        ev.preventDefault();
        alert('Inclua ao menos um item na entrega.');
        return;
      }
      if (semAssinatura.length) {
        var texto = 'Cada material precisa da assinatura de quem recebeu.\n\nEstá sem assinatura: ' +
                    semAssinatura.join(', ') + '\n\nSalvar assim mesmo e colher depois em “Editar”?';
        if (!confirm(texto)) { ev.preventDefault(); }
      }
    });
  });
})();
