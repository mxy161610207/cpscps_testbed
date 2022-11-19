from multiprocessing.managers import BaseManager
from multiprocessing import Value,Process,Queue,Manager

import time

# platform

from location import location_server
from ui import display_resource_manager 
from ui import display_raiser

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


    # ------ 进程按顺序开启 -------
    # 1) 定位服务器进程
    proc_server.start()
    location_server_status = platform_status_resources['location']
    while (location_server_status.value == 0):
        time.sleep(1)

    print("---- processor [proc_server] start ----\n" *10)


    # 2) 小车状态进程
    proc_platform.start()
    sdk_platform_status = platform_status_resources['sdk']
    # while (sdk_platform_status.value == 0):
    #     print("here")
    #     time.sleep(1)

    time.sleep(2)# 假装小车运行成功

    # 3) 前端显示进程
    proc_display.start()
    proc_display.join()


    # TODO 如果用户重启系统。

    # # proc_sim_engine.start()

    # if proc_server be terminated
    # user kill the server, join end.

    # if (loc_server_status.value==2):
    #     loc_manager.set_shutdown()

    # sim_manager = BaseManager()
    # sim_manager.register('simulate_map',simulate_map.SimulateMap)
    # sim_manager.start()



    # simulate_map = sim_manager.simulate_map()
    # loc_server.bind_simulte_map(simulate_map)
    

    


    # process_name = 'raise_simulate_engine'
    # proc_sim_engine = multiprocessing.Process(
    #     target=engine_conn.raise_simulate_engine,
    #     args=(process_name,loc_server,simulate_map)
    # )



    # # check is necessary to raise a new server
    # while loc_server_status.value == 1:
    #     # if RESET by user, raise a new server and registered in DispalyResourceManager
    #     print("Server [RESET] by user({}), waiting for a new server...".format(loc_server_status.value))
    #     loc_server_status.value=0

    #     # create new server
    #     loc_server = loc_manager.location_server()
    #     process_name = 'raise_location_server'
    #     proc_server = multiprocessing.Process(
    #         target=location_conn.raise_location_server,
    #         args=(process_name,loc_server)
    #     )
    #     proc_server.daemon = True
    #     proc_server.start()
    #     # register
    #     res_manager.register_location_server(loc_server)
    #     print("Server [RESET] ({})...".format(loc_server_status.value))

    #     # reset success           
    #     print("RESET succeed!")
    #     if (loc_server_status.value==0):
    #         proc_server.join()     
    #     else:
    #         proc_server.terminate()

    # print("Server [SHUTDOWN] by user({}), waiting for other processing ending...".format(loc_server_status.value))

    # proc_display.terminate()
    # proc_sim_engine.terminate()

