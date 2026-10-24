#!/usr/bin/env python3
"""
webhook_alert_dispatcher.py
===========================
Automated Webhook Dispatcher for Cloud Operations & NOC Tier-1/2 Alerting.
Author: Cassiano Moura (https://cassiano-moura.github.io)

Dispatches structured, severity-calibrated incident payloads to operational channels:
- Microsoft Teams (Office 365 Connector / Adaptive Cards)
- Slack / Mattermost (Incoming Webhooks)
- Discord (NOC War Room Webhooks)
- Freshservice / PagerDuty / Opsgenie generic webhooks
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("webhook_dispatcher")


class WebhookAlertDispatcher:
    """Formats and dispatches multi-cloud incident alerts to chatops webhooks."""

    SEVERITY_COLORS = {
        "P1_CRITICAL": 0xE02424,  # Vivid Red
        "P2_HIGH": 0xFF5A1F,      # Orange
        "P3_MEDIUM": 0xE3A008,    # Amber / Yellow
        "HEALTHY": 0x0E9F6E       # Green
    }

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url

    def build_discord_slack_payload(
        self,
        target_name: str,
        cloud_provider: str,
        status: str,
        error_message: Optional[str],
        latency_ms: float,
        runbook_url: str
    ) -> Dict[str, Any]:
        """Constructs rich chatops embed with operational actionable runbook links."""
        severity_key = "P1_CRITICAL" if status == "CRITICAL" else ("P2_HIGH" if status == "DEGRADED" else "HEALTHY")
        color = self.SEVERITY_COLORS.get(severity_key, 0x718096)
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        return {
            "username": "NOC Multi-Cloud Bot",
            "avatar_url": "https://img.icons8.com/color/96/cloud-checked.png",
            "embeds": [
                {
                    "title": f"🚨 [{status}] Alert: {target_name} ({cloud_provider})",
                    "description": f"Synthetic health check failed or breached latency threshold.\n**Error:** `{error_message or 'None'}`",
                    "color": color,
                    "fields": [
                        {"name": "Cloud Provider", "value": cloud_provider, "inline": True},
                        {"name": "Status", "value": status, "inline": True},
                        {"name": "Response Latency", "value": f"{latency_ms} ms", "inline": True},
                        {"name": "Timestamp", "value": now_utc, "inline": True},
                        {"name": "Standard Operating Procedure (SOP)", "value": f"[View Runbook]({runbook_url})", "inline": False}
                    ],
                    "footer": {
                        "text": "Dedalus Cloud Operations | NOC 24/7 Monitoring Engine"
                    }
                }
            ]
        }

    def dispatch(self, payload: Dict[str, Any]) -> bool:
        """Sends payload to configured webhook. Returns True on 2xx response."""
        if not self.webhook_url:
            logger.info("[Mock Webhook] No webhook_url configured. Outputting payload to stdout.")
            print(json.dumps(payload, indent=2))
            return True

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "NOC-IncidentOps-Dispatcher/1.0"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                return 200 <= resp.status < 300
        except urllib.error.URLError as e:
            logger.error(f"Failed to dispatch webhook alert: {e}")
            return False


if __name__ == "__main__":
    dispatcher = WebhookAlertDispatcher()
    sample = dispatcher.build_discord_slack_payload(
        target_name="AWS Core Production ALB",
        cloud_provider="AWS",
        status="CRITICAL",
        error_message="HTTP 502: Bad Gateway (Backend Unhealthy)",
        latency_ms=1240.5,
        runbook_url="https://github.com/cassiano-moura/cassiano-moura.github.io/blob/main/projects/multicloud-incident-ops-center/runbooks/runbook-02-alb-target-unhealthy-502-504.md"
    )
    dispatcher.dispatch(sample)
