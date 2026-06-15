// Vercel Serverless Function — 代理 B站 API 请求
// 路径: /api/bilibili/* → https://api.bilibili.com/*

export default async function handler(req, res) {
  const { path, ...queryParams } = req.query;
  const apiPath = Array.isArray(path) ? path.join('/') : (path || '');
  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries(queryParams).filter(([k]) => k !== 'path'))
  ).toString();
  const url = `https://api.bilibili.com/${apiPath}${qs ? '?' + qs : ''}`;

  try {
    const resp = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Referer': 'https://www.bilibili.com',
        'Origin': 'https://www.bilibili.com',
        'Accept': 'application/json, text/plain, */*',
      },
    });

    const body = await resp.text();

    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Cache-Control', 'public, max-age=60, s-maxage=120');
    res.status(resp.status).send(body);
  } catch (e) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.status(502).json({ error: 'Proxy error: ' + e.message });
  }
}
