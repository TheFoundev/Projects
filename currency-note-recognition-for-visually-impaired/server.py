"""Local backend for the Note Sense page.

Serves the static page and adds one endpoint, ``POST /api/detect``, that runs
the project's OpenCV detector on an uploaded photo and answers with JSON.

    python server.py            # http://127.0.0.1:8000/
    python server.py --port 8080

The browser part stays the same as the static build; only the "Identify note"
button now talks to this server instead of showing the backend-required notice.
"""

import argparse
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import detector  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))


def _parse_multipart(body, boundary):
    """Return {field_name: (filename, bytes)} for a multipart/form-data body."""
    fields = {}
    separator = b"--" + boundary
    for part in body.split(separator):
        if not part or part in (b"--\r\n", b"--", b"\r\n"):
            continue
        part = part.lstrip(b"\r\n")
        if part.startswith(b"--"):
            continue
        head, _, payload = part.partition(b"\r\n\r\n")
        if not _:
            continue
        payload = payload.rstrip(b"\r\n")
        disposition = ""
        for line in head.split(b"\r\n"):
            if line.lower().startswith(b"content-disposition:"):
                disposition = line.decode("utf-8", "replace")
        name = None
        filename = None
        for chunk in disposition.split(";"):
            chunk = chunk.strip()
            if chunk.startswith("name="):
                name = chunk[5:].strip('"')
            elif chunk.startswith("filename="):
                filename = chunk[9:].strip('"')
        if name:
            fields[name] = (filename, payload)
    return fields


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        # Never let a browser keep a stale copy of the page or the script:
        # an old cached app.js would still show the backend-required notice.
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/api/health":
            self._send_json({
                "status": "ok",
                "references": len(detector.load_references()),
            })
            return
        super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] != "/api/detect":
            self._send_json({"ok": False, "error": "not found"}, status=404)
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json(
                {"ok": False, "error": "bad request", "message": "Expected a photo upload."},
                status=400,
            )
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0:
            self._send_json(
                {"ok": False, "error": "empty upload", "message": "The photo did not arrive."},
                status=400,
            )
            return
        if length > detector.MAX_UPLOAD_BYTES:
            self._send_json(
                {"ok": False, "error": "too large", "message": "That photo is too large."},
                status=413,
            )
            return

        body = self.rfile.read(length)
        boundary = content_type.split("boundary=", 1)[-1].strip().strip('"').encode("utf-8")
        fields = _parse_multipart(body, boundary)

        upload = fields.get("photo") or fields.get("file")
        if not upload or not upload[1]:
            self._send_json(
                {"ok": False, "error": "empty upload", "message": "The photo did not arrive."},
                status=400,
            )
            return

        _, image_bytes = upload
        try:
            result = detector.detect_bytes(image_bytes)
        except Exception as exc:  # pragma: no cover - defensive
            self._send_json(
                {"ok": False, "error": "detector failed", "message": str(exc)},
                status=500,
            )
            return

        result["filename"] = upload[0]
        self._send_json(result)


def main():
    parser = argparse.ArgumentParser(description="Note Sense local backend")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print("Note Sense backend: http://127.0.0.1:%d/" % args.port)
    print("Detection endpoint: POST http://127.0.0.1:%d/api/detect" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
