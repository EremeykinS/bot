import config
from urllib.parse import parse_qs, urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from yandex_money.api import Wallet, ExternalPayment
import sqlite3


class Server(HTTPServer):
    def __init__(self, queue):
        class HTTPHandler(BaseHTTPRequestHandler):
            # def echo(self, text):
            #     self.wfile.write(bytes(text, "utf-8"))

            # def do_POST(self):
            #     uid = queue.get()
            #     print('POST processing...\n')
            #     length = int(self.headers.get('content-length'))
            #     field_data = self.rfile.read(length)
            #     fields = parse_qs(field_data)
            #     queue.put((uid, fields))

            def do_GET(self):
                #DB connection
                con = sqlite3.connect('/home/user/bot/users.sqlite')
                cur = con.cursor()
                p = urlparse(self.path)
                q = parse_qs(p.query)
                self.send_response(302, 'Found')
                if 'cid' in q:
                    scope = ['account-info', 'operation-history', 'payment-p2p']
                    auth_url = Wallet.build_obtain_token_url(config.client_id, config.redirect_uri, scope)
                    self.send_header('Location', auth_url)
                    if 'b' in q:
                        self.send_header("Set-Cookie", "cid=" + q['cid'][0] + '&b=1')
                    else:
                        self.send_header("Set-Cookie", "cid=" + q['cid'][0] + '&to=' + q['to'][0] + '&amount=' + q['amount'][0])
                elif 'code' in q:
                    access_token = Wallet.get_access_token(config.client_id, q['code'][0], config.redirect_uri, client_secret=None)
                    cookie = parse_qs(self.headers.get('Cookie'))
                    cid = cookie['cid'][0]
                    cur.execute('INSERT INTO users (cid, token) VALUES ("' + str(cid) +'", "' + access_token['access_token'] + '")')
                    con.commit()
                    wallet = Wallet(access_token['access_token'])
                    if 'b' in cookie:
                        queue.put({'cid': cid, 'b': wallet.account_info()['balance_details']['available']})
                    else:
                        to = cookie['to'][0]
                        amount = cookie['amount'][0]
                        request_options = {"pattern_id": "p2p", "to": to, "amount_due": amount, "comment": "переведено через бота", "message": "переведено через бота", "label": "testPayment"}
                        request_result = wallet.request_payment(request_options)
                        # check status
                        process_payment = wallet.process_payment({"request_id": request_result['request_id'],})
                        # check result
                        if process_payment['status'] == "success":
                            queue.put({'cid': cid, 'result':'+'})
                        else:
                            queue.put({'cid': cid, 'result':'-'})
                    self.send_header('Location', 'http://telegram.me/GodMoneyBot')
                self.end_headers()
                con.close()

        HTTPServer.__init__(self, (config.hostname, config.port), HTTPHandler)
        self.run()

    def run(self):
        try:
            print('HTTP server is started.\nPress Ctrl+C to stop and exit.')
            self.serve_forever()
        except KeyboardInterrupt:
            print("\nHTTP server is stopped.")
