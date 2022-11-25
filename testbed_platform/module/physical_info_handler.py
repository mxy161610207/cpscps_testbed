import threading
import json
import time
import random
from .sensor_source import SensorSourceHandler
from location.location_config import SystemState

# Data from physical  
class PhysicalInfoHandler(SensorSourceHandler):
    def __init__(self,syncer, self_addr,server_addr,car_handler):
        print("__init__ PhysicalInfoHandler start")
        super().__init__(self_addr,server_addr ,tag = 'P')

        self._position_syncer = syncer
        self._car_handler=car_handler
        self._sys_sub_modules = []

        # python list is thread-safe
        # 暂存需要回复的数据包
        self._wait_list=[]
        self._wait_list_lock=threading.Lock()
        print("__init__ PhysicalInfoHandler end")

    # Phycial端 - 小车发送数据包的处理
    # 1) 添加term_id和发送时间time
    # 2) 对需要回复的packet, 添加进等待队列
    def sender_send_json(self,send_json,need_reply = False):
        # print("ok", self.sender)
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

    # Phycial端 - 小车收到回复数据包的处理
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
         
    # 小车的模块订阅
    def sys_add_sub_module(self,module):
        self._sys_sub_modules.append(module)

    def sys_sub_all(self):
        print("开启platfrom订阅")
        for module in self._sys_sub_modules:
            module.sys_sub()

    def sys_unsub_all(self):
        for module in self._sys_sub_modules:
            module.sys_unsub() 

    # 小车本地数据上传到定位server
    def set_sensor_data_info(self, data_info):
        self.info._set_sensor_data_info(data_info)
        cur_distance=self.info.get_sensor_data_info()[:]
        F,R,B,L = cur_distance
        min_distance = min(cur_distance)
        #error here
        # print(1)
        security_monitor = self._car_handler._security_monitor
        stop_tag=security_monitor.check_is_trigger(min_distance)
        # print(2)

        sensor_json={
            'type':'SENSOR_TYPE',
            'info':{
                'sensor_info':[F,B,L,R],
                'need_location':stop_tag
            }
        }
        
        # print("to_send",sensor_json)

        self.sender_send_json(sensor_json,need_reply=stop_tag)
        # tid = self.sender.send_msg(msg,need_reply=stop_tag)

        if stop_tag:
            print("stop tag",sensor_json)
            # TODO
            security_monitor.load_trigger_json(sensor_json)
        return 

    def set_angle_data_info(self, data_info):
        self.info._set_angle_data_info(data_info)
        # d - yaw_ground_angle: 上电时刻yaw轴角度
        # 小车一开始向x轴正方向放，保证上电时刻=0
        a,b,c,d = data_info

        angle_json={
            'type':'ANGLE_TYPE',
            'info':{
                'yaw_ground_angle':d
            }
        }

        self.sender_send_json(angle_json,need_reply=False)
        # print("to_send",angle_json)
        return


    def send_action_info(self,action_info):
        # action_info = "move,x,y,z,xy_spd,z_spd"
        action_json={
            'type':'ACTION_TYPE',
            'info':action_info
        }
        
        self.sender_send_json(action_json,need_reply=False)
        # print("to_send",action_json)
        return

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
        # print("[********]send_adjust_status is_on = ",is_on)
        self.sender_send_json(system_json, need_reply=False)
        return

    def location_server_reset(self):
        system_json={
            'type':'SYSTEM_TYPE',
            'info':{
                'next_state': SystemState.NORMAL.name
            }
        }
        self.sender_send_json(system_json, need_reply=False)
        return

    def simulate_syncer_update(self,pos_info):
        syncer_json={
            'type':'SIMULATE',
            'info': pos_info
        }
        self.sender_send_json(syncer_json, need_reply=False)
        return
    
    def send_server_sync_json(self, is_reset = False):
        sync_json={
            'type':'SYNC',
            'info':{
                'status': 'init' if is_reset else 'sync',
                'sync_code': random.randint(0,10000)
            }
        }

        print('和Location服务器 初始化同步中... | sync code = {}'.format(sync_json['info']['sync_code']))

        self.sender_send_json(sync_json,need_reply=True)

        while('status' not in sync_json or sync_json['status']=='wait'):
            # time.sleep(1)
            # print("[query_status]",query_json['status'])
            continue

        if (sync_json['status']=='timeout'):
            return False
        return True

    # TODO 既然有了syncer，除了 stop tag，其他查询应该直接从sync获取
    def query_position(self):
        query_json={
            'type':'QUERY',
            'info':{
                'query_type':'position'
            }
        }
        
        self.sender_send_json(query_json,need_reply=True)
            
        # print("send success")

        while('status' not in query_json or query_json['status']=='wait'):
            # time.sleep(1)
            # print("[query_status]",query_json['status'])
            continue
        reply = query_json['reply']['info']

        return reply
