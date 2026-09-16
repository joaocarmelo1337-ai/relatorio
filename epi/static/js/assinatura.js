/* Captura de assinatura em tela cheia: o funcionário assina usando o aparelho
   inteiro e o traço é recortado antes de ir para o servidor, como PNG base64
   no input hidden de cada campo. */
(function () {
  var pad = null;
  var campoAberto = null;

  function ajustarCanvas() {
    var canvas = document.getElementById('canvasAssin');
    if (!canvas || document.getElementById('modalAssin').hidden || !canvas.offsetWidth) { return; }
    var ratio = Math.max(window.devicePixelRatio || 1, 1);
    var dados = pad.toData();
    canvas.width = canvas.offsetWidth * ratio;
    canvas.height = canvas.offsetHeight * ratio;
    canvas.getContext('2d').scale(ratio, ratio);
    pad.clear();
    if (dados && dados.length) { try { pad.fromData(dados); } catch (e) {} }
  }

  function abrir(campo) {
    campoAberto = campo;
    var previa = document.querySelector('[data-previa="' + campo + '"]');
    document.getElementById('modalAssinTitulo').textContent =
      (previa && previa.dataset.rotulo) || 'Assinatura';
    document.getElementById('modalAssin').hidden = false;
    document.getElementById('dicaAssin').style.display = '';
    setTimeout(function () { ajustarCanvas(); pad.clear(); }, 60);
  }

  function fechar() {
    document.getElementById('modalAssin').hidden = true;
    campoAberto = null;
  }

  function confirmar() {
    if (!campoAberto) { return fechar(); }
    if (pad.isEmpty()) {
      alert('Nada foi desenhado. Assine na área branca ou toque em Cancelar.');
      return;
    }
    var png = recortar(document.getElementById('canvasAssin'));
    document.getElementById(campoAberto).value = png;
    document.getElementById(campoAberto + '_apagar').value = '';
    var previa = document.querySelector('[data-previa="' + campoAberto + '"]');
    if (previa) { previa.innerHTML = '<img src="' + png + '" alt="Assinatura colhida agora">'; }
    fechar();
  }

  function apagar(campo) {
    if (!confirm('Apagar esta assinatura?')) { return; }
    document.getElementById(campo).value = '';
    document.getElementById(campo + '_apagar').value = '1';
    var previa = document.querySelector('[data-previa="' + campo + '"]');
    if (previa) { previa.innerHTML = '<span class="sem">Nenhuma assinatura ainda — toque para assinar</span>'; }
  }

  /* Recorta o espaço em branco em volta do traço e devolve um PNG enxuto. */
  function recortar(origem) {
    var ctx = origem.getContext('2d');
    var dados;
    try { dados = ctx.getImageData(0, 0, origem.width, origem.height); }
    catch (e) { return origem.toDataURL('image/png'); }
    var d = dados.data, minX = origem.width, minY = origem.height, maxX = 0, maxY = 0, achou = false;
    for (var y = 0; y < origem.height; y++) {
      for (var x = 0; x < origem.width; x++) {
        var i = (y * origem.width + x) * 4;
        if (d[i] < 200 || d[i + 1] < 200 || d[i + 2] < 200) {
          achou = true;
          if (x < minX) { minX = x; }
          if (x > maxX) { maxX = x; }
          if (y < minY) { minY = y; }
          if (y > maxY) { maxY = y; }
        }
      }
    }
    if (!achou) { return ''; }
    var folga = Math.round(origem.width * 0.015) + 6;
    minX = Math.max(0, minX - folga); minY = Math.max(0, minY - folga);
    maxX = Math.min(origem.width - 1, maxX + folga); maxY = Math.min(origem.height - 1, maxY + folga);
    var largura = maxX - minX + 1, altura = maxY - minY + 1;
    var escala = Math.min(1, 900 / largura, 400 / altura);
    var saida = document.createElement('canvas');
    saida.width = Math.max(1, Math.round(largura * escala));
    saida.height = Math.max(1, Math.round(altura * escala));
    var c2 = saida.getContext('2d');
    c2.fillStyle = '#fff';
    c2.fillRect(0, 0, saida.width, saida.height);
    c2.drawImage(origem, minX, minY, largura, altura, 0, 0, saida.width, saida.height);
    return saida.toDataURL('image/png');
  }

  document.addEventListener('DOMContentLoaded', function () {
    var canvas = document.getElementById('canvasAssin');
    if (!canvas) { return; }
    pad = new SignaturePad(canvas, {
      backgroundColor: 'rgba(255,255,255,1)',
      penColor: '#111827',
      minWidth: 1.1,
      maxWidth: 3.2
    });
    pad.addEventListener('beginStroke', function () {
      document.getElementById('dicaAssin').style.display = 'none';
    });

    document.querySelectorAll('[data-assinar]').forEach(function (bt) {
      bt.addEventListener('click', function () { abrir(bt.dataset.assinar); });
    });
    document.querySelectorAll('[data-apagar]').forEach(function (bt) {
      bt.addEventListener('click', function () { apagar(bt.dataset.apagar); });
    });
    document.querySelectorAll('[data-previa]').forEach(function (el) {
      el.addEventListener('click', function () { abrir(el.dataset.previa); });
    });

    document.getElementById('btCancelarAssin').addEventListener('click', fechar);
    document.getElementById('btLimparAssin').addEventListener('click', function () {
      pad.clear();
      document.getElementById('dicaAssin').style.display = '';
    });
    document.getElementById('btConfirmarAssin').addEventListener('click', confirmar);

    window.addEventListener('resize', ajustarCanvas);
    window.addEventListener('orientationchange', function () { setTimeout(ajustarCanvas, 350); });
  });
})();
