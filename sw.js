/* Service worker do Registro de Campo e EPI.

   Estratégia: páginas sempre pela rede quando há internet (assim a versão
   nova chega sem depender de cache), caindo para a cópia guardada quando
   está sem sinal — que é a situação da obra. Os arquivos de versão nunca
   são guardados, senão o aviso de atualização olharia para o passado. */
var CACHE = 'campo-epi-2026-09-23';
var ARQUIVOS = [
  './',
  './index.html',
  './campo.html',
  './epi.html',
  './manifest.webmanifest',
  './icone-192.png',
  './icone-512.png'
];

self.addEventListener('install', function(ev){
  ev.waitUntil(
    caches.open(CACHE).then(function(cache){
      // um arquivo que falhe não pode derrubar a instalação inteira
      return Promise.all(ARQUIVOS.map(function(url){
        return cache.add(url).catch(function(){});
      }));
    }).then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function(ev){
  ev.waitUntil(
    caches.keys().then(function(nomes){
      return Promise.all(nomes.map(function(n){
        return n === CACHE ? null : caches.delete(n);
      }));
    }).then(function(){ return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function(ev){
  var req = ev.request;
  if(req.method !== 'GET') return;
  var url;
  try{ url = new URL(req.url); }catch(e){ return; }
  if(url.origin !== self.location.origin) return;
  if(/versao[^/]*\.json$/.test(url.pathname)) return;      // sempre da rede, sem cache

  var ehPagina = req.mode === 'navigate' || /\.html$/.test(url.pathname) || url.pathname.endsWith('/');
  if(ehPagina){
    ev.respondWith(
      fetch(req).then(function(resp){
        var copia = resp.clone();
        caches.open(CACHE).then(function(c){ c.put(req, copia); }).catch(function(){});
        return resp;
      }).catch(function(){
        return caches.match(req).then(function(guardado){
          return guardado || caches.match('./index.html');
        });
      })
    );
    return;
  }

  ev.respondWith(
    caches.match(req).then(function(guardado){
      if(guardado){
        fetch(req).then(function(resp){                     // atualiza em segundo plano
          caches.open(CACHE).then(function(c){ c.put(req, resp); }).catch(function(){});
        }).catch(function(){});
        return guardado;
      }
      return fetch(req).then(function(resp){
        var copia = resp.clone();
        caches.open(CACHE).then(function(c){ c.put(req, copia); }).catch(function(){});
        return resp;
      });
    })
  );
});
