from http.server import *

def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', 80)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

run()