from multiprocessing.managers import BaseManager
from multiprocessing import Value,Process,Queue,Manager

import time

# platform

from location import location_server
from ui import display_raiser
from ui.controller import controller_raiser

from module import sdk_handler


if __name__ == '__main__': 
    # 系统多进程资源
    platform_manager = Manager()    

    platform_status_resources = {}
    platform_message_resources = {}
    platform_socket_address = {
        'phy_sender': ('127.0.0.1', 41997),
        'sdk' : ('127.0.0.1', 41011),
        'location': ('127.0.0.1', 41234),
    }
    
    platform_status_resources['global'] = Value('i',0)

    # --- 定位系统工具 ---
    platform_status_resources['location'] = Value('i',0)
    platform_message_resources['location'] = Queue(-1)
    platform_message_resources['grd_position'] = platform_manager.dict()
    platform_message_resources['sim_position'] = platform_manager.dict()

    # --- SDK通信工具 ---
    platform_status_resources['sdk'] = Value('i',0)
    platform_message_resources['sdk'] = Queue(-1)

    # --- 平台前端工具 ---
    platform_status_resources['display'] = Value('i',0)
    platform_message_resources['display'] = Queue(-1)

    # --- 用户操控工具 ---
    platform_status_resources['control'] = Value('i',0)
    platform_message_resources['control'] = Queue(-1)

    # --- 多进程处理器定义 ---
    # 1) 小车状态进程
    process_name = 'raise_sdk_handler'
    proc_platform = Process(
        target=sdk_handler.raiser,
        args=(  process_name,
                platform_status_resources,
                platform_message_resources,
                platform_socket_address)
    )
    proc_platform.daemon = True
    
    # 2) 定位系统进程
    process_name = 'raise_location_server'
    proc_server = Process(
        target=location_server.raiser,
        args=(  process_name,
                platform_status_resources,
                platform_message_resources,
                platform_socket_address)
    )
    proc_platform.daemon = True
  
    # 3) 前端显示进程
    process_name = 'raise_display'
    proc_display = Process(
        target=display_raiser.raiser,
        args=(  process_name,
                platform_status_resources,
                platform_message_resources,
                platform_socket_address)
    )

    # 4) 用户操作进程
    process_name = 'raise_controller'
    proc_controller = Process(
        target=controller_raiser.raiser,
        args=(  process_name,
                platform_status_resources,
                platform_message_resources,
                platform_socket_address)
    )
    proc_controller.is_alive()

    # ------ 进程按顺序开启 -------
    # 1) 定位服务器进程
    proc_server.start()
    location_server_status = platform_status_resources['location']
    while (location_server_status.value == 0):
        time.sleep(1)

    print("---- processor [proc_server] start ----\n")


    # 2) 小车状态进程
    proc_platform.start()
    sdk_platform_status = platform_status_resources['sdk']
    while (sdk_platform_status.value == 0):
        time.sleep(1)
    
    print("---- processor [proc_platform] start ----\n")

    # 3) 前端显示进程
    display_status = platform_status_resources['display']
    proc_display.start()

    # 4) 用户操作进程
    proc_controller.start()

    global_status = platform_status_resources['global']
    while True:
        if (global_status.value == -1):
            print("关闭所有资源中...")
            sdk_handler.closer(
                platform_status_resources,
                platform_message_resources,
                platform_socket_address)
            
            location_server.closer(
                platform_status_resources,
                platform_message_resources,
                platform_socket_address)
            
            display_raiser.closer(
                platform_status_resources,
                platform_message_resources,
                platform_socket_address)

            controller_raiser.closer(
                platform_status_resources,
                platform_message_resources,
                platform_socket_address)

            print("关闭完成...")
            break
        
        time.sleep(3)

    print("平台窗口关闭")