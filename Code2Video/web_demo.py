"""Serve the local BioVideo CLI interface on loopback."""
import json
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOBS = {}
LOCK = threading.Lock()


def read(path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, ValueError):
        return default


class Handler(BaseHTTPRequestHandler):
    def respond(self, content, mime, status=200):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def reply(self, data, status=200):
        self.respond(json.dumps(data).encode(), 'application/json', status)

    def do_POST(self):
        if self.path != '/runs':
            return self.reply({}, 404)
        if self.headers.get('Origin') != f'http://127.0.0.1:{self.server.server_port}':
            return self.reply({}, 403)
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size < 8192 or self.headers.get_content_type() != 'application/json':
                raise ValueError()
            payload = json.loads(self.rfile.read(size))
            request = payload['request'].strip()
            duration = int(payload['duration'])
            backend = payload['backend']
            if not request or not 6 <= duration <= 120 or backend not in ('auto', 'manim'):
                raise ValueError()
        except (KeyError, TypeError, ValueError, AttributeError):
            return self.reply({'error': 'Invalid teaching request'}, 400)
        with LOCK:
            if any(proc.poll() is None for _, proc in JOBS.values()):
                return self.reply({'error': 'A run is already active'}, 409)
            job = uuid.uuid4().hex
            root = HERE / 'outputs' / 'web' / job
            root.mkdir(parents=True)
            cmd = [sys.executable, str(HERE/'generate_biology_video.py'), '--request', request,
                   '--duration', str(duration), '--backend', backend, '--budget', '8',
                   '--output', str(root)]
            with (root/'console.log').open('w') as log:
                JOBS[job] = root, subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        self.reply({'id': job}, 201)

    def do_GET(self):
        if self.path == '/':
            return self.respond((HERE/'web_demo.html').read_bytes(), 'text/html; charset=utf-8')
        kind, _, job = self.path.strip('/').partition('/')
        if job not in JOBS:
            return self.reply({}, 404)
        root, proc = JOBS[job]
        result = read(root/'result.json', {})
        if kind == 'video':
            name = result.get('video_path')
            if name and Path(name).name == name:
                return self.respond((root/name).read_bytes(), 'video/mp4')
        if kind == 'status':
            trace = root/'trajectory.jsonl'
            lines = trace.read_text().splitlines() if trace.exists() else []
            steps = []
            for line in lines:
                try:
                    row = json.loads(line)
                    steps.append(dict(tool=row['tool_name'], status=row['domain_status'],
                                      reason=row['observation'].get('reason')))
                except ValueError:
                    continue
            done = proc.poll() is not None
            return self.reply(result | dict(done=done, steps=steps,
                              sources=[e['url'] for e in read(root/'evidence.json', [])]))
        self.reply({}, 404)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
