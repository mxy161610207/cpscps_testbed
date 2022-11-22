# -*- coding:utf-8 -*-
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

class BaseControllerPanel():
    _class_panel_left_col = 0

    def __init__(self,window,name,status,panel_span=4):
        self._window=window
        self._name = name
        self._status = status

        # 一个面板占_col_span列
        self._panel_span = panel_span
        self._panel_col_start = BaseControllerPanel._class_panel_left_col+1
        
        BaseControllerPanel._class_panel_left_col += panel_span

        self._button_list = []
        self._status_text = tk.Label(self._window, text=self._name,justify='left')

    def _set_status_text(self,prefix):
        self._status_text.config(text="{}".format(
            prefix))

    def _disable_all_button(self):
        for button in self._button_list:
            button._set_disable()
    
    def _enable_all_button(self):
        for button in self._button_list:
                button._set_enable()

class DJIControllerPanel(BaseControllerPanel):
    def __init__(self,window,name,status,panel_span=10):
        super().__init__(window,name,status,panel_span)

        grid_row = 0
        grid_col = self._panel_col_start
        col_span = self._panel_span

        button_name_list=[
            ['前进','左移','后退','右移'],
            ['左转45','小左转','小右转','右转45'],
            ['掉头','定位刷新']
        ]
        button_code_list=[
            ['W','A','S','D'],
            ['L','l','r','R'],
            ['B','F']
        ]
        
        for i in range(len(button_name_list)):
            grid_row+=1
            for j in range(len(button_name_list[i])):
                bname,bcode=button_name_list[i][j],button_code_list[i][j]
                button_col_span = 4//len(button_name_list[i])
                tmp = ActionButton(self,bname,bcode,grid_row,grid_col+j*button_col_span,ysize=button_col_span)
                self._button_list.append(tmp)
                # print(bname,grid_row,grid_col+j,1,button_col_span)

        grid_row+=1
        tmp = ActionButton(self,"平台初始化","init",grid_row,grid_col,ysize = col_span)
        self._button_list.append(tmp)
        
        grid_row+=1
        status_size = 10
        self._status_text.grid(row=grid_row, column=grid_col,rowspan=status_size, columnspan=col_span,
        sticky="nsew")

        grid_row+=status_size
        self._panel_total_row = grid_row+1

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
                'type':'MOVE',
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

class UsrControllerPanel(BaseControllerPanel):
    def __init__(self,window,name,status,panel_span=10):

        super().__init__(window,name,status,panel_span)

        button_name_list = [
            ['move','x','y','z','timeout'],
            ['drive','x','y','z','timeout'],
            ['sim_syncer','x','y','deg']
        ]
        self._action_info = {}
        
        grid_row = 0
        grid_col = self._panel_col_start
        col_span = self._panel_span

        for button_info in button_name_list:
            grid_row+=1
            col = grid_col
            api_name = button_info[0]

            api_text = tk.Label(self._window, text=api_name)
            api_text.grid(row=grid_row, column=col, rowspan=1, columnspan=1, sticky="nsew")

            args_element = {}
            for args_name in button_info[1:]:
                args_text = tk.Label(self._window, text=args_name,width=6)
                args_entry = tk.Entry(self._window, width=6)
                
                col+=1
                args_text.grid(row=grid_row, column=col, rowspan=1, columnspan=1, sticky="nsew",pady=10)
                col+=1
                args_entry.grid(row=grid_row, column=col,rowspan=1, columnspan=1, sticky="nsew",pady=10)
        
                args_element[args_name] = args_entry
            
            self._action_info[api_name]=args_element

            col+=1
            api_button = ActionButton(self,"提交",api_name,grid_row,col)
            self._button_list.append(api_button)

        
        grid_row+=1
        status_size = 3
        self._status_text.grid(row=grid_row, column=grid_col,rowspan=status_size, columnspan=col_span,
        sticky="nsew")

        self._sensor_name_list = ['distance','angle']
        self._sensor_info={}

        for sensor_name in self._sensor_name_list:
            grid_row+=1
            col = grid_col

            sensor_text = tk.Label(self._window, text=sensor_name)
            sensor_text.grid(row=grid_row, column=col, rowspan=1, columnspan=2, sticky="nsew")

            sensor_button = ActionButton(self,"查询",sensor_name,grid_row,col+2, ysize = 2)
            self._button_list.append(sensor_button)

            sensor_result = tk.Label(self._window, text="None")
            sensor_result.grid(row=grid_row, column=col+4,columnspan= 3, sticky="nsew")

            self._sensor_info[sensor_name] = sensor_result

        grid_row+=1
        status_size = 1
        self._status_text.grid(row=grid_row, column=grid_col,rowspan=status_size, columnspan=col_span,
        sticky="nsew")

        grid_row+=status_size
        self._panel_total_row = grid_row+1

        self._disable_all_button()

    def handle_sensor_update(self,sensor_type,sensor_info):
        sensor_label = self._sensor_info[sensor_type]
        sensor_label.config(text=sensor_info)

    def is_block(self,button_code):
        if (button_code=='drive' or self.is_sensor(button_code)):
            return False
        return True

    def is_sensor(self,button_code):
        if (button_code in self._sensor_name_list):
            return True
        return False
    
    @staticmethod
    def _sensor_json_create(button_code):
        sensor_json={
            'type':'SENSOR',
            'info':{
                'sensor_type':button_code,
            }
        } 
        return sensor_json

    @staticmethod
    def _api_json_create(button_code,args):
        api_json={
            'type':button_code.upper(),
            'info':{
                'api_version':'USER',
                'api_info':args
            }
        } 
        return api_json

    def _args_json_create(self,api_code):

        args_element = self._action_info[api_code]
        args_json = {}
        # print(args_element)
        for k in args_element:
            args_str = args_element[k].get()
            try:
                val = float(args_str)
            except Exception as e:
                if (k=='timeout'):
                    val = 10.0
                else:
                    val = 0.0
            
            if (api_code == 'drive' or api_code == 'move'):
                if (k=='timeout'):
                    val = min(max(0.0,val),10.0)
                elif k=='z' or k=='deg':
                    val = min(max(0,val),360)
                else:
                    val = min(max(0.3,val),3)
            elif api_code == 'sim_syncer':
                if k=='deg':
                    val = min(max(0,val),360)
                else:
                    val = min(max(300,val),900)

            args_json[k]=val
        
        return args_json
      
    def _bind_action(self,button_code):
        if self._status.value != 1:
            self._set_status_text("reject [{}]".format(button_code))
            return 

        to_send_json = {}
        self._set_status_text("accept [{}]".format(button_code))
        if self.is_sensor(button_code):
            to_send_json = self._sensor_json_create(button_code)
            action_json_sender(to_send_json)
        else:
            args_json = self._args_json_create(button_code)
            to_send_json = self._api_json_create(button_code,args_json)
            action_json_sender(to_send_json)
        
        json_str = json.dumps(to_send_json,indent=2)
        controller_panels['dji']._set_status_text("send : "+json_str)

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
    
    dji_controller_panel._set_status_text("先初始化")
    usr_controller_panel._set_status_text("")

    # next_row = dji_controller_panel._panel_total_row
    next_row = max(dji_controller_panel._panel_total_row,usr_controller_panel._panel_total_row)

    # 总按键
    global status_update_register
    status_box = tk.Label(root_window, text="flush")
    status_box.grid(row=next_row,rowspan=1,
                    column=1, columnspan=6,
                    sticky="nsew",
                    padx=20, pady=10)
    status_update_register.append(status_box)

    quit_button = tk.Button(root_window, text='quit',width=3)
    quit_button.grid(row=next_row+1,rowspan=1,
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
    elif val == -1:
        message = "执行出错"

    controller_status.value = val

    global status_update_register
    for label in status_update_register:
        label.config(text = "{} | status = {}".format(message, controller_status.value))
    
    return 

# 另一个线程的，权限只能读取controller_status和controller_message
def flush_controller_status(controller_status,controller_message):
    global controller_panels
    while True:
        if controller_message.empty():
            time.sleep(0.5)
        
        reply_json_str = controller_message.get()
        reply_json = json.loads(reply_json_str)
        if (reply_json['status']!='success'):
                update_controller_status(controller_status, -1)
        
        reply_type,reply_info = reply_json['type'],reply_json['info']
        if (reply_type=='SYSTEM_STATUS'):
            if (reply_info['msg']=='init_success'):
                # 按钮有效性交换
                update_controller_status(controller_status, 1)
                controller_panels['dji']._disable_all_button()
                controller_panels['usr']._enable_all_button()
        elif reply_type=='SENSOR':
            update_controller_status(controller_status, 1)
            sensor_type = reply_info['sensor_type']
            sensor_info = reply_info['sensor_info']
            
            controller_panels['usr'].handle_sensor_update(sensor_type,sensor_info)
        else:
            update_controller_status(controller_status, 1)


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