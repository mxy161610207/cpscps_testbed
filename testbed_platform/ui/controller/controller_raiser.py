# -*- coding:utf-8 -*-
from abc import abstractmethod
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import matplotlib.pyplot as plt
import matplotlib.figure as mplfig
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading
import math,copy,json
import os
import time
import matplotlib.animation as animation

class ActionButton():
    _button_width = 10
    _grid_padx = 20
    _grid_pady = 10

    def __init__(self, panel, name, button_code,x,y,xsize=1,ysize=1):
        self._panel = panel
        self._name = name
        self._button_code = button_code

        self._x = x
        self._xsize = xsize
        self._y = y
        self._ysize = ysize

        self._button = self._create_button()
        self._bind_action()
        return
    
    def _create_button(self):
        button = tk.Button(
                    self._panel._window, 
                    text=self._name,
                    width=self._button_width
                    )
        button.grid(row=self._x,rowspan=self._xsize,
                    column=self._y, columnspan=self._ysize,
                    sticky="nsew",
                    padx=self._grid_padx, pady=self._grid_pady)
        return button

    def _set_disable(self):
        self._button.config(state=tk.DISABLED)
    
    def _set_enable(self):
        self._button.config(state=tk.ACTIVE)

    def _bind_action(self):
        self._button.config(command= lambda: 
            self._panel._bind_action(self._button_code))

class DJIControllerPanel():
    def __init__(self,window,name,status):
        self._window=window
        self._name = name
        self._status = status

        row,col=3,3
        button_name_list=[
            ['小左转','刷新','小右转'],
            ['左转45','前进','右转45'],
            ['左移','后退','右移'],
        ]
        button_code_list=[
            ['l','F','r'],
            ['L','W','R'],
            ['A','S','D'],
        ]

        self._button_list=[
            [] for _ in range(row+1)
        ]

        for i in range(row):
            for j in range(col):
                bname,bcode=button_name_list[i][j],button_code_list[i][j]
                tmp = ActionButton(self,bname,bcode,i+1,j+1)
                self._button_list[i].append(tmp)

        tmp = ActionButton(self,"初始化","init",row+1,1,1,col)
        self._button_list[row].append(tmp)

        self._status_text = tk.Label(self._window, text="DJIControllerPanel", font=('Times', 14))
        self._status_text.grid(
            row=row+2, column=1,
            rowspan=1, columnspan=col,
            sticky="nsew")

    
    def _set_status_text(self,prefix):
        self._status_text.config(text="{}".format(prefix))

    @staticmethod
    def _action_json_create(ch):
        if (ch=='init'):
            action_json={
                'type':'SYSTEM_STATUS',
                'info':{
                    'status':'init_success',
                }
            }
        else:
            action_json={
                'type':'ACTION',
                'info':{
                    'api_version':'DJI',
                    'api_info':ch
                }
            }
        return action_json
    
    def _bind_action(self,ch):
        if self._status.value != 1:
            self._set_status_text("reject [{}]".format(ch))
            return 
        
        elif self._status.value == 1:
            action_json_sender(DJIControllerPanel._action_json_create(ch))
            self._set_status_text("accept [{}]".format(ch))
            return 
        
        self._set_status_text("error".format(ch))

    def _disable_all_button(self):
        for button_row in self._button_list:
            for button in button_row:
                button._set_disable()
    
    def _enable_all_button(self):
        for button_row in self._button_list:
            for button in button_row:
                button._set_enable()

class UsrControllerPanel():
    def __init__(self,window,name,status):
        self._window=window
        self._name = name
        self._status = status

        row,col=3,3
        button_name_list=[
            ['小左转','刷新','小右转'],
            ['左转90','前进','右转90'],
            ['左移','后退','右移'],
        ]
        button_code_list=[
            ['l','F','r'],
            ['L','W','R'],
            ['A','S','D'],
        ]

        self._button_list=[
            [] for _ in range(row+1)
        ]

        for i in range(row):
            for j in range(col):
                bname,bcode=button_name_list[i][j],button_code_list[i][j]
                tmp = ActionButton(self,bname,bcode,i+1,3+j+1)
                self._button_list[i].append(tmp)

        self._status_text = tk.Label(self._window, text="DJIControllerPanel", font=('Times', 14))
        self._status_text.grid(
            row=row+1, column=3+1,
            rowspan=2, columnspan=col,
            sticky="nsew")

        self._disable_all_button()

    def _set_status_text(self,prefix):
        self._status_text.config(text="{}".format(prefix))

    @staticmethod
    def _action_json_create(ch):
        if (ch=='init'):
            action_json={
                'type':'SYSTEM_STATUS',
                'info':{
                    'status':'init_success',
                }
            }
        else:
            action_json={
                'type':'ACTION',
                'info':{
                    'api_version':'USER',
                    'api_info':ch
                }
            }
        return action_json
    
    def _bind_action(self,ch):
        if self._status.value != 1:
            self._set_status_text("reject [{}]".format(ch))
            return 
        
        elif self._status.value == 1:
            action_json_sender(UsrControllerPanel._action_json_create(ch))
            self._set_status_text("accept [{}]".format(ch))
            return 
        
        self._set_status_text("error".format(ch))
    
    def _disable_all_button(self):
        for button_row in self._button_list:
            for button in button_row:
                button._set_disable()
    
    def _enable_all_button(self):
        for button_row in self._button_list:
            for button in button_row:
                button._set_enable()

def my_root_window_set():
    # name
    root_window = tk.Tk()
    root_window.title('RoboMaster-EP contorller')

    # size
    # root_window.geometry('900x600')

    # # 窗口图标
    # dir = os.path.dirname(os.path.abspath(__file__))
    # icon_file = dir+'/assert/display_icon.ico'
    # root_window.iconbitmap(icon_file)

    return root_window

def create_controller_display(
        platform_status_resources,
        platform_message_resources,
        platform_socket_address,
        exit_func):
    # 获取必要的资源
    global controller_status
    controller_status = platform_status_resources['control']
    
    global controller_message
    controller_message = platform_message_resources['control']

    global sdk_platform_message
    sdk_platform_message = platform_message_resources['sdk']


    # 调用Tk()创建主窗口
    root_window = my_root_window_set()

    global controller_panels
    dji_controller_panel = DJIControllerPanel(
        root_window,name="dji_controller_panel",status=controller_status)
    
    usr_controller_panel = UsrControllerPanel(
        root_window,name="usr_controller_panel",status=controller_status
    )

    controller_panels = {
        'dji':dji_controller_panel,
        'usr':usr_controller_panel
    }
    
    dji_controller_panel._set_status_text("able")
    usr_controller_panel._set_status_text("freezed")

    # 总按键
    global status_update_register
    status_box = tk.Label(root_window, text="flush", font=('Times', 14))
    status_box.grid(row=6,rowspan=1,
                    column=1, columnspan=6,
                    sticky="nsew",
                    padx=20, pady=10)
    status_update_register.append(status_box)

    quit_button = tk.Button(root_window, text='quit',width=3)
    quit_button.grid(row=7,rowspan=1,
                    column=1, columnspan=6,
                    sticky="nsew",
                    padx=20, pady=10)
    quit_button.config(command = root_window.destroy)
    exit_func.append(root_window.destroy)

    update_controller_status(controller_status,1)

    # 开启主循环，让窗口处于显示状态
    root_window.mainloop()
    # 用户按下quit_button后退出

# 界面中关于controller_status的更新
def action_json_sender(action_json):
    global controller_status
    global sdk_platform_message

    action_json_str = json.dumps(action_json)
    # print("send {}".format(action_json_str))
    update_controller_status(controller_status,2)
    sdk_platform_message.put(action_json_str)

def update_controller_status(controller_status, val):
    message = ""
    if (val == 1):
        if (controller_status.value == 2):
            message = "已完成"
        else:
            message = "空闲中"
    elif val == 2:
        message = "正在运行中"

    controller_status.value = val

    global status_update_register
    for label in status_update_register:
        label.config(text = "{} | status = {}".format(message, controller_status.value))
    
    return 

# 另一个线程的，权限只能读取controller_status和controller_message
def flush_controller_status(controller_status,controller_message):
    while True:
        if controller_message.empty():
            time.sleep(0.5)
        
        get = controller_message.get()
        if isinstance(get,str):
            # "init_success","action_success"
            # print("get {}".format(get))
            update_controller_status(controller_status, 1)
            if get=='init_success':
                # 按钮有效性交换
                global controller_panels
                controller_panels['dji']._disable_all_button()
                controller_panels['usr']._enable_all_button()


def window_outside_exiter(controller_status,exit_func):
    while True:
        if controller_status.value!=-1:
            time.sleep(2)
        
        else:
            while (len(exit_func)==0):
                time.sleep(1)
            exit_func[0]()
            break

def closer(
    platform_status_resources,
    platform_message_resources,
    platform_socket_address):

    controller_status = platform_status_resources['control']
    
    # 自己就是退出者
    if controller_status.value == -1:
        return
    
    # 设置之后 window_outside_exiter 会结束 root_window.mainloop()
    controller_status.value = -1

# main
def raiser(
    proc_name,
    platform_status_resources,
    platform_message_resources,
    platform_socket_address):

    print("Proc [{}] start".format(proc_name))

    controller_status = platform_status_resources['control']
    controller_message = platform_message_resources['control']
    
    # 当controller_status变化时 所有需要更新的模块
    global status_update_register
    status_update_register = []
    t_update = threading.Thread(
        target=flush_controller_status, 
        args=(controller_status,controller_message))
    t_update.daemon = True
    t_update.start()


    # 外部结束界面
    exit_func = []
    t_closer = threading.Thread(
        target=window_outside_exiter, 
        args=(controller_status,exit_func))
    t_closer.daemon = True
    t_closer.start()
    
    # 界面生成
    create_controller_display(
        platform_status_resources,
        platform_message_resources,
        platform_socket_address,
        exit_func)

    time.sleep(1)
    # 控制程序退出时，如果小车正常初始化完，不需要结束所有的资源
    sdk_platform_status = platform_status_resources['sdk']
    print("Display [{}] end with status = {}".format(proc_name,sdk_platform_status.value))
    
    if sdk_platform_status.value >=2:
        pass
    elif sdk_platform_status.value == 1:
        global_status = platform_status_resources['global']
        global_status.value = -1
        print("Proc [{}] end".format(proc_name))
        return 
    
    # 界面退出后，清空资源管道
    controller_status.value = 0
    while(not controller_message.empty()):
        controller_message.get()

    print("Proc [{}] end".format(proc_name))