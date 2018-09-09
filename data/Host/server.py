from http.server import *

class SHandler(BaseHTTPRequestHandler):
	def do_HEAD(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(bytes("OK", "utf-8"))

	def do_POST(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(bytes("OK", "utf-8"))


def run(server_class=HTTPServer, handler_class=SHandler):
	server_address = ('', 80)
	httpd = server_class(server_address, handler_class)
	httpd.serve_forever()

run()