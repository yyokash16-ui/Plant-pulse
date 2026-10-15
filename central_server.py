#!/usr/bin/env python3
"""PlantPulse Central Server: local multi-process API for DWSIM digital twins.

Runs independently of the legacy HX1 bridge and PlantPulse server on port 8766.
DWSIM-side adapters POST telemetry to this server; this server does not guess
DWSIM object names or claim to control a flowsheet without an adapter.
"""
from __future__ import annotations

import json
import os
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = int(os.environ.get("PLANTPULSE_CENTRAL_PORT", "8770"))
MAX_BODY = 256_000
STALE_AFTER_SECONDS = 15

PROCESS_CONFIG = {
    "hx1": {"id": "hx1", "name": "HX1 Heat Exchanger", "kind": "heat_exchanger"},
    "pumptank": {"id": "pumptank", "name": "Pump–Tank System", "kind": "pump_tank"},
}
LOCK = threading.RLock()
TELEMETRY: dict[str, dict] = {}
SETPOINTS: dict[str, dict] = {key: {} for key in PROCESS_CONFIG}
STARTED_AT = time.time()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def process_status(process_id: str) -> dict:
    with LOCK:
        payload = TELEMETRY.get(process_id)
        setpoints = dict(SETPOINTS.get(process_id, {}))
    age = None if not payload else max(0.0, time.time() - payload.get("_received_epoch", time.time()))
    connected = age is not None and age <= STALE_AFTER_SECONDS
    clean_payload = {} if not payload else {k: v for k, v in payload.items() if not k.startswith("_")}
    return {
        **PROCESS_CONFIG[process_id],
        "connected": connected,
        "telemetry_age_s": None if age is None else round(age, 2),
        "last_seen": None if not payload else payload.get("_received_at"),
        "telemetry": clean_payload,
        "setpoints": setpoints,
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def send_json(self, code: int, obj):
        body = json.dumps(obj, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:%d" % PORT)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("Invalid Content-Length")
        if length < 1 or length > MAX_BODY:
            raise ValueError("Request body must be between 1 byte and 256 KB")
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as exc:
            raise ValueError("Body must be valid UTF-8 JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:%d" % PORT)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/api/health":
            self.send_json(200, {
                "ok": True, "service": "PlantPulse Central Server",
                "listen": f"http://{HOST}:{PORT}", "legacy_bridge_required": False,
                "uptime_s": round(time.time() - STARTED_AT, 1), "time": utc_now(),
            })
            return
        if path == "/api/processes":
            self.send_json(200, {"processes": [process_status(pid) for pid in PROCESS_CONFIG]})
            return
        if path.startswith("/api/process/") and path.endswith("/telemetry"):
            pid = path.split("/")[3]
            if pid not in PROCESS_CONFIG:
                self.send_json(404, {"ok": False, "error": "Unknown process id"})
            else:
                state = process_status(pid)
                self.send_json(200, {"ok": True, **state})
            return
        # Compatibility routes for the current dashboard; they read this server's
        # own telemetry cache and do not contact the old :8765 bridge.
        if path == "/api/bridge/status":
            states = [process_status(pid) for pid in PROCESS_CONFIG]
            self.send_json(200, {"ok": True, "service": "PlantPulse Central Server",
                                 "connected_processes": [s["id"] for s in states if s["connected"]],
                                 "processes": states, "legacy_bridge_used": False})
            return
        if path == "/api/bridge/hx1":
            state = process_status("hx1")
            if not state["connected"]:
                self.send_json(503, {"ok": False, "error": "No recent HX1 telemetry received from DWSIM adapter.",
                                     "process_id": "hx1", "legacy_bridge_used": False})
            else:
                self.send_json(200, state["telemetry"])
            return
        if path == "/api/bridge/pumptank":
            state = process_status("pumptank")
            if not state["connected"]:
                self.send_json(503, {"ok": False, "error": "No recent pump-tank telemetry received from DWSIM adapter.",
                                     "process_id": "pumptank", "legacy_bridge_used": False})
            else:
                self.send_json(200, state["telemetry"])
            return
        if path.startswith("/api/"):
            self.send_json(404, {"ok": False, "error": "Unknown central API route"})
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        try:
            payload = self.read_json()
        except ValueError as exc:
            self.send_json(400, {"ok": False, "error": str(exc)})
            return

        # DWSIM adapters POST measured values here: /api/telemetry/hx1 or /api/telemetry/pumptank
        if path.startswith("/api/telemetry/"):
            pid = path.rsplit("/", 1)[-1]
            if pid not in PROCESS_CONFIG:
                self.send_json(404, {"ok": False, "error": "Unknown process id", "valid_ids": list(PROCESS_CONFIG)})
                return
            if any(isinstance(v, (dict, list)) for v in payload.values()):
                # Nested telemetry is allowed; JSON serializability was already checked.
                pass
            payload["_received_at"] = utc_now()
            payload["_received_epoch"] = time.time()
            with LOCK:
                TELEMETRY[pid] = payload
            self.send_json(200, {"ok": True, "process_id": pid, "received_at": payload["_received_at"]})
            return

        # Setpoints are queued for a DWSIM adapter to consume. They are NOT applied
        # to a simulation by this server alone.
        if path.startswith("/api/process/") and path.endswith("/setpoints"):
            pid = path.split("/")[3]
            if pid not in PROCESS_CONFIG:
                self.send_json(404, {"ok": False, "error": "Unknown process id"})
                return
            with LOCK:
                SETPOINTS[pid].update(payload)
                queued = dict(SETPOINTS[pid])
            self.send_json(202, {"ok": True, "process_id": pid, "queued": queued,
                                 "applied_to_dwsim": False,
                                 "message": "Stored locally; a DWSIM adapter must read and apply these setpoints."})
            return

        self.send_json(404, {"ok": False, "error": "Unknown central API route"})

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()


if __name__ == "__main__":
    print("\nPlantPulse Central Server")
    print(f"Dashboard/API: http://{HOST}:{PORT}")
    print("Independent of the old HX1 server and port 8765 bridge.")
    print("Local-only listener. DWSIM telemetry adapters should POST to /api/telemetry/<process_id>.")
    print("Telemetry is marked disconnected if no update arrives within %s seconds." % STALE_AFTER_SECONDS)
    print("Press Ctrl+C to stop.\n")
    threading.Timer(1.0, lambda: webbrowser.open(f"http://{HOST}:{PORT}")).start()
    try:
        ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nPlantPulse Central Server stopped.")
