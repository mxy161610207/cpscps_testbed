from multiprocessing.managers import BaseManager
from multiprocessing import Value,Process

import time

# platform

from location import location_server
from ui import display_resource_manager 
from ui import display_raiser

import user_watcher

if __name__ == '__main__': 

    # --- multi-process Class Object ---
    loc_manager = BaseManager()
    loc_manager.register('location_server',location_server.LocationServer)
    loc_manager.start()

    # dsp_manager = BaseManager()
    # dsp_manager.register('resource_manager',display_resource_manager.DispalyResourceManager)
    # dsp_manager.start()

    # --- multi-processer ---
    # 1) 平台总进程
    process_name = 'raise_platform'
    proc_platform = Process(
        target=user_watcher.raise_platform,
        args=(process_name,)
    )
    proc_platform.daemon = True
    
    # 2) 定位系统进程
    loc_server = loc_manager.location_server()
    # 0/1/2 - server working/reset by user/shutdown by user
    loc_server_status = Value('i', 0)
    process_name = 'raise_location_server'
    proc_server = Process(
        target=location_server.raise_location_server,
        args=(process_name,loc_server)
    )
    proc_server.daemon = True
  
    # 3) 前端显示进程
    # res_manager = dsp_manager.resource_manager()
    # res_manager.register_location_server(loc_server)
    # process_name = 'raise_display'
    # proc_display = Process(
    #     target=display_raiser.raise_loction_display,
    #     args=(process_name,res_manager,loc_server_status)
    # )

    proc_server.start()
    time.sleep(1)
    proc_platform.start()
    # proc_display.start()
    # # proc_sim_engine.start()

    # if proc_server be terminated
    # user kill the server, join end.
    proc_server.join()

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

