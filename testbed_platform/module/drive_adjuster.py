# from robomaster.chassis import *

import threading

# from robomaster import logger
# from robomaster import action

from module import sdk_handler
from module.platform_exception import PlatformException
from module.platform_timer import PlatformTimer
# from location.location_list import ActionMonitor

'''
class DriveSpeedAdjuster()

新加的类: DriveSpeedAdjuster
用于将一个Drive类型分阶段完成，且在阶段间插入调整动作
'''
class DriveSpeedAdjuster():
    def __init__(self, car_handler) :
        self._car_handler = car_handler

        self._chassis = None

        # 同时只watch一个proto
        self._proto_register_event=threading.Event()
        self._proto_register_lock = threading.Lock()
        self._proto_register_event.clear()
        self._run_proto = None
        self._run_timeout = None

        # 一直接受proto的程序
        self._event = None
        self.monitor_thread = threading.Thread(target=self.run_monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def _encode_drive_proto(self, proto):
        encode_json={
            'api':'move',
            'x':proto._x_spd,
            'y':proto._y_spd,
            'z':proto._z_spd,
            'spd_xy':3,
            'spd_z':3,
        }
        return encode_json

    def register_proto(self, chassis, proto, timeout):
        if (self._chassis is None): self._chassis = chassis
        if (self._run_proto is not None):
            self.proto_clear()
        
        self._proto_register_lock.acquire()
        self._run_proto = proto
        self._run_timeout = timeout

        if timeout:
            if self._chassis._auto_timer:
                if self._chassis._auto_timer.is_alive():
                    self._chassis._auto_timer.cancel()
            self._chassis._auto_timer = PlatformTimer(timeout, self._chassis._auto_stop_timer, args=("drive_wheels",))
            self._chassis._auto_timer.start()

        self._proto_register_event.set()      
        self._proto_register_lock.release()

        sdk_handler.PHY_SENDER.send_action_info(self._encode_drive_proto(self._run_proto))
        return self._chassis._send_sync_proto(proto)

    def proto_clear(self):
        self._proto_register_lock.acquire()

        if (self._run_timeout):
            if self._chassis._auto_timer:
                if self._chassis._auto_timer.is_alive():
                    self._chassis._auto_timer.cancel()
                    sdk_handler.SECURITY_MONITOR.event_set_by("END")
            self._chassis._auto_timer = None
        
        self._run_proto = None
        self._run_timeout = None
        self._proto_register_event.clear()
        
        self._proto_register_lock.release()
            
    def run_monitor(self):
        while True:
            self._proto_register_event.wait()
            print("_proto_register_event get")
            self._proto_register_event.clear()

            if (self._run_proto is None):
                raise PlatformException("register proto but None")                
            
            sdk_handler.SECURITY_MONITOR.register_and_start( 
                obj=self._run_proto, 
                check_distance=300)

            sdk_handler.SECURITY_MONITOR.wait_for_trigger()

            # 如果触发者是其他人
            if not sdk_handler.SECURITY_MONITOR.is_accessable(self._run_proto):
                continue
                # raise PlatformException("SECURITY_MONITOR not accessable for proto {}".format(self._run_proto))

            # 确实是被当前proto触发
            set_reason = sdk_handler.SECURITY_MONITOR.get_set_reason()
            print("[drive_adjuster] set_reason =",set_reason)

            if (set_reason == "ADJUST"):
                sdk_handler.PHY_SENDER.send_adjust_status(is_on=True)
                self.drive_adjust()
                print("drive proto send again")
                self._recover_proto()
            elif (set_reason == "END"):
                self.proto_clear()

            print("---drive end _once_turn")
    
    def _recover_proto(self):
        # ERROR 这里逻辑有问题 只能adjust一次
        self._proto_register_lock.acquire()

        print("recover :x_spd:{0:f}, y_spd:{1:f}, z_spd:{2:f}".format(self._run_proto._x_spd, self._run_proto._y_spd, self._run_proto._z_spd))

        sdk_handler.PHY_SENDER.send_action_info(self._encode_drive_proto(self._run_proto))
        self._chassis._send_sync_proto(self._run_proto)
        self._proto_register_event.set()

        self._proto_register_lock.release()

    def drive_adjust(self):
        sdk_handler.EP_ROBOT.chassis._dij_drive_speed(0, 0, 0)
        print("stop_here")
        sdk_handler.SECURITY_MONITOR.security_monitor_adjust("drive_speed",self)

