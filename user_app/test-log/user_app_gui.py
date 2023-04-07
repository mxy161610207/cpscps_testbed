import tkinter as tk
import socket
import json
import time
import random
import math
import threading
import numpy as np
from tkinter import filedialog,messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from PIL import ImageTk, Image
import matplotlib.pyplot as plt
import io

class DoubleBufferedCanvas(tk.Canvas):
    def __init__(self, master=None, **kw):
        super().__init__(master=master, **kw)
        self._buffer = tk.Canvas(self, width=self['width'], height=self['height'],bg='black')
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

class FileLoadModule:
    def __init__(self,port, master,file_type,cur_row):
        self.master = master
        self.file_type = file_type
        self.file_suffix = ".py" if file_type=="决策程序" else ".txt"
        self.sendto_addr = ('localhost',port)

        self.file_label = tk.Label(master, text="{}:".format(file_type))
        self.file_entry = tk.Entry(master, width=50)
        self.browse_button = tk.Button( 
            master, text="选择", width=10, command = self.browse_file)
        self.transfer_button = tk.Button(
            master, text="上传", width=10,command=self.transfer_file)
        
        self.file_label.grid(row=cur_row, column=0)
        self.file_entry.grid(row=cur_row, column=1, columnspan= 3)
        self.browse_button.grid(row=cur_row, column=4,padx=10,pady=10)
        self.transfer_button.grid(row=cur_row, column=5,padx=10,pady=10)
        
    def browse_file(self):
        # open a file dialog to select a file
        file_path = filedialog.askopenfilename(initialdir=".")
        # set the file path entry to the selected file path
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, file_path)

    def transfer_file(self):
        # get the local file path and remote host and port from the GUI widgets
        local_file_path = self.file_entry.get()

        if not local_file_path.endswith(self.file_suffix):
            messagebox.showinfo("提示框", "[{}]文件必须以[{}]结尾!".
                                format(self.file_type,self.file_suffix))
            return

        
        # open the local file and read its contents
        with open(local_file_path, 'rb') as f:
            file_contents = f.read()

        # create a socket and connect to the remote host and port
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = "file"+" "+str(len(file_contents))
        s.sendto(data.encode('utf-8'), self.sendto_addr)
        s.sendto(file_contents, self.sendto_addr)

        # close the socket
        s.close()

        # show a message box to indicate success
        messagebox.showinfo("提示框", "[{}]文件传输成功!".format(self.file_type))

class CanvasUpdateModule:
    pop_messagebox = False
    def __init__(self, port, canvas):
        self.canvas = canvas
        self.camera_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_addr = ('localhost', port)

        self.update_thread = threading.Thread(target=self.update_thread_main, daemon=True)
        self.update_thread.start()

        self.img = None
        self.img_tk = None

    def update_thread_main(self):
        self.server_is_online = True
        try:
            # 可能会发生异常的代码块
            self.camera_socket.connect(self.server_addr)
        except:
            self.server_is_online = False
            if not CanvasUpdateModule.pop_messagebox:
                CanvasUpdateModule.pop_messagebox=True
                messagebox.showinfo("提示框", "等待服务器开机!")
        else:
            self.server_is_online = True

        while True:
            if (not self.server_is_online):
                time.sleep(1)
                try:
                    # 可能会发生异常的代码块
                    self.camera_socket.connect(self.server_addr)
                except:
                    self.server_is_online = False
                    continue
                else:
                    self.server_is_online = True

            # 从TCP Socket接收图像数据
            data = self.camera_socket.recv(30000)
            if data:
                # 用PIL库打开图像
                self.img = Image.open(io.BytesIO(data))
                # 将图像转换为Tkinter PhotoImage
                self.img_tk = ImageTk.PhotoImage(self.img)
                # 在画布上显示图像
                self.canvas.update_image(image=self.img_tk)
            else:
                break

        self.canvas.clear()
        self.camera_socket.close()

class TextUpdateModule:
    def __init__(self, port, text):
        self.text = text
        self.text_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.text_socket.bind(("localhost",port))

        self.update_thread = threading.Thread(target=self.update_thread_main, daemon=True)
        self.update_thread.start()

    def update_thread_main(self):
        while True:
        # 从UDP Socket接收消息
            data, addr = self.text_socket.recvfrom(1024)
            # 在文本框中显示消息
            self.text.insert(tk.END, f"{data.decode()} from {addr[0]}:{addr[1]}\n")
            self.text.see(tk.END)


class AnimationUpdateModule:
    def __init__(self, port, canvas, fig):
        self.canvas = canvas        
        self.fig = fig
        self.E = 2400

        self.ax = self.fig.add_subplot(111, aspect='equal',
            autoscale_on=False, xlim=[-self.E/2.0, self.E/2.0], ylim=[-self.E/2.0, self.E/2.0])
        self.scatter = None
        self.arrow = None

        self.draw_basic_place()
        # self.draw_axes()
        # self.draw_square()

        self.canvas_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.canvas_socket.bind(('localhost', port))

        self.update_thread = threading.Thread(target=self.update_thread_main, daemon=True)
        self.update_thread.start()

    def draw_basic_place(self):
        self.ax.set_xlabel("x")
        self.ax.set_xlabel("y")
        self.ax.set_aspect('equal')
        self.ax.set_xlim([-self.E/2.0, self.E/2.0])
        self.ax.set_ylim([-self.E/2.0, self.E/2.0])

    def draw_car_symbol(self, position_info,aw_len=100):
        x,y,rad = position_info['x'],position_info['y'],position_info['rad']

        '''
        draw (scatter, arrow) to show a car's position
        '''

        dx = aw_len*math.cos(rad)
        dy = aw_len*math.sin(rad)

        if (not self.arrow is None):
            self.arrow.remove()
            self.arrow=None

        if (not self.scatter is None):
            self.scatter.remove()
            self.scatter=None
            
        self.scatter = self.ax.scatter([x], [y],s=50,c='blue',marker='o',alpha=0.5)
        self.arrow = self.ax.arrow(x,y,dx,dy,color='k',width=1)

        self.canvas.draw()
        
        print(1)

    def update_thread_main(self):
        while True:
            # data, addr = self.canvas_socket.recvfrom(1024)
            # positon = json.loads(data.decode())['position']
   
            time.sleep(1)
            positon = {
                'x':random.random()*self.E- self.E/2,
                'y':random.random()*self.E- self.E/2,
                'rad': math.radians(random.randint(0,360))
            }

            print(positon)
            self.draw_car_symbol(positon)

class FileTransferGUI:
    def __init__(self, master):
        self.master = master
        master.title("用户程序")

        cur_row = 0
        canvas_size=3
        
        label = tk.Label(master, text="虚拟场景-俯视图")
        label.grid(row=cur_row, column=0,columnspan= canvas_size,pady=10)
        label = tk.Label(master, text="虚拟场景-相机数据")
        label.grid(row=cur_row, column=canvas_size,columnspan= canvas_size,pady=10)
        label = tk.Label(master, text="物理场景-定位结果数据")
        label.grid(row=cur_row, column=canvas_size*2,columnspan= canvas_size,pady=10)
        cur_row +=1

        # 创建画布和图像 3*3 | 3*3 | 3*3
        self.canvas_main = DoubleBufferedCanvas(master, width=300, height=300)
        self.canvas_main_module = CanvasUpdateModule(6666,self.canvas_main)
        self.canvas_car = DoubleBufferedCanvas(master, width=300, height=300)
        self.canvas_car_module = CanvasUpdateModule(6665,self.canvas_car)

        self.canvas_sdk_fig = plt.Figure()
        self.canvas_sdk = FigureCanvasTkAgg(self.canvas_sdk_fig, master)
        self.canvas_sdk.get_tk_widget().configure(bg='white',width=300, height=300)
        self.canvas_sdk_module = AnimationUpdateModule(6664,self.canvas_sdk,self.canvas_sdk_fig)


        self.canvas_main.grid(row=cur_row, column=0, 
                              rowspan=canvas_size, columnspan= canvas_size,
                              padx=10, pady=10)
        self.canvas_car.grid(row=cur_row, column=canvas_size, 
                              rowspan=canvas_size, columnspan= canvas_size,
                              padx=10, pady=10)
        self.canvas_sdk.get_tk_widget().grid(
                            row=cur_row, column=canvas_size*2, 
                            rowspan=canvas_size, columnspan= canvas_size,
                            padx=10, pady=10)
        cur_row+=canvas_size

        # 程序上传组件 - 文件传输 1|3|1|1 目录:[        ] [选择][上传]
        self.prog_file_module = FileLoadModule(7777,master,"决策程序",cur_row)
        cur_row+=1
        self.maze_file_module = FileLoadModule(7778,master,"迷宫配置",cur_row)
        cur_row+=1

        # 创建文本框
        label = tk.Label(master, text="虚拟场景日志")
        label.grid(row=0, column=9,columnspan= 2,pady=10)
        text = tk.Text(root,width=50, height=15)
        text.grid(row=1, column=9, rowspan=2, columnspan=2, padx=10, pady=20)
        self.text_sim_module = TextUpdateModule(6667,text)

        # 创建文本框
        label = tk.Label(master, text="物理场景日志")
        label.grid(row=3, column=9,columnspan= 2,pady=10)
        text = tk.Text(root,width=50, height=15)
        text.grid(row=4, column=9, rowspan=2, columnspan=2, padx=10, pady=20)
        self.text_grd_module = TextUpdateModule(6668,text)

if __name__=="__main__":
    root = tk.Tk()
    gui = FileTransferGUI(root)
    root.mainloop()