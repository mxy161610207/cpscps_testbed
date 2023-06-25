# this module help recv & send position data

import json
from socket import *
import threading
import time
import queue

from .location_calculater import LocationCalculater
from .location_config import OUTPUT_DIR

class LocationServer:
    def __init__(self,
        grd_location_syncer,sim_location_syncer,
        location_server_status,
        location_server_addr, physical_sender_addr,
        is_square_court
        ):
        print("__init__ LocationServer start")
        self.name = 'LocationServer'
        self.log = open(OUTPUT_DIR+"recv-{}.txt".format(time.time()), "w")

        self._code_mode = "utf-8"
        self._self_addr = location_server_addr
        self._reply_addr = physical_sender_addr
        self._is_square_court = is_square_court

        self._send_msg_queue = queue.Queue(64)

        self._status = location_server_status
        self._shutdown = False

        # creaete calculate module
        self.calculater = LocationCalculater(
            self, grd_location_syncer, sim_location_syncer)

        print("__init__ LocationServer end")

    def is_shutdown(self):
        return self._shutdown or self._status.value == -1

    # def get_grd_display_info(self,sz=5):
    #     loc_list = self.calculater.location_grd
    #     pos_dict_list = loc_list.get_latest_pos(sz)
    #     return pos_dict_list

    # def get_sim_display_info(self,sz=5):
    #     loc_list = self.calculater.location._sim_pair
    #     pos_dict_list = loc_list.get_latest_pos(sz)
    #     return pos_dict_list

    def start_udp_server(self):
        self.server_socket = socket(AF_INET, SOCK_DGRAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
        self.server_socket.bind(self._self_addr)
        print("[LocationServer] address start {}".format(self._self_addr))

        # start send msg threading
        t = threading.Thread(target=self.send_msg, args=())
        t.daemon = True
        t.start()

        t = threading.Thread(target=self.recv_msg, args=())
        t.daemon = True
        t.start()

        # location server 正常工作中
        self._status.value = 1

        while True:
            if (self.is_shutdown()): break
            time.sleep(3)

        self.server_socket.close()
        print("[LocationServer] address end {}".format(self._self_addr))

    def recv_msg(self):
        # while true - recv message
        while True:
            if (self.is_shutdown()): break

            try:
                recv_info, recv_addr = self.server_socket.recvfrom(1024)
            except Exception as e:
                print("[location_server error] recv failed")
                break

            if recv_addr!= self._reply_addr:
                print("[drop] recv addr {} not match {}".format(
                    recv_addr, self._reply_addr))

            recv_info = recv_info.decode(self._code_mode)
            print(recv_info, file=self.log)

            recv_json = json.loads(recv_info)
            if recv_json['type']=='SYSTEM_TYPE':
                print(recv_json['info'])
            if (not self._is_square_court): continue
            self.handle_msg(recv_json)
        
        if (not self.is_shutdown()): self._status.value == -1

    def send_msg(self):
        # while true - send message
        while True:
            # if (self._reply_addr is None):
            #     continue
            send_json = self._send_msg_queue.get()
            # print("[send reply_json]",send_json)
            send_msg = json.dumps(send_json)

            # print(msg)
            print("[location] reply"+send_msg, file=self.log)
            # print("[location] reply to {} | msg={}".format(self._reply_addr,send_msg))
            try:
                self.server_socket.sendto(send_msg.encode(
                    self._code_mode), self._reply_addr)
            except Exception as e:
                print("[location_server error] send failed")
                break
        
        if (not self.is_shutdown()): self._status.value == -1


    def make_sync_reply(self, sync_json):
        qid = sync_json['term_id']
        sync_code = sync_json['info']['sync_code']
        sync_status = sync_json['info']['status']

        if (sync_status == 'init'):
            #TODO reset
            pass

        reply_json = {
            'query_id': qid,
            'type': 'sync',
            'info': {
                'sync_code': sync_code
            }
        }
        self._send_msg_queue.put(reply_json)

    def handle_msg(self, msg_json: json):
        if msg_json['type'] == 'SYNC':
            self.make_sync_reply(msg_json)
            return
        self.calculater.info_queue.put(msg_json)

    def __del__(self):
        self.log.close()
        print("__del__ LocationServer end")
        pass

    # def bind_simulte_map(self, simulate_map):
    #     print('bind sim map succeed')
    #     self.calculater.bind_map = simulate_map
    #     self.calculater.bind_map_update()

def closer(
    platform_status_resources,
    platform_message_resources,
    platform_socket_address):

    location_server_status = platform_status_resources['location']

    if (location_server_status.value == -1):
        return

    location_server_status.value = -1

    return

def raiser(
        proc_name,
        platform_status_resources,
        platform_message_resources,
        platform_socket_address):
    print("Proc [{}] start".format(proc_name))

    # out_file = open(out_dir+"/detail.txt","w")
    # print("- proc output to file:",out_dir+"/detail.txt")
    # sys.stdout = out_file

    grd_location_syncer = platform_message_resources['grd_position']
    sim_location_syncer = platform_message_resources['sim_position'] 

    location_server_status = platform_status_resources['location']
    square_court_status = platform_status_resources['square_court']

    physical_sender_addr = platform_socket_address['phy_sender']
    location_server_addr = platform_socket_address['location']

    loc_server = LocationServer(
        grd_location_syncer,sim_location_syncer,
        location_server_status,
        location_server_addr, physical_sender_addr,
        square_court_status.value)
    loc_server.start_udp_server()

    # 如果服务器停止运行，说明 location_server_status.value == -1
    # 此时其他模块需要退出
    global_status = platform_status_resources['global']
    global_status.value = -1

    print("Proc [{}] end".format(proc_name))
