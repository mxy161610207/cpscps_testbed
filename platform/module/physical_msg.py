import threading
import json
import time
from .sensor_source import SensorSource
from .sensor_source import LOCATION_PORT
from location.location_config import SystemState

# Data from physical  
class PhysicalMsg(SensorSource):
    def __init__(self,car_handler):
        print("Register Phy Sensor sender")
        super(PhysicalMsg,self).__init__(port=LOCATION_PORT,tag="P")
        self._car_handler=car_handler

        self._sys_sub_modules = []

        # python list is thread-safe
        self._wait_list=[]
        self._wait_list_lock=threading.Lock()

    # 小车发送数据包的处理
    def sender_send_json(self,send_json,need_reply = False):
        send_json['term_id']=self.sender._get_term_id()
        send_json['time']=time.time()
        if (need_reply):
            # print("[query]",send_json)
            self._wait_list_lock.acquire()
            self._wait_list.append(send_json)
            self._wait_list_lock.release()
            
            # if (self.query_type == "snapshot"):
            #     print("snapshot acquire lock")
        
        send_info=json.dumps(send_json)
        self.sender.send_msg(send_info)

        # if send_json['type']=='SENSOR_TYPE':
        #     print("sd:",send_json)
        
        if (need_reply):
            send_json['status']='wait'
            print("[query]", send_json)
        pass

    # 小车收到json的处理
    def handle_recv_json(self,recv_json):
        print("[get reply_json]",recv_json)
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
                if (time.time()-cur_json['time']>5):
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
        self.angle_init_once = False
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
        stop_tag=self.security_monitor.check_is_trigger(min_distance)

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
            self._car_handler._security_monitor.load_trigger_json(sensor_json)
        return 

    def set_angle_data_info(self, data_info):
        self.info._set_angle_data_info(data_info)
        a,b,c,d = data_info
        if (not self.angle_init_once):
            self.angle_init_once=True
            self.angle_init_val = d
            print("init angle to {}".format(self.angle_init_val))

        angle_json={
            'type':'ANGLE_TYPE',
            'info':{
                'angle':d-self.angle_init_val,
                'raw_angle':d
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
        self.sender_send_json(system_json, need_reply=False)
        return

    def location_server_reset(self):
        system_json={
            'type':'SYSTEM_TYPE',
            'info':{
                'next_state': SystemState.INIT.name
            }
        }
        self.angle_init_once = False
        self.sender_send_json(system_json, need_reply=False)
        return


    # unused 小车动作检测
    # def explore_action(self,msg):
    #     reply = self.sender.send_msg(msg, need_reply=True)
    #     self.sender.send_msg(msg, need_reply=True)
    #     self.sender.query_event.wait()
    #     reply = self.sender.get_reply()

    #     return reply

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
