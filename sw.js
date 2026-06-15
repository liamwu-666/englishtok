// EnglishTok Service Worker — 缓存核心资源，离线也能打开 App 壳
const CACHE = 'englishtok-v1';
const PRELOAD = ['/', '/index.html', '/manifest.json'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(PRELOAD))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

// 缓存策略: 静态文件优先缓存，API 请求走网络
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // API 请求 — 只走网络
  if (url.pathname.startsWith('/api/')) return;

  // 静态资源 — 缓存优先
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
