import threading
import json
import time
import random,math
from .sensor_source import SensorSourceHandler
from location.location_config import SystemState
from .platform_exception import PlatformException
from .noisy_generator import NoisyGenerator

# Data from Simulate  
class SimulateInfoHandler(SensorSourceHandler):
    def __init__(self,syncer, self_addr,server_addr,car_handler,sim_distance):
        print("__init__ SimulateInfoHandler start")
        super().__init__(self_addr,server_addr ,tag = 'S')
        
        self._position_syncer = syncer
        self._distance_syncer = sim_distance
        self._car_handler=car_handler
        self._sys_sub_modules = []

        self._program_run = False
        self._last_time = 0
        self._interval = 0.5

        self.noisy_generator = NoisyGenerator()

        self.last_position = None
        self.position_thread = threading.Thread(target=self.send_position, args=())
        self.position_thread.daemon = True
        self.position_thread.start()

        # python list is thread-safe
        # 暂存需要回复的数据包
        self._wait_list=[]
        self._wait_list_lock=threading.Lock()
        print("__init__ SimulateInfoHandler end")

    # 返回值：
    # x - 向前移动距离
    # y - 向左移动距离
    # deg - 逆时针旋转角度
    def get_diff_json(self,last,cur):
        # rad = (rad - math.pi/2.0)
        rad = math.radians(last['deg'])

        dx = cur['x']-last['x']
        dy = cur['y']-last['y']
        ddeg = cur['deg']-last['deg']
        drad = math.radians(ddeg)

        rot_mat = [ [math.cos(rad), math.sin(rad)],     # 前方
                    [-math.sin(rad), math.cos(rad)]]    # 左方
        # print("rot_mat =",rot_mat)
        # print("dx dy =",dx,dy)
        tx = rot_mat[0][0]*dx + rot_mat[0][1]*dy
        ty = rot_mat[1][0]*dx + rot_mat[1][1]*dy
        # print("tx ty =",tx,ty)

        diff_json={
            'x':tx,
            'y':ty,
            'deg':ddeg,
            'rad':drad
        }

        return diff_json
    
    def append_phy_position_file(self,cur_position):
        if (not self._program_run): return
        cur_time = time.time()
        if (cur_time-self._last_time>=self._interval):
            self._last_time = cur_time

            with open('filename.txt', 'a') as f:
                line = "{} {} {} {}\n".format(
                    self._car_handler._adjust_state.value == 0,
                    cur_position['x'],cur_position['y'],cur_position['deg']
                )
                f.write(line)

    def send_position(self):
        # fake instead

        time.sleep(1)
        self.last_position = self._car_handler._phy_msg_sender.query_position()

        while True:
            cur_position = self._car_handler._phy_msg_sender.query_position()
            self.append_phy_position_file(cur_position)
            
            has_diff=False

            diff_json = self.get_diff_json(self.last_position,cur_position)

            for key in ['x','y','deg','rad']:
                if (abs(diff_json[key])>0.1): 
                     has_diff = True

                    
            if (not has_diff): 
                time.sleep(0.1)
                continue
            
            # print(self.last_position)
            # print(diff_json)

            # print (cur_position,diff)
            try:
                if (self._car_handler._adjust_state.value == 0):
                    # raise Exception("None")
                    # print("normal")
                    self.sender_send_json(diff_json)
                else:
                    # print("drop",diff_json)
                    pass
            except Exception as e:
                # print(e)
                # print(self.sender._server_addr)
                pass
            else:
                self.last_position = cur_position
                
            time.sleep(0.05)

    def send_status(self,status='init'):
        status_json={
            'type':'system',
            'status':status
        }
        try:
            self.sender_send_json(status_json)
        except Exception as e:
            pass

                
    def handle_recv_json(self, recv_json):
        # print("[get sim_engine reply_json]",recv_json)
        
        json_type = recv_json['type']
        json_data = recv_json

        if json_type=='distance':
            dist_json = self.noisy_generator.convert_to_sdk_distance(json_data['data'])
            F,B,L,R = dist_json['result']
            self.info._set_sensor_data_info([F,R,B,L])
            self._distance_syncer['F']=F
            self._distance_syncer['R']=R
            self._distance_syncer['B']=B
            self._distance_syncer['L']=L
            # print("sim senser: [raw]",json_data['data'] ,"[md]",[F,R,B,L])

        elif json_type == 'event':
            # 发生碰撞了。
            pass

        elif json_type == 'figure':
            # 啥也不干
            pass

    # 发送端 - 小车发送数据包的处理
    def sender_send_json(self,send_json):
        # send_json['term_id']=self.sender._get_term_id()
        # send_json['send_time']=time.time()

        send_info=json.dumps(send_json)
        self.sender.send_msg(send_info)

        # if send_json['type']=='SENSOR_TYPE':
        #     print("sd:",send_json)


    # 开一个线程 一直发送小车位置更新
    
    # 发送 config 场景配置
    # 发送 position 小车位置更新

    def query_sensor_data_info(self, sensor_type):
        position_json = self.query_position()
        query_json={
            'type':'SENSOR',
            'info':{
                'sensor_type': sensor_type,
                'position': position_json
            }
        }

        self.sender_send_json(query_json,need_reply=True)

        while('status' not in query_json or query_json['status']=='wait'):
            # time.sleep(1)
            # print("[query_status]",query_json['status'])
            continue

        if (query_json['status']=='timeout'):
            print("Simulate Engine timeout...")
            raise PlatformException("")
            
        data_info = query_json['reply']['info']
        return data_info


    # def send_adjust_status(self,is_on=True):
    #     if is_on:
    #         nxt_state=SystemState.ADJUST.name
    #     else:
    #         nxt_state=SystemState.NORMAL.name
    #     system_json={
    #         'type':'SYSTEM_TYPE',
    #         'info':{
    #             'next_state':nxt_state
    #         }
    #     }
    #     self.sender_send_json(system_json, need_reply=False)
    #     return
    
    def location_server_reset(self):
        system_json={
            'type':'SYSTEM_TYPE',
            'info':{
                'next_state': SystemState.INIT.name
            }
        }
        self.sender_send_json(system_json, need_reply=False)
        return
    
    # [unused] 实际未用
    def send_server_sync_json(self):
        # 仅同步位置
        sync_json={
            'type':'SYNC',
            'info':{
                'position': self.query_position()
            }
        }

        print('和Simulate服务器 初始化同步中... | sync code = {}'.format(sync_json['info']['sync_code']))

        self.sender_send_json(sync_json,need_reply=False)

    def query_position(self):
        get_syncer = self._position_syncer

        position_json = {
            'x': get_syncer['x'],
            'y': get_syncer['y'],
            'deg': get_syncer['deg'],
            'rad': get_syncer['rad'],
        }
        return position_json
