"""Tiny test HTTP server used for quick local checks.

Run directly with Python to serve a simple health response on the
configured host and port.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler

HOST = "127.0.0.1"
PORT = 9000


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"working")


if __name__ == "__main__":
    HTTPServer((HOST, PORT), Handler).serve_forever()