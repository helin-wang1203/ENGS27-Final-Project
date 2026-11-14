#!/usr/bin/env python3
"""Serve the project site on this machine only, and rebuild it whenever a source is saved.

    python site/serve.py              http://localhost:8027
    python site/serve.py --port 9000
    python site/serve.py --no-open    don't open a browser tab

Open pages reload themselves after each rebuild. Stop with Ctrl-C.
"""
import argparse
import functools
import http.server
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402

WATCHED = [build.NOTES, build.NOTEBOOK, HERE / "style.css"]
version = 0


def stamp():
    return tuple(p.stat().st_mtime_ns if p.exists() else 0 for p in WATCHED)


def rebuild():
    global version
    try:
        build.build()
        version += 1
        print(time.strftime("%H:%M:%S"), "rebuilt")
    except Exception:  # e.g. the notebook was caught half-saved; the next save retries
        print(time.strftime("%H:%M:%S"), "build failed, keeping the previous pages:")
        traceback.print_exc()


def watch():
    last = stamp()
    while True:
        time.sleep(0.7)
        now = stamp()
        if now != last:
            last = now
            time.sleep(0.2)  # let the editor finish writing
            rebuild()


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/__version"):
            body = str(version).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8027)
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    rebuild()
    threading.Thread(target=watch, daemon=True).start()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), functools.partial(Handler, directory=str(HERE)))
    url = f"http://localhost:{args.port}/"
    print(f"serving {url}  (Ctrl-C to stop)")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
