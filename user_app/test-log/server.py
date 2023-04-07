import socket
import json

act = ""
size=0
def handle_message(message):
    global act,size
    if act!="":
        if act == 'print':
            print(message)
        elif act == 'file':
            with open('./a.py', 'wb') as f:
                print("open success!")
                f.write(message)
        act=""
        size=0
    elif message == 'end':
        print('Server shutting down...')
        exit()
    else:
        l =str(message.decode('utf-8')).split(" ")
        act,size=l[0],l[1]
        size=int(size)
        print("wait",act,size)


def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('127.0.0.1', 1998))
        print('Server is running...')
        while True:
            if (act!="" and size!=0):
                data, addr = s.recvfrom(size)
            else:
                data, addr = s.recvfrom(1024)

            # print(message)
            handle_message(data)

if __name__ == '__main__':
    run_server()


