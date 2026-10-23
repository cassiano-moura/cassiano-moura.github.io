"""
Unit tests for MultiCloudHealthEngine (NOC Incident & Operations Center).
Validates multi-cloud probe logic, HTTP status parsing, latency thresholds, and socket fallbacks.
"""

import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import urllib.request
import os
import sys

# Add scripts directory to path to import engine
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from multicloud_healthcheck import MultiCloudHealthEngine, ProbeResult


class TestMultiCloudHealthEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MultiCloudHealthEngine(timeout_seconds=2.0, latency_threshold_ms=500.0)

    @patch("urllib.request.urlopen")
    def test_probe_http_healthy_200(self, mock_urlopen):
        """Tests that a 200 OK HTTP response within latency budget registers as HEALTHY."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = self.engine.probe_http(
            target_name="AWS Production API Gateway",
            cloud="AWS",
            url="https://api.aws-demo.example.com/healthz"
        )

        self.assertEqual(result.status, "HEALTHY")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.cloud_provider, "AWS")
        self.assertIsNone(result.error_message)

    @patch("urllib.request.urlopen")
    def test_probe_http_critical_502_bad_gateway(self, mock_urlopen):
        """Tests that a 502 Bad Gateway registers as CRITICAL for NOC intervention."""
        http_error = urllib.error.HTTPError(
            url="https://app.azure-demo.example.com/status",
            code=502,
            msg="Bad Gateway",
            hdrs={},
            fp=None
        )
        mock_urlopen.side_effect = http_error

        result = self.engine.probe_http(
            target_name="Azure Core App Gateway",
            cloud="Azure",
            url="https://app.azure-demo.example.com/status"
        )

        self.assertEqual(result.status, "CRITICAL")
        self.assertEqual(result.status_code, 502)
        self.assertIn("HTTP 502: Bad Gateway", result.error_message)

    @patch("urllib.request.urlopen")
    def test_probe_http_timeout_triggers_critical(self, mock_urlopen):
        """Tests that a connection timeout triggers a CRITICAL status."""
        mock_urlopen.side_effect = TimeoutError("Connection timed out")

        result = self.engine.probe_http(
            target_name="OCI Edge Load Balancer",
            cloud="OCI",
            url="https://oci-edge.example.com/health"
        )

        self.assertEqual(result.status, "CRITICAL")
        self.assertIsNone(result.status_code)
        self.assertIn("TimeoutError", result.error_message)

    @patch("socket.socket")
    def test_probe_tcp_socket_healthy(self, mock_socket_class):
        """Tests TCP socket connection for DB ports (e.g. MySQL 3306)."""
        mock_socket_instance = MagicMock()
        mock_socket_class.return_value = mock_socket_instance
        # connect succeeds without exception
        mock_socket_instance.connect.return_value = None

        result = self.engine.probe_tcp_socket(
            target_name="AWS RDS Multi-AZ Primary",
            cloud="AWS",
            host="rds-mysql-prod.internal",
            port=3306
        )

        self.assertEqual(result.status, "HEALTHY")
        self.assertEqual(result.target_type, "TCP_PORT")
        self.assertEqual(result.endpoint, "rds-mysql-prod.internal:3306")
        self.assertIsNone(result.error_message)

    @patch("socket.socket")
    def test_probe_tcp_socket_refused(self, mock_socket_class):
        """Tests TCP socket connection failure triggers CRITICAL."""
        mock_socket_instance = MagicMock()
        mock_socket_class.return_value = mock_socket_instance
        mock_socket_instance.connect.side_effect = ConnectionRefusedError("Connection refused")

        result = self.engine.probe_tcp_socket(
            target_name="OCI Autonomous DB Listener",
            cloud="OCI",
            host="adb-listener.internal",
            port=1521
        )

        self.assertEqual(result.status, "CRITICAL")
        self.assertIn("ConnectionRefused/Timeout", result.error_message)


if __name__ == "__main__":
    unittest.main()
