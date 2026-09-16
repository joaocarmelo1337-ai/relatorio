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
        ' data-ca="' + (e.ca || '') + '" data-tamanho="' + (e.tem_tamanho ? '1' : '0') + '">' +
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
        '<div class="campo campo-tamanho"><label>Tamanho</label>' +
          '<input type="text" class="in-tamanho" name="item_tamanho[]" list="lista-tamanhos" ' +
          'placeholder="P, M, G, GG, EXG ou nº" value="' + (dados.tamanho || '') + '"></div>' +
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

    function aplicar(preservarCa) {
      var novo = sel.value === '__novo__';
      campoNome.style.display = novo ? '' : 'none';
      var op = sel.selectedOptions[0];
      if (novo || !sel.value) {
        campoTam.style.display = '';
      } else {
        if (!preservarCa) { inCa.value = op.dataset.ca || ''; }
        // o campo de tamanho só aparece nos itens que pedem tamanho (camisa, calça, calçado...)
        campoTam.style.display = op.dataset.tamanho === '1' ? '' : 'none';
        if (op.dataset.tamanho !== '1' && !preservarCa) { campoTam.querySelector('input').value = ''; }
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
