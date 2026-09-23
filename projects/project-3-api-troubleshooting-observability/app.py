"""
==============================================================================
Microservice API with Structured JSON Logging
Author: Cassiano Moura
Technologies: Python, Docker, Structured Logging
==============================================================================
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
import uuid

class StructuredLogAPIHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Override default server logging to avoid duplicate plain text logs
        pass

    def emit_structured_log(self, status_code, endpoint, error_message=None):
        log_payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": str(uuid.uuid4()),
            "service": "order-management-microservice",
            "method": self.command,
            "endpoint": endpoint,
            "status_code": status_code,
            "client_ip": self.client_address[0],
            "error_message": error_message,
            "tier": "Production-API"
        }
        print(json.dumps(log_payload), flush=True)

    def do_GET(self):
        if self.path == "/api/v1/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "order-management"}')
            self.emit_structured_log(200, self.path)

        elif self.path == "/api/v1/orders":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'[{"order_id": 101, "total": 250.0}, {"order_id": 102, "total": 980.5}]')
            self.emit_structured_log(200, self.path)

        elif self.path == "/api/v1/secure/data":
            # 401 Unauthorized Simulation
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Unauthorized", "message": "Missing Authorization Bearer header"}')
            self.emit_structured_log(401, self.path, "Missing Bearer Token in Entra ID Header")

        elif self.path == "/api/v1/system/crash-simulation":
            # 500 Internal Server Error Simulation
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "InternalServerError", "message": "Null pointer in payment gateway adapter"}')
            self.emit_structured_log(500, self.path, "NullPointerException in PaymentGatewayAdapter.connect()")

        elif self.path == "/api/v1/checkout/timeout-simulation":
            # 504 Gateway Timeout Simulation
            time.sleep(1.5)
            self.send_response(504)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "GatewayTimeout", "message": "Downstream database query exceeded timeout threshold"}')
            self.emit_structured_log(504, self.path, "Downstream MySQL query on orders table exceeded timeout")

        else:
            # 404 Not Found
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "NotFound", "message": "Endpoint does not exist"}')
            self.emit_structured_log(404, self.path, "Endpoint route not registered")

    def do_POST(self):
        if self.path == "/api/v1/orders":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body) if body else {}
                if "customer_id" not in data:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"error": "BadRequest", "message": "customer_id is a mandatory field"}')
                    self.emit_structured_log(400, self.path, "Missing required payload field: customer_id")
                    return

                self.send_response(201)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"order_id": 103, "status": "created"}')
                self.emit_structured_log(201, self.path)

            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "InvalidJson", "message": "Malformed JSON payload"}')
                self.emit_structured_log(400, self.path, "Malformed JSON syntax")


if __name__ == "__main__":
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, StructuredLogAPIHandler)
    print("API Microservice running on port 8080 with JSON structured logging active...", flush=True)
    httpd.serve_forever()
