#!/usr/bin/env python3
"""Local-only PlantPulse server and safe proxy for the existing DWSIM HX1 bridge."""
from __future__ import annotations
import json, os, threading, time, urllib.error, urllib.request, webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = int(os.environ.get("PLANTPULSE_PORT", "8766"))
BRIDGE_URL = os.environ.get("DWSIM_BRIDGE_URL", "http://127.0.0.1:8765").rstrip("/")
ALLOWED_BRIDGE_HOSTS = {"127.0.0.1", "localhost", "::1"}

def bridge_request(path: str, method: str = "GET", payload=None):
    parsed = urlparse(BRIDGE_URL)
    if parsed.scheme != "http" or parsed.hostname not in ALLOWED_BRIDGE_HOSTS:
        raise ValueError("Bridge must be an HTTP loopback URL; remote bridge hosts are blocked.")
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BRIDGE_URL + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            raw = resp.read(2_000_000).decode("utf-8", errors="replace")
            try: parsed_body = json.loads(raw)
            except json.JSONDecodeError: parsed_body = {"raw": raw}
            return resp.status, parsed_body
    except urllib.error.HTTPError as e:
        raw = e.read(200_000).decode("utf-8", errors="replace")
        try: body = json.loads(raw)
        except json.JSONDecodeError: body = {"raw": raw}
        return e.code, body
    except Exception as e:
        raise ConnectionError(f"Cannot reach DWSIM bridge at {BRIDGE_URL}: {e}") from e

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))
    def send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self.send_json(200, {"ok": True, "service": "PlantPulse", "listen": f"http://{HOST}:{PORT}",
                                 "bridge_url": BRIDGE_URL, "bridge_host_restricted": True,
                                 "time": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
            return
        routes = {"/api/bridge/status": "/api/status", "/api/bridge/hx1": "/api/hx1"}
        if path in routes:
            try:
                code, data = bridge_request(routes[path])
                self.send_json(code, data)
            except Exception as e:
                self.send_json(503, {"ok": False, "error": str(e), "bridge_url": BRIDGE_URL})
            return
        if path.startswith("/api/"):
            self.send_json(404, {"error": "Unknown PlantPulse API route"})
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()
    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/bridge/hx1/set":
            self.send_json(404, {"error": "Unknown PlantPulse API route"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 64_000:
            self.send_json(400, {"error": "Request body must be between 1 byte and 64 KB"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self.send_json(400, {"error": "Body must be valid JSON"})
            return
        if not isinstance(payload, dict):
            self.send_json(400, {"error": "Expected a JSON object"})
            return
        try:
            code, data = bridge_request("/api/hx1/set", "POST", payload)
            self.send_json(code, {"bridge_status": code, "response": data})
        except Exception as e:
            self.send_json(503, {"ok": False, "error": str(e)})
    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

if __name__ == "__main__":
    print("\nPlantPulse local DWSIM dashboard")
    print(f"Open: http://{HOST}:{PORT}")
    print(f"Existing DWSIM bridge: {BRIDGE_URL}")
    print("Local-only listener. Keep DWSIM open and start your existing HX1 bridge.")
    print("Opening the dashboard in your default browser. Press Ctrl+C to stop.\\n")
    threading.Timer(1.0, lambda: webbrowser.open(f"http://{HOST}:{PORT}")).start()
    try:
        ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nPlantPulse stopped.")
