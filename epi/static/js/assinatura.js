/* Captura de assinatura em canvas (mouse/toque), usando signature_pad.
   Cada bloco <div class="assinatura-campo" data-alvo="id_do_input_hidden"> com um <canvas>
   dentro é ligado a um input hidden que recebe o PNG em base64 no envio do formulário. */
(function () {
  function ajustarCanvas(canvas, pad) {
    var ratio = Math.max(window.devicePixelRatio || 1, 1);
    var dados = pad.toData();
    canvas.width = canvas.offsetWidth * ratio;
    canvas.height = canvas.offsetHeight * ratio;
    canvas.getContext('2d').scale(ratio, ratio);
    pad.clear();
    if (dados && dados.length) { pad.fromData(dados); }
  }

  function iniciar(bloco) {
    var canvas = bloco.querySelector('canvas');
    var alvo = document.getElementById(bloco.dataset.alvo);
    if (!canvas || !alvo) { return; }

    var pad = new SignaturePad(canvas, {
      backgroundColor: 'rgba(255,255,255,1)',
      penColor: '#111827',
      minWidth: 0.9,
      maxWidth: 2.4
    });

    var redimensionar = function () { ajustarCanvas(canvas, pad); };
    redimensionar();
    window.addEventListener('resize', redimensionar);
    window.addEventListener('orientationchange', redimensionar);

    var dica = bloco.querySelector('.dica');
    pad.addEventListener('beginStroke', function () { if (dica) { dica.style.display = 'none'; } });

    var limpar = (bloco.parentElement || bloco).querySelector('[data-limpar]');
    if (limpar) {
      limpar.addEventListener('click', function () {
        pad.clear();
        alvo.value = '';
        if (dica) { dica.style.display = ''; }
      });
    }

    var form = bloco.closest('form');
    if (form) {
      form.addEventListener('submit', function () {
        alvo.value = pad.isEmpty() ? '' : pad.toDataURL('image/png');
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.assinatura-campo').forEach(iniciar);
  });
})();
