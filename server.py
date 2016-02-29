import config
from http.server import BaseHTTPRequestHandler, HTTPServer


class HTTPHandler(BaseHTTPRequestHandler):
    def echo(self, text):
        self.wfile.write(bytes(text, "utf-8"))

    def do_POST(self):
        print('POST processing...\n')

    def do_GET(self):
        self.send_response(200, 'OK')
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.echo('Don\'t worry, the server is running!')


class Server(HTTPServer):
    def __init__(self):
        HTTPServer.__init__(self, (config.hostname, config.port), HTTPHandler)
        self.run()

    def run(self):
        try:
            print('HTTP server is started.\nPress Ctrl+C to stop and exit.')
            self.serve_forever()
        except KeyboardInterrupt:
            print("\nHTTP server is stopped.")
