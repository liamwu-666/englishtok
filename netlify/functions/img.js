// Netlify Function — 代理 B站图片 (绕过防盗链)
const https = require('https');
const http = require('http');

exports.handler = async (event) => {
  const params = event.queryStringParameters || {};
  const url = params.url;
  if (!url) {
    return { statusCode: 400, headers: { 'content-type': 'application/json', 'access-control-allow-origin': '*' }, body: JSON.stringify({ error: 'Missing url' }) };
  }

  return new Promise((resolve) => {
    const mod = url.startsWith('https') ? https : http;
    mod.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com',
        'Origin': 'https://www.bilibili.com',
        'Accept': 'image/avif,image/webp,image/*,*/*;q=0.8',
      },
    }, (resp) => {
      const chunks = [];
      resp.on('data', chunk => chunks.push(chunk));
      resp.on('end', () => {
        const body = Buffer.concat(chunks);
        resolve({
          statusCode: resp.statusCode,
          headers: {
            'content-type': resp.headers['content-type'] || 'image/jpeg',
            'access-control-allow-origin': '*',
            'cache-control': 'public, max-age=86400',
          },
          body: body.toString('base64'),
          isBase64Encoded: true,
        });
      });
    }).on('error', (e) => {
      resolve({
        statusCode: 502,
        headers: { 'content-type': 'text/plain', 'access-control-allow-origin': '*' },
        body: e.message,
      });
    });
  });
};
