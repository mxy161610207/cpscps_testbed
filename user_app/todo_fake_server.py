import socket

class FakeServer:
    def __init__(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = '127.0.0.1'
        port = 18080
        self.server_socket.bind((host, port))   
        self.server_socket.listen(10)

    def run(self):
        con,addr = self.server_socket.accept()
        while True:
            try:
                # 接受套接字的大小，怎么发就怎么收
                msg = con.recv(1024)
                if msg.decode('utf-8') == 'EXIT':
                    # 断开连接
                    con.close()
                print('服务器收到消息',msg.decode('utf-8'))
            except Exception as e:
                break


if __name__=='__main__':
    server = FakeServer()
    server.run()