import time
import socket
import queue
import threading
import warnings
import copy
import json

from abc import abstractmethod

class SensorSourceSender:
    def __init__(self,self_addr,server_addr,manager) -> None:
        self._manager=manager
        
        self.term_id_lock = threading.Lock()
        self.term_id=0

        self._client_addr = self_addr
        self._server_addr = server_addr
        self.start_recv_thread()

        self._handle_recv_func=None
        pass
    
    def _get_term_id(self):
        self.term_id_lock.acquire()
        curr_id = self.term_id
        self.term_id = (self.term_id+1) % 10000
        self.term_id_lock.release()
        return curr_id

    @classmethod
    def create_init_msg(self):
        init_msg_json={'type':'INIT'}
        msg_str=json.dumps(init_msg_json)
        return msg_str

    def start_recv_thread(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(self._client_addr)

        self.t_recv = threading.Thread(target=self.recv_msg)
        self.t_recv.daemon = True
        self.t_recv.start()

    # 每次要发消息时调用一下
    def send_msg(self,send_info):
        self.server_socket.sendto(send_info.encode('utf-8'),self._server_addr)
        pass
        
    # 线程 - While True 一直接受消息
    def recv_msg(self):
        # 先测试这个接口是否是有效接口
        # while not self._manager.send_server_sync_json(is_reset=True):
        #     time.sleep(1)

        print('[sdk] recv_msg 进程已启动, bind {}, recv_from {}'.format(
            self._client_addr,self._server_addr))

        while True:
            try:
                recv_info, _ = self.server_socket.recvfrom(1024)
            except Exception as e:
                print(e)
                print('远程主机已关闭 (addr)=',self._server_addr)
                break
            recv_info = recv_info.decode('utf-8')
            # print("[sdk recv] {0} \t  服务器端消息：{1}".format(
            #       time.asctime(time.localtime()), recv_info))

            if (recv_info=='quit'):break
            if (recv_info=='ack'):continue

            recv_json=json.loads(recv_info)
            self._manager.handle_recv_json(recv_json)
        
        # self.udp_send.kill()
        
        print('数据接受线程{}终止,端口{}关闭'.format(
            self._manager._tag,
            self._client_addr))

        self.server_socket.close()

class SensorSourceInfo:
    def __init__(self,tag=""):
        self._tag=tag
        self._distance = [0] * 4
        self._yaw_angle = 0
        self._pitch_angle = 0
        self._yaw_ground_angle = 0
        self._pitch_ground_angle = 0
        self._cv2_image = None

    def _set_sensor_data_info(self, data_info):
        self._distance = data_info[:]
        # if (self._tag=='S'):
        #     d = self._distance
        #     print("[source-{}] tof1:{}  tof2:{}  tof3:{}  tof4:{}".format(self._tag, \
        #         d[0], d[1], d[2], d[3]))
    
    def _set_angle_data_info(self, data_info):
        self._pitch_angle, self._yaw_angle, self._pitch_ground_angle, self._yaw_ground_angle = data_info[:]
        # print("[source-{}] angle:{}".format(self._tag, self._yaw_ground_angle))

    def get_sensor_data_info(self):
        return self._distance 

    def _set_cv2_image(self, img):
        self._cv2_image = img

    def get_cv2_image(self):
        if self._cv2_image is None:
            return None
        return self._cv2_image

class SensorSourceHandler:
    def __init__(self,self_addr,server_addr ,tag):
        self._tag = tag

        self.sender = SensorSourceSender(self_addr,server_addr,self)
        self.info   = SensorSourceInfo()
        self._online_status = False
        self.set_online()
        
    def set_online(self):
        self._online_status = True

    @property
    def is_online(self):
        return self._online_status

    # 每次收到消息后的处理
    @abstractmethod
    def handle_recv_json(self,recv_json):
        pass

    @classmethod
    def send_server_sync_json(self, is_reset = False):
        pass
 
