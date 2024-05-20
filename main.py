import json
import mimetypes
import pathlib
import socket
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

HOST = ''
PORT_WEB = 3000
PORT_SOCKET = 5000
# Отримання базового шляху до директорії, де знаходиться скрипт
BASE_DIR = pathlib.Path(__file__).resolve().parent
# Шлях до файлу збереження даних у директорії storage
STORAGE_PATH = BASE_DIR / 'storage' / 'data.json'
# Створюємо директорію storage, якщо вона не існує
STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.parse_qs(data.decode())
        print(data_parse)
        timestamp = datetime.now().isoformat(sep=' ', timespec='microseconds')
        username = data_parse.get('username', [''])[0].strip()
        message = data_parse.get('message', [''])[0].strip()

        if not username or not message:
            self.send_response(400)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            response = """
                        <html>
                        <body>
                        <h1>Both fields are required!</h1>
                        <p>Fields Your Nikname and Message are required</p>
                        <a href="/message">Go back to the message form</a>
                        </body>
                        </html>
                        """
            self.wfile.write(response.encode('utf-8'))
            return

        data_dict = {timestamp: {'username': username, 'message': message}}
        print(data_dict)
        print(json.dumps(data_dict).encode())

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(json.dumps(data_dict).encode(), ((HOST, PORT_SOCKET)))
        sock.close()

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run_socket_server():
    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    server_socket.bind((HOST, PORT_SOCKET))
    print(f'Socket server is running on port {PORT_SOCKET}')

    while True:
        # Wait for a connection
        print('Waiting for a connection')
        try:
            data, client_address = server_socket.recvfrom(1024)
            message = json.loads(data.decode())
            print('Connection from', client_address)
            print('Received', repr(data))

            if STORAGE_PATH.exists():
                with STORAGE_PATH.open('r') as file:
                    try:
                        storage_data = json.load(file)
                    except json.JSONDecodeError as js_err:
                        print(js_err)
                        storage_data = {}
            else:
                storage_data = {}
            storage_data.update(message)

            with STORAGE_PATH.open('w') as file:
                json.dump(storage_data, file, indent=2)

        except Exception as e:
            print('Errror', e)


def run_web_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = (HOST, PORT_WEB)
    http = server_class(server_address, handler_class)
    try:
        print(f'Server is running at http://localhost:{PORT_WEB}')
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    web_server_thread = threading.Thread(target=run_web_server)
    socket_server_thread = threading.Thread(target=run_socket_server)

    web_server_thread.start()
    socket_server_thread.start()

    web_server_thread.join()
    socket_server_thread.join()
