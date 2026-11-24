"""Serve the canonical MkDocs fragment outside MkDocs for local UI development."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import functools

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'docs/learn/ai-roadmap'
FRAGMENT = ROOT / 'material/overrides/partials/ai-roadmap-content.html'

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ASSETS), **kwargs)

    def do_GET(self):
        if self.path.split('?')[0] == '/':
            page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width,initial-scale=1">'
                    '<title>SSC AI Roadmap</title><style>body{margin:0}</style>'
                    '<link rel="stylesheet" href="css/roadmap.css"></head><body>'
                    + FRAGMENT.read_text(encoding='utf-8') +
                    '<script type="module" src="js/main.js"></script></body></html>')
            payload = page.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            super().do_GET()

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8001)
    args=parser.parse_args()
    with ThreadingHTTPServer(('127.0.0.1',args.port),Handler) as server:
        print(f'http://127.0.0.1:{args.port}',flush=True)
        server.serve_forever()
