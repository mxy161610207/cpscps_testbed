from PIL import Image
import io
import socket

# 创建一个TCP客户端套接字并连接到服务器
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("localhost", 6666))

# 接收从Unity发送的JPEG图像字节并显示图像
while True:
    # 从套接字接收数据
    data = b""
    while True:
        packet = client_socket.recv(1024)
        if not packet:
            break
        data += packet

    # 将字节数据转换为图像
    image = Image.open(io.BytesIO(data))

    # 显示图像
    image.show()
