import config
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer


class Server(HTTPServer):
    def __init__(self, queue):
        class HTTPHandler(BaseHTTPRequestHandler):
            def echo(self, text):
                self.wfile.write(bytes(text, "utf-8"))

            def do_POST(self):
                uid = queue.get()
                print('POST processing...\n')
                length = int(self.headers.get('content-length'))
                field_data = self.rfile.read(length)
                fields = parse_qs(field_data)
                queue.put((uid, fields))

            def do_GET(self):
                self.send_response(200, 'OK')
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.echo('Don\'t worry, the server is running!')

        HTTPServer.__init__(self, (config.hostname, config.port), HTTPHandler)
        self.run()

    def run(self):
        try:
            print('HTTP server is started.\nPress Ctrl+C to stop and exit.')
            self.serve_forever()
        except KeyboardInterrupt:
            print("\nHTTP server is stopped.")
