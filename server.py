import json
import os
import re
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

EMAILS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emails.txt")


class SubscribeHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/subscribe":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 1024:
            self._respond(400, {"error": "Request too large"})
            return

        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
            return

        email = data.get("email", "").strip().lower()
        if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            self._respond(400, {"error": "Invalid email address"})
            return

        # Check for duplicate
        if os.path.exists(EMAILS_FILE):
            with open(EMAILS_FILE, "r") as f:
                existing = {line.split(",")[0] for line in f if "," in line}
                if email in existing:
                    self._respond(200, {"message": "Already subscribed"})
                    return

        with open(EMAILS_FILE, "a") as f:
            f.write(f"{email},{datetime.utcnow().isoformat()}\n")

        self._respond(200, {"message": "Subscribed"})

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8090))
    server = HTTPServer(("127.0.0.1", port), SubscribeHandler)
    print(f"SailPrivate subscribe server running on port {port}")
    server.serve_forever()
