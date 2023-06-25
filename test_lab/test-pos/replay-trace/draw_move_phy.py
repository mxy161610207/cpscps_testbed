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

TAG,SIZE = 'phy',5
# TAG,SIZE = 'sim',10
# TAG,SIZE = 'sim',5

subfolder = '3'
ITER_CNT=150

print(TAG)
print(subfolder)

W = 4
with open('{}/maze.txt'.format(subfolder), 'r') as f:
    _,W,_ = map(int, f.readline().split())

def draw_maze(edge_len):
    # 读入迷宫信息
    with open('{}/maze.txt'.format(subfolder), 'r') as f:
        M,W,H = map(int, f.readline().split())
        print(M,W,H)
        walls = []
        for _ in range(M):
            x1, y1, x2, y2 = map(int, f.readline().split())
            walls.append((x1, y1, x2, y2))
        # print(walls)
    
    edge_len=900
    global canvas_ax    
    for x1, y1, x2, y2 in walls:
        canvas_ax.plot([x1*edge_len, x2*edge_len], [y1*edge_len, y2*edge_len], color='black')
        # print(1)

def draw_scatter(x,y,rad,color,aw_len=100):
    dx = aw_len*math.cos(rad)
    dy = aw_len*math.sin(rad)

    global canvas_ax
    canvas_ax.scatter([x], [y],s=50,c=color,marker='o',alpha=0.5)
    # ax.arrow(x,y,dx,dy,color='k',width=1)

    global plt


import tkinter as tk

# 创建窗口
root = tk.Tk()
root.title("position")

if TAG=='phy':
    E = 2700
else:
    E = W*900
root.geometry('{}x{}'.format(E//SIZE,E//SIZE))

canvas_sdk_fig = plt.Figure()
canvas_sdk = FigureCanvasTkAgg(canvas_sdk_fig, root)
canvas_sdk.get_tk_widget().configure(bg='white',
                                     width=E//SIZE, height=E//SIZE)
canvas_sdk.get_tk_widget().grid()


phy_range = [-E/2.0, E/2.0]
sim_range = [0,E]

canvas_ax = canvas_sdk_fig.add_subplot(111, aspect='equal',
    autoscale_on=True, 
    xlim=phy_range if TAG=='phy' else sim_range,  
    ylim=phy_range if TAG=='phy' else sim_range)

canvas_ax.set_xlabel("x")
canvas_ax.set_ylabel("y")
canvas_ax.set_aspect('equal')
canvas_ax.set_xlim(phy_range if TAG=='phy' else sim_range)
canvas_ax.set_ylim(phy_range if TAG=='phy' else sim_range)


if TAG == 'sim':
    draw_maze(E)

lines=[]
with open('{}/{}_pos.txt'.format(subfolder, TAG), 'r') as f:
    lines = f.readlines()

# with open('{}/p1.txt'.format(subfolder, TAG), 'r') as f:
#     lines = f.readlines()

pre_color = 'red'
idx = 0
cur_idx = 0 


# 逐个读取数据文件并在画布上绘制点
def update_thread_main():
    total_iter = len(lines)
    adjust_iter = 0
    for line in lines:
        k = list(line.strip().split())
        x, y = float(k[1]),float(k[2])
        if TAG == 'phy':
            x-=E/2.0
            y-=E/2.0
            color ='blue' if k[0]=='True' else 'red'
        else:
            x = x*100
            y = y*100
            color ='red' if k[0]=='True' else 'blue'

        if (color=='red'):
            adjust_iter +=1

        global pre_color,cur_idx,idx
        if TAG == 'phy' and pre_color=='red' and color =='blue':
            cur_idx+=1
        pre_color = color


        deg = float(k[3])
        rad = math.radians(deg)

        # if cur_idx == idx:
        #     if (color == 'blue'):
        #         draw_scatter(x,y,rad,color,100)
        draw_scatter(x,y,rad,color,100)

        # time.sleep(0.05)

        global canvas_sdk
        canvas_sdk.draw()
    print("finished")
    print("total iteration =",total_iter)
    print("adjust iteration =",adjust_iter)
    print("adjust percent = {:.2f}%".format(adjust_iter*100.0/total_iter))



def all_update():
    # 逐个读取数据文件并在画布上绘制点
    blue_scatter_x = []
    blue_scatter_y = []
    red_scatter_x = []
    red_scatter_y = []

    old_scatter = None

    global canvas_ax,canvas_sdk
    total_iter = len(lines)
    adjust_iter = 0
    adjust_cnt = 0
    has_count = False
    for line_id,line in enumerate(lines):

        k = list(line.strip().split())
        x, y = float(k[1]),float(k[2])
        if TAG == 'phy':
            x-=E/2.0
            # x*=0.92
            y-=E/2.0
            color ='blue' if k[0]=='True' else 'red'
            # x-=100
            # y+=80
        else:
            x = x*100
            y = y*100
            color ='red' if k[0]=='True' else 'blue'

        if (color=='red'):
            if not has_count:
                adjust_cnt +=1
                has_count = True
            adjust_iter +=1
        else:
            has_count=False

        global pre_color,cur_idx,idx
        if TAG == 'phy' and pre_color=='red' and color =='blue':
            cur_idx+=1
        pre_color = color

        deg = float(k[3])
        rad = math.radians(deg)

        if color == 'blue':
            blue_scatter_x.append(x)
            blue_scatter_y.append(y)
        else:
            red_scatter_x.append(x)
            red_scatter_y.append(y)

        # if cur_idx == idx:
        #     if (color == 'blue'):
        #         draw_scatter(x,y,rad,color,100)
        # draw_scatter(x,y,rad,color,100)

        # time.sleep(0.05)


    canvas_ax.scatter([blue_scatter_x], [blue_scatter_y],
                    s=50,c='gray',marker='o',alpha=0.5)
    canvas_ax.scatter([red_scatter_x], [red_scatter_y],
                    s=50,c='red',marker='o',alpha=0.5)
    
    lastx = blue_scatter_x[-1]
    lasty = blue_scatter_y[-1]
    canvas_ax.scatter([lastx], [lasty],
                    s=50,c='blue',marker='o',alpha=0.5)

    
    canvas_sdk.draw()
    

    print("finished")
    print("total iteration =",total_iter)
    print("adjust iteration =",adjust_iter)
    print("adjust cnt =",adjust_cnt)
    print("adjust percent = {:.2f}%".format(adjust_iter*100.0/total_iter))



# update_thread = threading.Thread(target=update_thread_main, daemon=True)
# update_thread.start()

update_thread = threading.Thread(target=all_update, daemon=True)
update_thread.start()


# 窗口关闭时执行的函数
def on_closing():
    # 保存图像
    buf = io.BytesIO()
    canvas_sdk_fig.savefig(buf, format='png')
    buf.seek(0)
    img = Image.open(buf)
    global idx
    img.save('{}/{}_trace_image_{}.png'.format(subfolder,TAG,idx))
    buf.close()
    # 关闭窗口
    root.destroy()

# 设置窗口关闭时执行的函数
root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()

