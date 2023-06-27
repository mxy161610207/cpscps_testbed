import socket
import threading

class JavaCommunicationHelper:
    def __init__(self,updater):
        self.sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = '127.0.0.1'
        port = 18888
        self.sender.connect((host, port))    # 发指令"SAFE: chassis"
        self._updater=updater

        self._log_file = open("conn_app_log.txt","w")

        self._recv_thread=threading.Thread(target=self._update_thread)
        self._recv_thread.daemon=True
        self._recv_thread.start()

    def __del__(self):
        self._log_file.close()

    def put_msg(self, msg: str):
        print("[Log] [APP -> PT] send",msg)
        print(f"[APP->PT->DRIVER]:{msg}",file=self._log_file)
        self.sender.send(f'{msg}\n'.encode('utf8'))

    def _update_thread(self):
        while True:
            packet = self.sender.recv(1024)
            if not packet:
                break
            
            packet = packet.decode('utf8')
            print(f"[DRIVER->PT->APP]:{packet.strip()}",file=self._log_file)
            # print("[Log] [PT->APP] recv",packet)
            self._updater.update(packet)