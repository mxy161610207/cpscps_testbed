from abc import abstractmethod
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import matplotlib.pyplot as plt
import matplotlib.figure as mplfig
from matplotlib.widgets import TextBox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading
import math,copy,json
import os
import time
import matplotlib.animation as animation


def my_root_window_set():
    # name
    root_window = tk.Tk()
    root_window.title('Sensor Display')

    # size
    # root_window.geometry('900x600')

    # # 窗口图标
    # dir = os.path.dirname(os.path.abspath(__file__))
    # icon_file = dir+'/assert/display_icon.ico'
    # root_window.iconbitmap(icon_file)

    return root_window


def update_sensor_info(sensor_info,show_sp,F_dis,platform_message_resources):
    sim_pos = platform_message_resources['sim_position']
    while True:
        f_dir = open("D:\\GitHub\\cpscps_testbed\\unity_dir.txt","r")
        context = f_dir.read()
        f_dir.close()
        dir = list(map(int,context.split()))
        # F,R,B,L
        tag = ['F','R','B','L']
        for _ in range(len(tag)):
            try:
                F_dis.value = int(dir[0])
                t = "{}:{}".format(tag[_],dir[_])
            except Exception as e:
                continue
            sensor_info[tag[_]].config(text=t)

        # sdk_platform_message =      platform_message_resources['sdk']
        # if (F_dis.value>0 and F_dis.value<700):
        #     run_json={
        #         'type':"FFF",
        #         'info':{}
        #     }
        #     sdk_platform_message.put(json.dumps(run_json))

        # print(1111)

        tag = ['x','y','deg']
        for i in range(len(tag)):
            try:
                t = "{}:{:.3f}".format(tag[i],sim_pos[tag[i]])
                # print(t)
            except Exception as e:
                continue
            show_sp[tag[i]].config(text=t)

        time.sleep(0.2)

def raiser(proc_name,
    platform_status_resources,
    platform_message_resources,
    platform_socket_address):

    root_window = my_root_window_set()
    row=0

    sensor_info = {}
    row+=1
    tag = ['F','B','L','R']
    for i in range(len(tag)):
        sensor = tk.Label(root_window, text=tag[i], justify='left', font=("times",20))
        if (tag[i]=='F'):
            sensor.grid(row=row,rowspan=1,
                column=i+1, columnspan=3,
                sticky="nsew",
                padx=20, pady=10)
        sensor_info[tag[i]]=sensor

    show_sp={}
    row+=1
    tag = ['x','y','deg']
    tmp = tk.Label(root_window, text="car_pos", justify='left',font=("times",14))
    tmp.grid(row=row,rowspan=1,column=1, columnspan=1, sticky="nsew", padx=20, pady=10,)
    for i in range(len(tag)):
        tmp = tk.Label(root_window, text=tag[i], justify='left',font=("times",14))
        tmp.grid(row=row,rowspan=1,
                column=i+2, columnspan=1,
                sticky="nsew",
                padx=20, pady=10)
        show_sp[tag[i]]=tmp

    F_dis = platform_status_resources['F_dis']

    t_update = threading.Thread(
        target=update_sensor_info, 
        args=(sensor_info,show_sp,F_dis,platform_message_resources))
    t_update.daemon = True
    t_update.start()


    row+=1
    quit_button = tk.Button(root_window, text='quit',width=3)
    quit_button.grid(row=row,rowspan=1,
                    column=1, columnspan=1,
                    sticky="nsew",
                    padx=20, pady=10)
    quit_button.config(command = root_window.destroy)

    # 开启主循环，让窗口处于显示状态
    root_window.mainloop()

