import time
import socket
import queue
import threading
import warnings
import copy
import json

SERVER_IP = '127.0.0.1'
IR_SENSOR_PORT = 41997
LOCATION_PORT = 41234
SAFE_CHECK_PORT = 41998
UNUSED_PORT=42143

class SensorSourceSender:
    def __init__(self,ip=SERVER_IP,port=42143,manager=None) -> None:
        self._server_addr=(ip,port)
        self._manager=manager
        
        self.term_id_lock = threading.Lock()
        self.term_id=0
        
        self.start_recv_thread()

        self._handle_recv_func=None
        pass
    
    def _get_term_id(self):
        self.term_id_lock.acquire()
        curr_id = self.term_id
        self.term_id = (self.term_id+1) % 1000
        self.term_id_lock.release()
        return curr_id

    def create_init_msg(self):
        init_msg_json={'type':'INIT'}
        msg_str=json.dumps(init_msg_json)
        return msg_str

    def start_recv_thread(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.t_recv = threading.Thread(target=self.recv_msg)
        self.t_recv.daemon = True
        self.t_recv.start()

    # 每次要发消息时调用一下
    def send_msg(self,send_info):
        self.server_socket.sendto(send_info.encode('utf-8'),self._server_addr)
        pass
        
    # While True的线程 一直等待消息
    def recv_msg(self):
        # 先测试这个接口是否是有效接口
        self.server_socket.sendto(self.create_init_msg().encode('utf-8'),self._server_addr)
        while True:
            try:
                recv_info, _ = self.server_socket.recvfrom(1024)
            except Exception as e:
                print(e)
                print('远程主机已关闭 (addr)=',self._server_addr)
                print('是否忘记打开服务器定位端？..')
                break
            recv_info = recv_info.decode('utf-8')
            # print("[{2}] {0} \t  服务器端消息：{1}".format(
            #       time.asctime(time.localtime()), recv_info,self._server_addr))

            if (recv_info=='quit'):break
            if (recv_info=='ack'):continue

            recv_json=json.loads(recv_info)
            self._handle_recv_json(recv_json)
        
        # self.udp_send.kill()
        self.server_socket.close()
    
    # 每次收到消息后的处理
    def _handle_recv_json(self,recv_json):
        if (self._manager is None): return
        if (self._manager.handle_recv_json is None):
            return

        self._manager.handle_recv_json(recv_json)

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

class SensorSource:
    def __init__(self,port,tag):
        self.sender=SensorSourceSender(SERVER_IP,port,self)
        self.info=SensorSourceInfo()
        self._status = False
        self.set_online()
        
    def set_online(self):
        self._status = True
    
    @property
    def is_online(self):
        return self._status

# Data from simulate 
 
class SimulateMsg(SensorSource):
    def __init__(self):
        super(SimulateMsg,self).__init__(port=IR_SENSOR_PORT,tag="Sim")
    
    '''
    explore for different action API:
        format: "? action [action_api] *args"
    
    1) move
        ? action move {x} {y} {z} {xy_spd} {z_spd}
    2) drive_speed #TODO
        ? action drive_speed {x_spd} {y_spd} {z_spd}
    '''
    def handle_query_reply(self,reply_data):
        reply_data = eval(reply_data)
        # print("SIM:",reply_data)
        F,B,L,R,time_tag,t = reply_data
        self.set_sensor_data_info([F,R,B,L])
        if (time_tag):
            time_gap = time.time()-t
            if (time_gap > 0.15): 
                s = "\ncycle: {:.6f}".format(time_gap)
                # warnings.warn(s,UserWarning)
