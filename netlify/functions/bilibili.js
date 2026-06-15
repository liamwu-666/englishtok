// Netlify Function — 代理 B站 API 请求
const https = require('https');
const http = require('http');

exports.handler = async (event) => {
  const params = event.queryStringParameters || {};
  const splat = params.splat || '';
  // Build Bilibili API URL
  const queryParts = [];
  for (const [k, v] of Object.entries(params)) {
    if (k !== 'splat') queryParts.push(encodeURIComponent(k) + '=' + encodeURIComponent(v));
  }
  const url = 'https://api.bilibili.com/' + splat + (queryParts.length ? '?' + queryParts.join('&') : '');

  return new Promise((resolve) => {
    const mod = url.startsWith('https') ? https : http;
    mod.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Referer': 'https://www.bilibili.com',
        'Origin': 'https://www.bilibili.com',
        'Accept': 'application/json, text/plain, */*',
      },
    }, (resp) => {
      let body = '';
      resp.on('data', chunk => body += chunk);
      resp.on('end', () => {
        resolve({
          statusCode: resp.statusCode,
          headers: {
            'content-type': resp.headers['content-type'] || 'application/json',
            'access-control-allow-origin': '*',
            'cache-control': 'public, max-age=60',
          },
          body: body,
        });
      });
    }).on('error', (e) => {
      resolve({
        statusCode: 502,
        headers: { 'content-type': 'application/json', 'access-control-allow-origin': '*' },
        body: JSON.stringify({ error: e.message }),
      });
    });
  });
};
