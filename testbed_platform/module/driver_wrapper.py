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


# 线程 当move完成时更新状态，权限只能读取controller_status、controller_message
def flush_controller_status(controller_status,controller_message):
    while True:
        reply_json_str = controller_message.get()
        reply_json = json.loads(reply_json_str)
        if (reply_json['status']!='success'):
            update_controller_status(controller_status, -1)
        
        reply_type,reply_info = reply_json['type'],reply_json['info']
        if (reply_type=='MOVE'):
                update_controller_status(controller_status, 1)

# 由于从 java socket读数据导致的
def recv_helper(java_socket,socket_buffer):
    data = None
    while True:
        r = java_socket.recv(1024)
        socket_buffer+=r
        split_pos = socket_buffer.find(b'\n')
        if split_pos!=-1:
            data = socket_buffer[:split_pos].decode("utf-8")
            socket_buffer = socket_buffer[split_pos+1:]
            break
    
    if (data.find('alive_request')==-1):
        # print(f"[P->{threading.current_thread().name}] {data}")
        pass
    return data


# 向java socket写数据，末尾加\n
def json_send_helper(java_socket,json_data):
    message = json.dumps(json_data)
    message = (message+'\n').encode('utf-8')
    # print(f"[{threading.current_thread().name}->P] {message}")
    java_socket.send(message)

# 线程 注册执行器 actuator
def register_actuator(context_platform_addr,controller_status,sim_distance):
    actuator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    actuator_socket.bind(("127.0.0.1",51234))
    print(f"[actutor register] {context_platform_addr}")
    actuator_socket.connect(context_platform_addr)
    actuator_socket_buffer=b''

    actuator_config = {
        "name": "RoboMasterEPActor",
        "type": "Actor"
    }

    if not register_config_json_success(actuator_socket,actuator_config,actuator_socket_buffer):
        return

    print(f"[actutor register]")

    while True:
        if controller_status.value == -1: break
        while True:
            # try:
                msg = recv_helper(actuator_socket,actuator_socket_buffer)
                if msg is None:
                    return
                
                act_json = json.loads(msg)

                if (act_json['cmd'] == 'action_request'):
                    reply_json = {
                        'cmd':'action_back',
                        'message':True}
                    cmd_str = act_json['message']
                    if (cmd_str.startswith("SAFE: chassis move")):
                        api_json = get_move_action(cmd_str)
                    elif (cmd_str.startswith("SAFE: chassis speed")):
                        api_json = get_chassis_action(cmd_str)

                    print("[PT]",api_json)

                    if 'type' in api_json:
                        # 加入等待队列
                        action_json_sender(api_json)
                    
                    json_send_helper(actuator_socket,reply_json)
                    
            # except Exception as e:
            #     print("ERROR",e)
            #     break
    
    print(f"[actutor] end...")

# 线程 注册传感器 sensor
def register_sensor(context_platform_addr,controller_status,sim_distance):
    sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sensor_socket.bind(("127.0.0.1",54321))
    print(f"[sensor register] {context_platform_addr}")
    sensor_socket.connect(context_platform_addr)
    sensor_socket_buffer=b''

    sensor_config={
        "name": "RoboMasterEPSensor",
        "type": "Sensor",
        "fields": [
            "ir_distance",
            "chassis_status" 
        ]
    }

    if not register_config_json_success(sensor_socket,sensor_config,sensor_socket_buffer):
        return
    print(f"[sensor register]")

    while True:
        # try:
            if controller_status.value == -1: break
            while True:
                msg = recv_helper(sensor_socket,sensor_socket_buffer)
                if msg is None:
                    return
                
                snr_json = json.loads(msg)
                if snr_json['cmd'] != 'alive_request':
                    # print("loads",snr_json)
                    pass

                if (snr_json['cmd'] == 'sensory_request'):
                    # print("sensory")
                    sensor_data_json={
                        'ir_distance': copy.deepcopy(sim_distance),
                        'chassis_status': controller_status.value
                    }

                    # print("[Reply]",sensor_data_json)

                    reply_json = {
                        "cmd":"sensory_back",
                        'message':json.dumps(sensor_data_json)
                    }
                    
                    json_send_helper(sensor_socket,reply_json)
                        
        # except Exception as e:
        #     print("ERROR",e)
        #     break
    
    print(f"[sensor] end...")


def register_config_json_success(driver_socket,config_json,socket_buffer):
    register_json={
        'message': config_json,
        'cmd':'register'
    }
    json_send_helper(driver_socket, register_json)

    #接收注册结果
    register_back = recv_helper(driver_socket,socket_buffer)
    if register_back == None:
        return False
    obj = json.loads(register_back)
    if obj["cmd"] != "register_back" or obj["message"] != "true":
        return False

    return True

# 处理执行器指令 drive_speed
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
# 处理执行器指令 move
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

    # 线程 外部结束该进程
    exit_func = []
    t_closer = threading.Thread(
        target=window_outside_exiter, 
        args=(controller_status,exit_func))
    t_closer.daemon = True
    t_closer.start()

    # 线程 用于更新底盘状态
    t_update = threading.Thread(
        target=flush_controller_status, 
        args=(controller_status,controller_message))
    t_update.daemon = True
    t_update.start()

    # 线程 控制器
    t_actutor = threading.Thread(
        name='Actor',
        target=register_actuator, 
        args=(context_platform_addr,controller_status,sim_distance))
    t_actutor.daemon = True
    t_actutor.start()
    
    # 线程 传感器
    t_sensor = threading.Thread(
        name='Sensor',
        target=register_sensor, 
        args=(context_platform_addr,controller_status,sim_distance))
    t_sensor.daemon = True
    t_sensor.start()

    # 主程序 检测并退出
    while True:
        if controller_status.value == -1: break
        time.sleep(3)

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