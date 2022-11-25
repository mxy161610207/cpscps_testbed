import threading
import json
import time
import random
from .sensor_source import SensorSourceHandler
from location.location_config import SystemState
from .platform_exception import PlatformException

# Data from Simulate  
class SimulateInfoHandler(SensorSourceHandler):
    def __init__(self,syncer, self_addr,server_addr,car_handler):
        print("__init__ SimulateInfoHandler start")
        super().__init__(self_addr,server_addr ,tag = 'S')
        
        self._position_syncer = syncer
        self._car_handler=car_handler
        self._sys_sub_modules = []

        # python list is thread-safe
        # 暂存需要回复的数据包
        self._wait_list=[]
        self._wait_list_lock=threading.Lock()
        print("__init__ SimulateInfoHandler end")

    # 发送端 - 小车发送数据包的处理
    # 1) 添加term_id和发送时间time
    # 2) 对需要回复的packet, 添加进等待队列
    def sender_send_json(self,send_json,need_reply = False):
        send_json['term_id']=self.sender._get_term_id()
        send_json['send_time']=time.time()

        if (need_reply):
            # print("[query]",send_json)
            self._wait_list_lock.acquire()
            self._wait_list.append(send_json)
            self._wait_list_lock.release()
        
        send_info=json.dumps(send_json)
        self.sender.send_msg(send_info)

        # if send_json['type']=='SENSOR_TYPE':
        #     print("sd:",send_json)
        
        if (need_reply):
            send_json['status']='wait'
            if (send_json['type']!='SYNC'):
                print("[query]", send_json)
        pass

    # 接受端 - 小车收到回复数据包的处理
    # "query_id": 对发送的指定term_id的回复
    # 更新json，追加回复，用户处理
    # 超时 删除数据包
    def handle_recv_json(self,recv_json):
        print("[get reply_json]",recv_json)
        
        # 莫名奇妙的回复
        if ("query_id" not in recv_json):
            pass

        qid = recv_json['query_id']
        self._wait_list_lock.acquire()

        n=len(self._wait_list)
        removed_json=[]
        for i in range(n):
            cur_json=self._wait_list[i]
            if (cur_json['term_id']==qid):
                cur_json['reply']= recv_json
                cur_json['status']='get'
                removed_json.append(cur_json)
            else:
                if (time.time()-cur_json['send_time']>5):
                    cur_json['status']='timeout'
                    removed_json.append(cur_json)
        
        for rjson in removed_json:
            self._wait_list.remove(rjson)

        self._wait_list_lock.release()
        return

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

    def update_distance_data_info(self):
        # {'F':f, 'L':l , 'B':b, 'R':r }
        dist_dict = self.query_sensor_data_info(self,'distance')
        data_info = [dist_dict['F'],dist_dict['R'],dist_dict['B'],dist_dict['L']]
        
        self.info._set_sensor_data_info(data_info)
        return data_info
        
    def update_angle_data_info(self):
        # _,_,_,d
        angle_val = self.query_sensor_data_info(self,'angle')
        data_info = [0,0,0,angle_val]
        
        self.info._set_angle_data_info(data_info)
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
