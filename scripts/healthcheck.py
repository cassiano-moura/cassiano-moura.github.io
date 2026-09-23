#!/usr/bin/env python3
"""
Cassiano Moura - Synthetic Uptime & Latency Monitor
Automated Cloud Observability script for cassiano-moura.github.io
Monitors HTTP Status, Latency (ms), and SSL/TLS Certificate Expiration.
"""

import os
import sys
import json
import time
import socket
import ssl
from datetime import datetime, timezone, timedelta
import urllib.request

TARGET_URL = "https://cassiano-moura.github.io/"
HOST = "cassiano-moura.github.io"
PORT = 443
METRICS_JSON_PATH = os.path.join("docs", "uptime-metrics.json")
LOG_MD_PATH = os.path.join("docs", "uptime-log.md")
MAX_HISTORY_ENTRIES = 30


def get_ssl_expiry_days(host: str, port: int = 443) -> int:
    """Connects via SSL socket and calculates remaining days until certificate expiry."""
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
            # Format: 'Jan  5 12:00:00 2027 GMT'
            not_after_str = cert["notAfter"]
            expiry_date = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            now_utc = datetime.now(timezone.utc)
            days_left = (expiry_date - now_utc).days
            return days_left


def perform_health_check():
    """Performs HTTP GET request measuring latency and status code."""
    req = urllib.request.Request(
        TARGET_URL,
        headers={"User-Agent": "CassianoMoura-SRE-SyntheticMonitor/1.0 (+https://cassiano-moura.github.io)"},
    )

    start_time = time.perf_counter()
    status_code = None
    error_msg = None

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status_code = response.getcode()
    except urllib.error.HTTPError as e:
        status_code = e.code
        error_msg = f"HTTP Error: {e.reason}"
    except Exception as e:
        status_code = 500
        error_msg = str(e)

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    ssl_days = None
    try:
        ssl_days = get_ssl_expiry_days(HOST, PORT)
    except Exception as e:
        ssl_days = -1

    now_utc = datetime.now(timezone.utc)
    # Brasilia Time is UTC-3
    brt_tz = timezone(timedelta(hours=-3))
    now_brt = now_utc.astimezone(brt_tz)

    check_result = {
        "timestamp_utc": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "timestamp_brt": now_brt.strftime("%d/%m/%Y %H:%M:%S BRT"),
        "target_url": TARGET_URL,
        "status_code": status_code,
        "status_text": "OPERATIONAL" if status_code == 200 else "DEGRADED",
        "latency_ms": latency_ms,
        "ssl_days_remaining": ssl_days,
        "error": error_msg,
    }

    return check_result


def update_metrics(result):
    """Updates metrics JSON and Markdown log file."""
    os.makedirs("docs", exist_ok=True)

    # 1. Load or initialize history
    history = []
    if os.path.exists(METRICS_JSON_PATH):
        try:
            with open(METRICS_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                history = data.get("history", [])
        except Exception:
            history = []

    # Prepend latest check
    history.insert(0, result)
    history = history[:MAX_HISTORY_ENTRIES]

    # Save JSON
    metrics_payload = {
        "last_check": result,
        "summary": {
            "uptime_target": "99.9%",
            "monitored_endpoint": TARGET_URL,
            "total_checks_recorded": len(history),
        },
        "history": history,
    }

    with open(METRICS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2, ensure_ascii=False)

    # 2. Render Markdown Log
    status_icon = "🟢" if result["status_code"] == 200 else "🔴"
    ssl_icon = "🔒" if (result["ssl_days_remaining"] or 0) > 15 else "⚠️"

    md_lines = [
        "# 📡 SRE Synthetic Monitoring & Uptime Report",
        "",
        "> Automated health check pipeline orchestrated via **GitHub Actions**.",
        "> Validates HTTP response codes, round-trip latency, and SSL/TLS certificate validity for [cassiano-moura.github.io](https://cassiano-moura.github.io/).",
        "",
        "## 📊 Current Service Status",
        "",
        "| Metric | Value | Status |",
        "| :--- | :--- | :--- |",
        f"| **Service Status** | `{result['status_text']}` | {status_icon} |",
        f"| **HTTP Status Code** | `{result['status_code']}` | {'OK' if result['status_code'] == 200 else 'ALERT'} |",
        f"| **Response Latency** | `{result['latency_ms']} ms` | {'Optimal' if result['latency_ms'] < 1000 else 'Elevated'} |",
        f"| **SSL Certificate Expiry** | `{result['ssl_days_remaining']} days remaining` | {ssl_icon} |",
        f"| **Last Inspection** | `{result['timestamp_brt']}` (`{result['timestamp_utc']}`) | Checked |",
        "",
        "---",
        "",
        "## 📜 Historical Execution Log (Last 30 Runs)",
        "",
        "| Date / Time (BRT) | Status | Code | Latency | SSL Remaining |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ]

    for item in history:
        icon = "🟢" if item["status_code"] == 200 else "🔴"
        md_lines.append(
            f"| {item['timestamp_brt']} | {icon} `{item['status_text']}` | `{item['status_code']}` | `{item['latency_ms']} ms` | `{item.get('ssl_days_remaining', 'N/A')} days` |"
        )

    md_lines.extend([
        "",
        "---",
        "*Report auto-generated by `scripts/healthcheck.py` running in GitHub Actions CI/CD runner.*",
    ])

    with open(LOG_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(f"Health check complete: {result['status_text']} ({result['status_code']}) in {result['latency_ms']}ms. SSL valid for {result['ssl_days_remaining']} days.")


if __name__ == "__main__":
    result = perform_health_check()
    update_metrics(result)
