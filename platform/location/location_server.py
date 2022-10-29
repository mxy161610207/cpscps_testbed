# this module help recv & send position data

import json
from socket import *
import threading
import time
import queue

from .location_calculater import LocationCalculater
from .location_config import OUTPUT_DIR,SERVER_IP,LOCATION_PORT

class LocationServer:
    def __init__(self):
        print("__init__ LocationServer start")
        self.name = 'LocationServer'
        self.log = open(OUTPUT_DIR+"recv-{}.txt".format(time.time()),"w")

        self._code_mode = "utf-8"
        self._reply_addr = None

        self._send_msg_queue = queue.Queue(64)

        self._shutdown = False

        # creaete calculate module
        self.calculater = LocationCalculater(self) 
        
        print("__init__ LocationServer end")

    def is_shutdown(self):
        return self._shutdown

    def set_shutdown(self):
        print("set status shutdown")
        self._shutdown = True

    def get_grd_display_info(self,sz=5):
        loc_list = self.calculater.location_grd
        pos_dict_list = loc_list.get_latest_pos(sz)
        return pos_dict_list

    # def get_sim_display_info(self,sz=5):
    #     loc_list = self.calculater.location._sim_pair
    #     pos_dict_list = loc_list.get_latest_pos(sz)
    #     return pos_dict_list

    def start_udp_server(self):
        self.server_socket = socket(AF_INET, SOCK_DGRAM) 
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
        self.server_socket.bind((SERVER_IP, LOCATION_PORT))
        print("[LocationServer] port start {}".format(LOCATION_PORT))

        # start send msg threading
        t=threading.Thread(target=self.send_msg,args=())
        t.daemon = True 
        t.start()   

        t=threading.Thread(target=self.recv_msg,args=())
        t.daemon = True 
        t.start()   

        while True:
            if (self._shutdown): break
            time.sleep(3)
        
        print("[LocationServer] port end {}".format(LOCATION_PORT))


    def recv_msg(self):
        # while true - recv message
        while True:
            if (self._shutdown): break

            recv_info, recv_addr = self.server_socket.recvfrom(1024)
            self._reply_addr = recv_addr

            recv_info = recv_info.decode(self._code_mode) 
            print(recv_info,file=self.log)

            recv_json = json.loads(recv_info)
            self.handle_msg(recv_json)

    def send_msg(self):
        # while true - send message
        while True:
            if (self._reply_addr is None): continue
            
            send_json = self._send_msg_queue.get()
            # print("[send reply_json]",send_json)
            send_msg=json.dumps(send_json)

            # print(msg)
            print("#"+send_msg,file=self.log)
            self.server_socket.sendto(send_msg.encode(self._code_mode), self._reply_addr) 

    def handle_msg(self,msg_json:json):
        if msg_json['type']=='INIT': return
        self.calculater.info_queue.put(msg_json)    

    def __del__(self):
        self.log.close()
        print("__del__ LocationServer end")
        pass

    def bind_simulte_map(self,simulate_map):
        print('bind sim map succeed')
        self.calculater.bind_map = simulate_map
        self.calculater.bind_map_update()

def raise_location_server(proc_name,loc_server):
    print("Proc [{}] start".format(proc_name))
    
    # out_file = open(out_dir+"/detail.txt","w")
    # print("- proc output to file:",out_dir+"/detail.txt")
    # sys.stdout = out_file

    loc_server.start_udp_server()

    print("Proc [{}] end".format(proc_name))
