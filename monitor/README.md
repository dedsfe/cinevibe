Monitor Service
===============
A lightweight health/metrics monitor for the scraping stack. Runs separately from the scrapers to avoid any risk of breaking existing code.

What it does
- Exposes /health to check basic availability of the API and daemons.
- Exposes /metrics to surface lightweight runtime metrics (daemon status, recent saves, etc.).

How to run
- Install environment (Python 3.x assumed): nothing extra required for this minimal version.
- Start monitor: python3 monitor/monitor_server.py
- Optional: run on a different port via MONITOR_PORT env var, e.g., MONITOR_PORT=8080 python3 monitor/monitor_server.py

Health checks
- curl http://127.0.0.1:8080/health
- curl http://127.0.0.1:8080/metrics

Notes
- This monitor does not touch the scrapers; it reads their logs and checks process presence for basic health signals.
- It is safe to run alongside the existing scrapers without risk of breaking them.
