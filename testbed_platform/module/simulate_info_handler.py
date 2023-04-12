import threading
import json
import time
import random
from .sensor_source import SensorSourceHandler
from location.location_config import SystemState
from .platform_exception import PlatformException
from .noisy_generator import NoisyGenerator

# Data from Simulate  
class SimulateInfoHandler(SensorSourceHandler):
    def __init__(self,syncer, self_addr,server_addr,car_handler):
        print("__init__ SimulateInfoHandler start")
        super().__init__(self_addr,server_addr ,tag = 'S')
        
        self._position_syncer = syncer
        self._car_handler=car_handler
        self._sys_sub_modules = []

        self.noisy_generator = NoisyGenerator()

        # python list is thread-safe
        # 暂存需要回复的数据包
        self._wait_list=[]
        self._wait_list_lock=threading.Lock()
        print("__init__ SimulateInfoHandler end")


    def handle_recv_json(self, recv_json):
        print("[get sim_engine reply_json]",recv_json)
        
        json_type = recv_json['type']
        json_data = recv_json['data']

        if json_type=='distance':
            dist_json = self.noisy_generator.convert_to_sdk_distance(json_data)
            F,B,L,R = dist_json['result']
            self.info._set_sensor_data_info([F,R,B,L])

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


    def send_adjust_status(self,is_on=True):
        if is_on:
            nxt_state=SystemState.ADJUST.name
        else:
            nxt_state=SystemState.NORMAL.name
        system_json={
            'type':'SYSTEM_TYPE',
            'info':{
                'next_state':nxt_state
            }
        }
        self.sender_send_json(system_json, need_reply=False)
        return
    
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
        position_json = {
            'x': self._position_syncer['x'],
            'y': self._position_syncer['y'],
            'deg': self._position_syncer['deg'],
            'rad': self._position_syncer['rad'],
        }
        return position_json
