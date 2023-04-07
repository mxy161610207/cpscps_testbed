import tkinter as tk
import socket
import threading
from PIL import ImageTk, Image
import io

# 创建TCP Socket
car_camera_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
car_camera_socket.connect(('localhost', 6665))

main_camera_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
main_camera_socket.connect(('localhost', 6666))

# 创建UDP Socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind(('localhost', 6667))

class DoubleBufferedCanvas(tk.Canvas):
    def __init__(self, master=None, **kw):
        super().__init__(master=master, **kw)
        self._buffer = tk.Canvas(self, width=self['width'], height=self['height'])
        self._buffer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._current_image = None

    def create_image(self, *args, **kw):
        return self._buffer.create_image(*args, **kw)

    def update_image(self, image):
        self._current_image = image
        self._buffer.delete(tk.ALL)
        self._buffer.create_image(0, 0, anchor=tk.NW, image=image)
        self.update_idletasks()

    def clear(self):
        self._current_image = None
        self._buffer.delete(tk.ALL)
        self.update_idletasks()

# 创建GUI窗口
root = tk.Tk()
root.title('图像播放器')

# 创建画布和图像
canvas_main = DoubleBufferedCanvas(root, width=300, height=300)
canvas_car = DoubleBufferedCanvas(root, width=300, height=300)

canvas_main.grid(row=0, column=0, padx=10, pady=10)
canvas_car.grid(row=0, column=1, padx=10, pady=10)

# 创建文本框
text = tk.Text(root, height=5)
text.grid(row=1, column=0, columnspan=2, padx=10, pady=10)


img = None
img_tk = None

# 更新图像
def update_image():
    global img, img_tk
    while True:
        # 从TCP Socket接收图像数据
        data_main = main_camera_socket.recv(30000)
        data_car = car_camera_socket.recv(30000)
        if data_main:
            # 用PIL库打开图像
            img = Image.open(io.BytesIO(data_main))
            # 将图像转换为Tkinter PhotoImage
            img_tk = ImageTk.PhotoImage(img)
            # 在画布上显示图像
            canvas_main.update_image(image=img_tk)
        else:
            break
        if data_car:
            # 用PIL库打开图像
            img = Image.open(io.BytesIO(data_car))
            # 将图像转换为Tkinter PhotoImage
            img_tk = ImageTk.PhotoImage(img)
            # 在画布上显示图像
            canvas_car.update_image(image=img_tk)
        else:
            break

    main_camera_socket.close()
    car_camera_socket.close()

# 创建线程，用于更新图像
threading.Thread(target=update_image, daemon=True).start()

# 更新文本框
def update_text():
    while True:
        # 从UDP Socket接收消息
        data, addr = udp_socket.recvfrom(1024)
        # 在文本框中显示消息
        text.insert(tk.END, f"{data.decode()} from {addr[0]}:{addr[1]}\n")
        text.see(tk.END)
    udp_socket.close()

# 创建线程，用于更新文本框
threading.Thread(target=update_text, daemon=True).start()

root.mainloop()
