# -*- coding:utf-8 -*-
from typing import List
import socket
import numpy as np
import threading
import math,copy,json
import os
import time
from multiprocessing import Value

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

    print(message)

    return 

# 界面中关于controller_status的更新
def action_json_sender(action_json):
    global controller_status
    global sdk_platform_message

    action_json_str = json.dumps(action_json)
    # print("send {}".format(action_json_str))
    update_controller_status(controller_status,2)
    sdk_platform_message.put(action_json_str)


# 线程，权限只能读取controller_status、controller_message和sensor
def flush_controller_status(controller_status,controller_message,sim_distance):
    global conn, conn_addr 
    while True:
        if controller_message.empty():
            send_json={
                'ir_distance': copy.deepcopy(sim_distance),
                'chassis_status': controller_status.value
            }
            send_json_str = json.dumps(send_json)
            if conn is not None:
                conn.send(f'{send_json_str}\n'.encode('utf8'))
            time.sleep(0.1)
        else:
            reply_json_str = controller_message.get()
            reply_json = json.loads(reply_json_str)
            if (reply_json['status']!='success'):
                update_controller_status(controller_status, -1)
            
            reply_type,reply_info = reply_json['type'],reply_json['info']
            if (reply_type=='MOVE'):
                update_controller_status(controller_status, 1)

# 线程 
def register_actuator(context_platform_addr,controller_status):
    actuator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"[actutor register] {context_platform_addr}")
    actuator_socket.connect(context_platform_addr)

    register_json={
        'message':{
        "name": "RoboMasterEP",
        "type": "Actor"
        },
        'cmd':'register'
    }
    config = json.dumps(register_json) +'\n'
    config = config.encode('utf-8')
    print(f"[actutor config] {config}")
    actuator_socket.send(config)
    print(f'send success')
    #接收数据
    register_back = actuator_socket.recv(1024).decode('utf-8')
    print(register_back)
    if register_back == None:
        return
    obj = json.loads(register_back)
    if obj["cmd"] != "register_back" or obj["message"] != "true":
        return

    while True:
        if controller_status.value == -1: break
        while True:
            try:
                msg = actuator_socket.recv(1024)
                if msg == None:
                    return
                
                msg = msg.decode('utf-8')
                print(f"[from pt]:{msg}")

                act_json = json.dumps(msg)

                if (act_json['cmd'] == 'action_request'):
                    reply_json = {
                        'cmd':'action_back',
                        'message':True}
                    cmd_str = act_json['message']
                    if (cmd_str.startswith("SAFE: chassis move")):
                        api_json = get_move_action(msg)
                    elif (cmd_str.startswith("SAFE: chassis speed")):
                        api_json = get_chassis_action(msg)

                    print(api_json)
                    if 'type' in api_json:
                        # 加入等待队列
                        action_json_sender(api_json)
                    
                    actuator_socket.send(reply_json.encode("utf-8"))
                    
            except Exception as e:
                print("ERROR",e)
                break
   
# 处理执行器指令
def get_chassis_action(action: str) -> List[float]:
    items = action.strip()[:-1].split(' ')
    x,y,z,timeout = [float(i) for i in [items[4], items[6], items[8], items[10]]]
    action_json={
        'type':'MOVE',
        'info':{
            'api_version':'USER',
            'api_info':{
                'x':x,
                'y':y,
                'z':z,
                'timeout':None if timeout<0 else timeout
            }
        }
    }
    return action_json

def get_move_action(action: str) -> List[float]:
    items = action.strip()[:-1].split(' ')
    x,y,z,vxy,vz,timeout,uuid = [float(i) for i in [
        items[4], items[6], items[8], items[10],items[12], items[14], items[16]]]
    action_json={
        'type':'MOVE',
        'info':{
            'api_version':'USER',
            'api_info':{
                'x':x,
                'y':y,
                'z':z,
                'xy_spd':vxy,
                'z_spd':vz,
                'timeout':None if timeout<0 else timeout,
                'uuid': int(uuid)
            }
        }
    }
    return action_json

def window_outside_exiter(controller_status,exit_func):
    while True:
        if controller_status.value!=-1:
            time.sleep(2)
        
        else:
            while (len(exit_func)==0):
                time.sleep(1)
            exit_func[0]()
            break

# 供manager.py调用
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

    driver_server_addr = platform_socket_address['driver_server']
    context_platform_addr = platform_socket_address['context_platform'] # 9091

    global controller_status
    global controller_message
    global sdk_platform_message

    controller_status = platform_status_resources['control']
    controller_message = platform_message_resources['control']
    sdk_platform_message = platform_message_resources['sdk']
    sim_distance = platform_status_resources['sim_distance'] 

    global conn,conn_addr
    conn,conn_addr=None,None

    # 控制器线程
    t_actutor = threading.Thread(
        target=register_actuator, 
        args=(context_platform_addr,controller_status))
    t_actutor.daemon = True
    t_actutor.start()
    
    # 线程 用于更新底盘状态，并产生驱动发送数据
    t_update = threading.Thread(
        target=flush_controller_status, 
        args=(controller_status,controller_message,sim_distance))
    t_update.daemon = True
    t_update.start()

    # 外部结束界面
    exit_func = []
    t_closer = threading.Thread(
        target=window_outside_exiter, 
        args=(controller_status,exit_func))
    t_closer.daemon = True
    t_closer.start()
    

    # 创建一个服务器供上下文平台连接
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(driver_server_addr)   
    print(f"[bind] {driver_server_addr}")
    server_socket.listen(10)

    # # 线程，接受并处理数据
    # t_recv = threading.Thread(
    #     target=recv_and_handle_app_commond, 
    #     args=(controller_status,server_socket))
    # t_recv.daemon = True
    # t_recv.start()

    # 主程序 检测并退出
    while True:
        if controller_status.value == -1: break
        time.sleep(3)
        
    server_socket.close()

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