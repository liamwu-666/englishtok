#!/usr/bin/env python3
"""EnglishTok — 本地代理服务器
中转 B站 API + 视频流 + 图片，绕过跨域和防盗链
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import ssl
import os
import sys
import io

PORT = 8765
DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(DIR, 'index.html')

FAKE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

BL_HEADERS = {
    **FAKE_HEADERS,
    'Referer': 'https://www.bilibili.com',
    'Origin': 'https://www.bilibili.com',
}

ctx = ssl.create_default_context()


def do_fetch(url, headers, timeout=15):
    """发起请求，返回 (status, content_type, data)"""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = resp.read()
            ct = resp.headers.get_content_type() or 'application/octet-stream'
            return resp.status, ct, data
    except urllib.error.HTTPError as e:
        body = e.read() if hasattr(e, 'read') else b''
        return e.code, 'application/json', body or json.dumps({'error': str(e)}).encode()
    except Exception as e:
        return 502, 'text/plain', str(e).encode()


def proxy_video_stream(wfile, url, range_header, chunk_size=256*1024):
    """流式代理视频，支持 Range 请求（断点续传/拖动进度条）"""
    headers = dict(BL_HEADERS)
    headers['Accept'] = '*/*'
    if range_header:
        headers['Range'] = range_header

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            total_size = resp.headers.get('Content-Length')
            content_type = resp.headers.get_content_type() or 'video/mp4'
            content_range = resp.headers.get('Content-Range')

            if resp.status in (200, 206):
                wfile.write(('HTTP/1.1 %d OK\r\n' % resp.status).encode())
            else:
                wfile.write(b'HTTP/1.1 502 Bad Gateway\r\n')

            wfile.write(('Content-Type: %s\r\n' % content_type).encode())
            wfile.write(b'Access-Control-Allow-Origin: *\r\n')
            wfile.write(b'Accept-Ranges: bytes\r\n')
            wfile.write(b'Cache-Control: public, max-age=3600\r\n')
            if content_range:
                wfile.write(('Content-Range: %s\r\n' % content_range).encode())
            if total_size and not content_range:
                wfile.write(('Content-Length: %s\r\n' % total_size).encode())
            wfile.write(b'Connection: close\r\n')
            wfile.write(b'\r\n')

            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                wfile.write(chunk)
    except Exception as e:
        msg = str(e).encode()
        wfile.write(b'HTTP/1.1 502 Bad Gateway\r\n')
        wfile.write(b'Content-Type: text/plain\r\n')
        wfile.write(('Content-Length: %d\r\n' % len(msg)).encode())
        wfile.write(b'\r\n')
        wfile.write(msg)


class Handler(http.server.BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, filepath):
        ext = os.path.splitext(filepath)[1]
        mime = {
            '.html': 'text/html; charset=utf-8', '.css': 'text/css',
            '.js': 'application/javascript', '.json': 'application/json',
            '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
        }.get(ext, 'application/octet-stream')
        with open(filepath, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Range, Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = parsed.query

        # ---- 视频流代理 (支持 Range) ----
        if path.startswith('/api/video'):
            params = urllib.parse.parse_qs(qs)
            url = params.get('url', [None])[0]
            if not url:
                self.send_json(400, {'error': 'Missing url param'})
                return
            range_header = self.headers.get('Range')
            self.connection.setblocking(True)
            proxy_video_stream(self.wfile, url, range_header)
            return

        # ---- 图片代理 ----
        if path.startswith('/api/img'):
            params = urllib.parse.parse_qs(qs)
            url = params.get('url', [None])[0]
            if not url:
                self.send_json(400, {'error': 'Missing url param'})
                return
            status, ct, data = do_fetch(url, BL_HEADERS, 10)
            self.send_response(status)
            self.send_header('Content-Type', ct)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'public, max-age=86400')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # ---- Bilibili API ----
        if path.startswith('/api/bilibili'):
            real = path.replace('/api/bilibili', '')
            url = 'https://api.bilibili.com%s?%s' % (real, qs)
            status, ct, data = do_fetch(url, BL_HEADERS)
            self.send_response(status)
            self.send_header('Content-Type', ct)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # ---- YouTube API ----
        if path.startswith('/api/youtube'):
            real = path.replace('/api/youtube', '')
            url = 'https://www.googleapis.com/youtube/v3%s?%s' % (real, qs)
            status, ct, data = do_fetch(url, FAKE_HEADERS)
            self.send_response(status)
            self.send_header('Content-Type', ct)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # ---- 静态文件 ----
        if path == '/' or path == '/index.html':
            filepath = HTML_FILE
        else:
            filepath = os.path.join(DIR, path.lstrip('/'))

        if os.path.isfile(filepath):
            self.send_file(filepath)
        else:
            self.send_json(404, {'error': 'Not Found'})

    def log_message(self, fmt, *args):
        msg = str(args[0]) if args else ''
        if '/api/' in msg:
            print('  [%s] %s' % (self.command, msg))


class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """多线程服务器，支持同时处理视频流和 API 请求"""
    daemon_threads = True


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print('=' * 44)
    print('  EnglishTok Server')
    print('  http://localhost:%d' % PORT)
    print('  Press Ctrl+C to stop')
    print('=' * 44)
    server = ThreadedServer(('0.0.0.0', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
        server.shutdown()
