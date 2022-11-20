# -*- coding:utf-8 -*-
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


import location.position_config as pc
from location.position import Position
from location.distance import Distance

button_manager={}
loc_grd_list=[]
def register_button(button):
    global button_manager
    button_manager[button._name]=button
    return

def change_button_state(button_name,button_state):
    global button_manager
    if button_name in button_manager:
        button_manager[button_name].change_button_state(button_state)
    return
    
def button_action_reset():
    global resource_manager,reset_button_status
    print("[Button Click] Location Server reset")

    change_button_state('location_reset_button','RESETING')

    if (resource_manager.location_server_empty()):
        return
    
    # switch to reset status and wait
    reset_button_status.value=1
    resource_manager.shutdown_location_server()

    # wait for reset end
    # while(reset_button_status.value!=0):
    #     time.sleep(0.5)
    # change_button_state('location_reset_button','NORMAL')

def reset_sim_env():
    global resource_manager,reset_button_status
    print("[Button Click] Simulate position reset")
    if (resource_manager.location_server_empty()):
        return
    resource_manager.reset_simulate_position()
    return 


def basic_set(ax,xlim_range,ylim_range,title_str):
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect('equal')
    ax.set_xlim([0,xlim_range])
    ax.set_ylim([0,ylim_range])
    ax.set_title(title_str)

def init_guard_ax_set(ax):
    xlim_range = pc.E
    ylim_range = pc.E
    title_str = "Grd"
    basic_set(ax,xlim_range,ylim_range,title_str)

def init_simulate_ax_set(ax):
    global sim_map
    xlim_range = sim_map.E()
    ylim_range = sim_map.E()
    title_str = "Sim"
    basic_set(ax,xlim_range,ylim_range,title_str)
    
    # TODO draw map function
    ws = sim_map.walls()
    # print(ws)
    for w in ws:
        x,y,xl,yl = w
        ax.add_patch(Rectangle((x, y), xl, yl,color="red"))

def draw_distance_ray(ax,inter_ps,irs_x,irs_y):
    first = True
    for p in inter_ps:
        if not first:
            co = 'black'
        else:
            co = 'red'
            first = False
        ax.arrow(irs_x,irs_y,p[0]-irs_x,p[1]-irs_y,color=co)
    pass

class PositionCanvas:
    _grid_map = 10
    # 窗口本身X行X列：
    # 多1行：上方标题
    # 多3列：信息框+2个操作按钮
    _grid_row_sz = _grid_map + 1
    _grid_col_sz = _grid_map + 3
    _grid_padx = 10
    _title_font = ('Times', 20)
    _map_size = 400
    _map_padxy = _map_size//10

    def __init__(self, window, tag, name, x, y, syncer):
        self._window = window
        self._tag = tag
        self._name = name
        self._syncer = syncer

        self._grid_row = x * self._grid_row_sz
        self._grid_col = y * self._grid_col_sz

        self._text_freeze = False

        self._title = self._create_title()
        self._canvas, self._fig_ax = self._create_canvas()
        self._text = self._create_text()
        self._pause_button = self._create_pause_button()
        self._clear_button = self._create_clear_button()

        self.text_show("BB")
        _default_msg = "这是一则骇人听闻的长长长长长消息！\n"+'1     \n2   \n'
        self.text_show(_default_msg)
        for _ in range(100):
            self.text_append("AA")

    @property
    def _bottom(self):
        return self._bottom

    def _create_title(self):
        title = tk.Label(self._window, text=self._name, font=self._title_font)
        title.grid(
            row=self._grid_row, column=self._grid_col,
            rowspan=1, columnspan=self._grid_map,
            sticky="nsew")
        return title

    def _create_pos_fig(self, position_info,
        color = 'b',arrow_color = 'k',marker='o',
        is_latest=False,aw_len=50):

        ax = self._fig_ax
        x,y,rad = position_info['x'],position_info['y'],position_info['rad']

        '''
        draw (scatter, arrow) to show a car's position
        '''
        # assert(isinstance(pos,Position))
        # print("pos = ",pos)
        dx = aw_len*math.cos(rad)
        dy = aw_len*math.sin(rad)

        if (not is_latest):
            color = 'gray'
            pt = ax.scatter([x],[y],
                            s=50,c=color,marker=marker,alpha=0.5)
        else:
            pt = ax.scatter([x],[y],
                            s=50,c=color,marker=marker,alpha=0.5)
            pt_aw =ax.arrow(x,y,dx,dy,color=arrow_color,width=1)

    # 使用self._syncer绘制当前位置
    def _animate_update(self,fid):
        # print("update")
        # 获取_syncer信息
        position_info = copy.deepcopy(self._syncer)

        # 初始化画布
        self._fig_ax.clear()
        init_guard_ax_set(ax=self._fig_ax)

        # 绘制当前位置
        self._create_pos_fig(
            position_info=position_info,
            is_latest=True,aw_len=50
            )

        # TODO 绘制历史位置
        # for i in range(1,len(loc_list)):
        #     create_pos_fig(ax,loc_list[i],is_latest=False)
        # create_pos_fig(ax,position_info,is_latest=True,aw_len=50)

        # 添加文字描述 
        text = position_info['info']+'\n'+position_info['status']
        self.text_show(text)
        
    # TODO: 之后为虚拟端画图标
    # different from guard, need to build simulate map
    # def animate_update_sim(self,fid):
    #     ax = self._fig_ax

    #     global resource_manager
    #     if (resource_manager.location_server_empty()): return
        
    #     # get car center
    #     loc_list = resource_manager.get_display_info("sim")
    #         # location_server.get_sim_display_info(5)
    #     ax.clear()
    #     init_simulate_ax_set(ax)

    #     for i in range(1,len(loc_list)):
    #         create_pos_fig(ax,loc_list[i],is_latest=False)
    #     create_pos_fig(ax,loc_list[0],is_latest=True,aw_len=50)

    #     irs_pos = Position(loc_list[0],is_irs_center=False)._calc_sensor_center()

    #     # TODO 画传感器辅助线
    #     global sim_map
    #     status,inter_md_dis,inter_ps = sim_map.get_inter_info()
    #     if (status):
    #         draw_distance_ray(ax,inter_ps,irs_pos.x,irs_pos.y)
    #         F,B,L,R = list(map(int,inter_md_dis[:4]))
    #         log = []
    #         log.append("F:{}\tB:{}\nL:{}\tR:{}\n".format(
    #             F,B,L,R
    #         ))
    #         log.append(irs_pos.pos_str)
    #         self.text_show('\n'.join(log))
        
    #     # print("sim_ani end")`

    def _create_canvas(self):
        fig = mplfig.Figure()

        canvas = FigureCanvasTkAgg(fig, master=self._window)
        canvas.get_renderer
        canvas.get_tk_widget().configure(bg='white',
                                         height=self._map_size+self._map_padxy,
                                         width=self._map_size+self._map_padxy)
        canvas.get_tk_widget().grid(
            row=self._grid_row+1, column=self._grid_col,
            rowspan=self._grid_map, columnspan=self._grid_map,
            sticky="nsew", padx=self._grid_padx)

        ax = fig.add_subplot(111, aspect='equal',
                             autoscale_on=False, xlim=[0, 6], ylim=[-3, 3])

        self._x = np.arange(0, 2*np.pi, 0.01)        # x-array
        self._line, = ax.plot(self._x, np.sin(self._x))

        if (self._tag=='grd'):
            self._ani = animation.FuncAnimation(
            fig, self._animate_update, frames=10)
        # elif (self._tag=='sim'):
        #     self._ani = animation.FuncAnimation(
        #     fig, self.animate_update_sim, frames=10)
    
        return canvas, ax

    def _create_text(self):
        text = ScrolledText(self._window, bg='Gainsboro', width=25)
        text.grid(
            row=self._grid_row+1,
            column=self._grid_col+self._grid_map,
            rowspan=self._grid_map-2, columnspan=3,
            sticky="nsew", padx=self._grid_padx)
        text.config(state="disabled")
        return text

    def button_pause(self):
        self._text_freeze = not self._text_freeze

    def _create_pause_button(self):
        button = tk.Button(self._window, text="暂停",
                           command=self.button_pause, width=30)
        # 将按钮放置在主窗口内
        button.grid(
            row=self._grid_row+self._grid_map-1,
            column=self._grid_col+self._grid_map,
            rowspan=1, columnspan=1,
            sticky="nsew", padx=20, pady=10)
        return button

    def button_clear(self):
        self.text_show("", clear=True, ignore_freeze=True)

    def _create_clear_button(self):
        button = tk.Button(self._window, text="清除",
                           command=self.button_clear, width=30)
        # 将按钮放置在主窗口内
        button.grid(
            row=self._grid_row+self._grid_map,
            column=self._grid_col+self._grid_map,
            rowspan=1, columnspan=1,
            sticky="nsew", padx=20, pady=10)
        return button

    def text_show(self, msg, clear=True, ignore_freeze=False):
        if (not ignore_freeze and self._text_freeze):
            return
        if (msg != "" and msg[-1] != '\n'):
            msg += "\n"
        self._text.config(state="normal")
        if (clear):
            self._text.delete(1.0, tk.END)
        self._text.insert(tk.END, msg)
        self._text.config(state="disabled")
        self._text.see(tk.END)
        return

    def text_append(self, msg):
        if (self._text_freeze):
            return
        return self.text_show(msg, clear=False)

class PlatformButton():
    _grid_cur_row = 20
    _grid_row_sz = 1
    _grid_col_sz = 2+1
    _grid_padx = 20
    _grid_pady = 10
    _button_width = 30

    def __init__(self, window, name, button_text, with_info=False):
        self._window = window
        self._name = name

        self._grid_row = PlatformButton._grid_cur_row
        PlatformButton._grid_cur_row += 1

        self._button = self._create_button(button_text, with_info)
        return

    def _create_button(self, button_text, with_info):
        button = tk.Button(self._window, text=button_text,
                           width=self._button_width)
        button.grid(row=self._grid_row,
                    column=1, rowspan=1,
                    columnspan=2 if with_info else 5,
                    sticky="nsew",
                    padx=self._grid_padx, pady=self._grid_pady)
        return button

    def _bind_action(self, action):
        self._button.config(command=action)
    
    def change_button_state(self,info):
        pass

class PlatformActionButton(PlatformButton):
    def __init__(self, window, name, button_text, default_state):
        super().__init__(window, name, button_text, with_info=True)

        self._button_state = self._create_button_state(default_state)
        pass

    def _create_button_state(self, default_state):
        button_state = tk.Label(self._window, text=default_state)
        button_state.grid(row=self._grid_row,
                          column=3, rowspan=1, columnspan=1,
                          sticky="nsew", padx=20, pady=10)
        return button_state
    
    def change_button_state(self,info):
        self._button_state['text']=info
        return

class PlatformEnterButton(PlatformButton):
    def __init__(self, window, name, button_text):
        super().__init__(window, name, button_text, with_info=True)

        self._button_entry = self._create_button_entry()

        pass

    def _create_button_entry(self):
        button_entry = tk.Entry(self._window)
        button_entry.grid(row=self._grid_row,
                          column=3, rowspan=1, columnspan=1,
                          sticky="nsew", padx=20, pady=10)
        return button_entry

def my_root_window_set():
    # name
    root_window = tk.Tk()
    root_window.title('CPS-CPS platform')

    # size
    # root_window.geometry('900x600')

    # left-up icon image
    dir = os.path.dirname(os.path.abspath(__file__))
    icon_file = dir+'/assert/display_icon.ico'
    root_window.iconbitmap(icon_file)

    return root_window

def create_display(
        platform_status_resources,
        platform_message_resources,
        platform_socket_address,
        exit_func
        ):
    # 获取必要的资源
    grd_location_syncer = platform_message_resources['grd_position']
    sim_location_syncer = platform_message_resources['sim_position'] 

    global sdk_platform_status,sdk_platform_message,display_platform_message
    display_platform_message = platform_message_resources['display']
    sdk_platform_status = platform_status_resources['sdk']
    sdk_platform_message = platform_message_resources['sdk']

    # 调用Tk()创建主窗口
    root_window = my_root_window_set()

    grd_canvas = PositionCanvas(window = root_window,
        tag="grd", name = "Guard Position", x=0, y=0,
        syncer= grd_location_syncer)
    # sim_canvas = PositionCanvas(root_window, "sim", "Simulate Position", 0, 1)

    # global resource_manager
    # location_reset_button = PlatformActionButton(
    #     root_window, "location_reset_button", "定位系统启动", "Normal")
    # location_reset_button._bind_action(button_action_reset)
    # register_button(location_reset_button)

    # platform_raise_button = PlatformActionButton(
    #     root_window, "platform_raise_button", "平台初始化", "SystemState.Initialized")
    # register_button(platform_raise_button)

    # usr_program_upload_button = PlatformEnterButton(
    #     root_window, "usr_program_upload_button", "用户程序上传")
    # register_button(usr_program_upload_button)

    # global action_can_do
    # action_can_do=True

    # dji_sdk_L_button = PlatformActionButton(
    #     root_window, "dji_sdk_L_button", "大疆sdk调用-L", "")
    # dji_sdk_L_button._bind_action(action_L)
    # register_button(dji_sdk_L_button)

    # dji_sdk_r_button = PlatformActionButton(
    #     root_window, "dji_sdk_r_button", "大疆sdk调用-r", "")
    # dji_sdk_r_button._bind_action(action_r)
    # register_button(dji_sdk_r_button)

    # dji_sdk_F_button = PlatformActionButton(
    #     root_window, "dji_sdk_F_button", "大疆sdk调用-F", "")
    # dji_sdk_F_button._bind_action(action_F)
    # register_button(dji_sdk_F_button)

    # dji_sdk_init_end_button = PlatformActionButton(
    # root_window, "dji_init_end_button", "大疆初始化结束", "")
    # dji_sdk_init_end_button._bind_action(init_end)
    # register_button(dji_sdk_init_end_button)

    # sim_env_reset_button_status = PlatformActionButton(
    #     root_window, "sim_env_reset_button_status", "虚拟环境初始化", "")
    # sim_env_reset_button_status._bind_action(reset_sim_env)
    # register_button(sim_env_reset_button_status)

    quit_button = PlatformButton(
        root_window, "quit_button","退出")
    quit_button._bind_action(root_window.destroy)
    register_button(quit_button)

    # 注册退出函数，方便外部的程序结束窗口
    exit_func.append(root_window.destroy)

    # 开启主循环，让窗口处于显示状态
    display_status = platform_status_resources['display']
    display_status.value = 1

    root_window.mainloop()
    # 用户按下quit_button后退出

def window_outside_exiter(display_status,exit_func):
    while True:
        if display_status.value!=-1:
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

    display_status = platform_status_resources['display']

    # 自己就是退出者
    if display_status.value == -1:
        return
    
    # 设置之后 window_outside_exiter 会结束 root_window.mainloop()
    display_status.value = -1

# main
def raiser(
    proc_name,
    platform_status_resources,
    platform_message_resources,
    platform_socket_address):

    print("Proc [{}] start".format(proc_name))

    # 外部结束界面
    exit_func = []
    display_status = platform_status_resources['display']
    t_closer = threading.Thread(
        target=window_outside_exiter, 
        args=(display_status,exit_func))
    t_closer.daemon = True
    t_closer.start()

    display_status.value = 0

    create_display(
        platform_status_resources,
        platform_message_resources,
        platform_socket_address,
        exit_func)

    global_status = platform_status_resources['global']
    global_status.value = -1

    print("Proc [{}] end".format(proc_name))