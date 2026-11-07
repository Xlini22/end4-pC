"""Render and check the candidate native GLSL in isolated Firefox/WebGL.
Run: python3 tests/native-glass-optics-check.py tools/glass-optics-preview.html
Requires the already installed Firefox; no browser profile or desktop setting changes.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

html = Path(sys.argv[1]).read_bytes()
done = threading.Event()
result = {}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html)

    def do_POST(self):
        assert self.path == '/result'
        size = int(self.headers['Content-Length'])
        assert 0 < size < 4096
        result.update(json.loads(self.rfile.read(size)))
        self.send_response(204)
        self.end_headers()
        done.set()


with tempfile.TemporaryDirectory(prefix='glass-optics-', dir='/tmp') as temporary:
    profile = Path(temporary)
    (profile / 'user.js').write_text('user_pref("webgl.force-enabled", true);\n')
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}/?check=1'
    try:
        with (profile / 'browser.log').open('w+') as log:
            browser = subprocess.Popen(['firefox', '--headless', '--no-remote', '--profile', temporary,
                                        '--screenshot', '/tmp/end4-optics-preview.png',
                                        '--window-size', '1200,1000', url],
                                       env={**os.environ, 'MOZ_CRASHREPORTER_DISABLE': '1'},
                                       stdout=log, stderr=subprocess.STDOUT)
            try:
                assert done.wait(30), 'Browser did not report shader checks'
                assert result.get('ok'), result
                assert browser.wait(timeout=10) == 0
            finally:
                if browser.poll() is None:
                    browser.terminate()
                    browser.wait(timeout=10)
    finally:
        server.shutdown()
        server.server_close()
print('PASS:', ', '.join(result['checks']))
