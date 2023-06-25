import socket
import threading

class JavaCommunicationHelper:
    def __init__(self,updater):
        self.sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = '127.0.0.1'
        port = 18080
        self.sender.connect((host, port))    # 发指令"SAFE: chassis"
        self._updater=updater

        self._recv_thread=threading.Thread(target=self._update_thread)
        self._recv_thread.start()


    def put_msg(self, msg: str):
        print("mxy Log",msg)
        self.sender.send(f'{msg}\n'.encode('utf8'))

    def _update_thread(self):
        while True:
            packet = self.sender.recv(1024)
            if not packet:
                break
            
            packet = packet.decode('utf8')
            print(packet)
            self._updater.update(packet)