import threading
import json
import time

import user_watcher

# 在PhysicalMsg.info的sensor满足条件时把车停下来，
# 并切换系统到ADJUST状态
class SecurityMonitor():
    def __init__(self,car_handler):
        self._car_handler = car_handler

        # 事件, 会被两种情况触发:
        # 1) 到达边界
        # 2) 动作完成
        self._event = threading.Event()
        self._event.set()

        # 触发理由
        self._set_reason = 'initial'
        # 如果理由是"STOP",触发的sensor
        self._set_json = None

        # 需要监视的动作
        self._trigger_obj = None
        self._trigger_api = ""
        # 需要监视的警戒线
        self._monitor_distance = -1
        pass

    # 设置警戒线，并开启一个等待event事件的进程
    def register_and_start(self,obj,check_distance = 200):
        self._set_json = None
        self._event.clear()

        auto_stop_thread = threading.Thread(target=self._auto_stop)
        auto_stop_thread.start()

        self._set_reason = 'wait'
        self._trigger_obj = obj
        self._monitor_distance = check_distance
    
    def wait_for_trigger(self):
        return self._event.wait()

    def is_accessable(self,obj):
        if (obj!=self._trigger_obj):
            return False
        return True

    # event被触发 set_msg = STOP->ADJUST / END
    # 1) 信息设置
    # 2) 一个等event的线程
    def event_set_by(self,set_msg):
        print("monitor set by",set_msg)
        self._monitor_distance = -1
        self._set_reason = set_msg
        self._event.set()
        # print("set event")

    # 判断每一次小车测距值是否会触发事件
    # 如果返回True，不久后会通过watch返回触发时的位置
    def check_is_trigger(self,min_distance):
        # 无警戒线
        if (self._monitor_distance<0): return False
        # 被STOP触发
        if (min_distance<=self._monitor_distance and not self.isSet()):
            self.event_set_by('STOP')
            # set() 之后 _auto_stop会停下小车
            return True
        return False
    
    def load_trigger_json(self,trigger_json):
        self._set_json=trigger_json
        pass

    def get_set_reason(self):
        while(self._set_reason=='STOP'):
            continue
        return self._set_reason
    
    def _get_set_reply(self):
        while(self._set_json['status']=='wait'):
            continue
        reply_json=self._set_json
        self._set_json=None
        return reply_json['reply']['info']

    def get_set_position(self):
        if (self._set_reason=='ADJUST'):
            # 主动停止
            pos=self._get_set_reply()
        else:
            # 正常结束
            pos=user_watcher.PHY_SENDER.query_position()
        return pos
    
    def isSet(self):
        return self._event.isSet()



    # def get_set_tid(self):
    #     tid = self._set_tid
    #     while (tid==-1):
    #         tid = self._set_tid
    #     return tid

    # def set_tid(self,tid):
    #     print("cur tid =",tid)
    #     self._set_tid = tid

    # 事件触发后的处理：
    # 如果被STOP set：
    #   说明小车正在行驶且处于边界，需要主动停止车辆【设置速度为0
    #   此时小车状态变为ADJUST
    # 如果被其他 set: pass
    def _auto_stop(self):
        self._event.wait()
        # print("stop wait success")
        if (self._set_reason=='STOP'):
            print("stop car")
            user_watcher.EP_ROBOT.chassis._dij_drive_speed(0, 0, 0)
            self._set_reason='ADJUST'

    def adjust(self,api,obj,is_manual=False):
        user_watcher.CAR_HANDLER.flush_undefined_behavior()
        print("adjust for",api)
        if api=='move':
            print(obj.percent_str)
        else:
            pass
        
        user_watcher.CAR_HANDLER.adjust(is_manual)
