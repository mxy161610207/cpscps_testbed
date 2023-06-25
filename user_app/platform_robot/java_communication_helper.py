import socket


class JavaCommunicationHelper:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = '127.0.0.1'
        port = 8080
        self.s.connect((host, port))

    def put_msg(self, msg: str):
        self.s.send(f'{msg}\n'.encode('utf8'))

    def get_msg(self) -> str:
        return self.s.recv(1024).decode('utf8').strip()
