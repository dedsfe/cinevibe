#!/usr/bin/env python3
"""
Lightweight health/metrics monitor for the scraping stack.
Does not touch existing scrapers; runs as a separate service.
"""

import os
import json
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

ROOT = Path(__file__).resolve().parent.parent
LOG_SCRAPER = ROOT / "backend" / "scraper_run.log"
API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("API_PORT", "3000"))


def is_port_open(host, port, timeout=1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def pid_running(process_name: str) -> bool:
    try:
        out = subprocess.check_output(["pgrep", "-f", process_name])
        return len(out.strip()) > 0
    except Exception:
        return False


def recent_saves_window(minutes: int = 60) -> int:
    if not LOG_SCRAPER.exists():
        return 0
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    count = 0
    with open(LOG_SCRAPER, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "SAVED:" in line:
                ts = line[:19]
                try:
                    dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    dt = datetime.utcnow()
                if dt >= cutoff:
                    count += 1
    return count


def last_save_time() -> str | None:
    if not LOG_SCRAPER.exists():
        return None
    last = None
    with open(LOG_SCRAPER, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "SAVED:" in line:
                last = line[:19]
    return last


class Handler(BaseHTTPRequestHandler):
    def _json(self, payload, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))

    def do_GET(self):
        if self.path in ("/health", "/healthz"):
            self.do_health()
        elif self.path in ("/metrics", "/metrics.json"):
            self.do_metrics()
        else:
            self.send_error(404, "Not Found")

    def do_health(self):
        api_up = is_port_open(API_HOST, API_PORT)
        health = {
            "status": "up" if api_up else "degraded",
            "api": {"host": API_HOST, "port": API_PORT, "reachable": api_up},
            "daemons": {
                "poster_daemon": pid_running("poster_daemon.py"),
                "vpn_scraper": pid_running("scraper_vpn.py"),
            },
        }
        self._json(health)

    def do_metrics(self):
        metrics = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "api": {"host": API_HOST, "port": API_PORT},
            "daemons": {
                "poster_daemon": {"running": pid_running("poster_daemon.py")},
                "vpn_scraper": {"running": pid_running("scraper_vpn.py")},
            },
            "scraper": {
                "recent_saves_last_min": recent_saves_window(1),
                "last_save_time": last_save_time(),
            },
        }
        self._json(metrics)


def run():
    port = int(os.environ.get("MONITOR_PORT", 8080))
    httpd = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Monitor server running on port {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
