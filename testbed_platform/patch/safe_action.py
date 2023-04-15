from robomaster.chassis import *

import threading,math

from robomaster import logger
from robomaster import action

from module import sdk_handler
from module.platform_exception import PlatformException
from location.location_list import ActionMonitor

'''
class SafeChassisMoveAction(ChassisMoveAction)

新加的类: SafeChassisMoveAction
用于将一个Action分阶段完成，且在阶段间插入调整动作
'''
class SafeChassisMoveAction(action.Action):
    _action_proto_cls = 1 # just not None
    _push_proto_cls = 1 # just not None

    _actual_action = None
    _chassis = None

    # _pause_event = None

    # _monitor_thread = None
    # _monitor_enable = False
    _checker_args = None
    _checker_lock = threading.Lock()
    _on_state_changed = None

    def __init__(self, chassis:Chassis , x=0, y=0, z=0, spd_xy=0, spd_z=0, **kw):
        # self._action_id = -1
        self.timer = None
        self._percent = 0

        # self._adjust_lock = threading.Lock()
        # self._adjust_time = 0

        self._x = x
        self._y = y
        self._z = z
        self._zero_element = []
        for _ in (x,y,z):
            self._zero_element.append(0 if _==0 else 1)


        self._cur_x = 0
        self._cur_y = 0
        self._cur_z = 0

        self._spd_xy = spd_xy
        self._spd_z = spd_z
        self._chassis = chassis

        self._state = action.ACTION_IDLE

        self.run_thread = threading.Thread(target=self.run_action)
        self.run_thread.start()
        
        self._event = threading.Event()
        self._left_actual_exec_time = None

    def __repr__(self):
        return "action_id:{0}, state:{1}, percent:{2}, x:{3}, y:{4}, z:{5}, xy_speed:{6}, z_speed:{7}".format(
            self._actual_action._action_id, self._state, self._percent, self._x, self._y, self._z, self._spd_xy, self._spd_z)

    def _generate_action(self):
        left = self._left()[:]
        return ChassisMoveAction(left[0],left[1],left[2],self._spd_xy,self._spd_z)

    def _goal(self):
        return [self._x,self._y,self._z]

    def _current(self):
        return [self._cur_x,self._cur_y,self._cur_z]
    
    def _left(self):
        left_x = (self._x - self._cur_x)*self._zero_element[0]
        left_y = (self._y - self._cur_y)*self._zero_element[1]
        left_z = (self._z - self._cur_z)*self._zero_element[2]

        return [left_x,left_y,left_z]

    def _update_current(self,old_pos,new_pos):
        # print("old_pos = {:.3f} {:.3f} deg = {:.3f}".format(old_pos[0],old_pos[1],old_pos[2]))
        # print("new_pos = {:.3f} {:.3f} deg = {:.3f}".format(new_pos[0],new_pos[1],new_pos[2]))

        det_x = new_pos['x']-old_pos['x']
        det_y = new_pos['y']-old_pos['y']
        det_deg = new_pos['deg']-old_pos['deg']

        rad = math.radians(old_pos['deg'])
        dx,dy = ActionMonitor._after_rot_matrix(-rad,det_x,det_y)

        # motion = (dx*0.001,dy*0.001,det_deg)

        self._cur_x += dx*0.001
        self._cur_y += -dy*0.001
        self._cur_z += det_deg
        print("+++",self.percent_str)
        return 

    def wait_for_completed(self, timeout=None):
        """ 等待任务动作直到完成

        :param timeout: 超时，在timeout前未完成任务动作，直接返回
        :return: bool: 动作在指定时间内完成，返回True; 动作超时返回False
        """
        if self._event.isSet() and self.is_completed:
            return True

        if timeout:
            self.timer = threading.Timer(timeout,
                self._changeto_state, args=(action.ACTION_EXCEPTION,))
            self.timer.start()

            self._event.wait()
            # 由于adjust模块的存在，timeout计时不准确
   
            if (self.state==action.ACTION_EXCEPTION):
                print("+++ Action: wait_for_completed timeout.")
                logger.warning("Action: wait_for_completed timeout.")
                return False
        else:
            self._event.wait()
            if not self._event.isSet():
                logger.warning("Action: wait_for_completed timeout.")
                self._changeto_state(action.ACTION_EXCEPTION)
                return False
        return True

    @property
    def percent_str(self):
        s = "+++ cur_percent: x=({:.3f}/{:.3f}),y=({:.3f}/{:.3f}),deg=({:.3f}/{:.3f})".format(
            self._cur_x,self._x,
            self._cur_y,self._y,
            self._cur_z,self._z)
        return s

    def _start_security_monitor(self):
        print("+++ security_monitor init")
        sdk_handler.SECURITY_MONITOR.register_and_start(
            obj=self, check_distance=200
        )

    def _start_action_completed_monitor(self):
        monitor_thread = threading.Thread(target=self.action_compelted_monitor)
        monitor_thread.start()
        # print("action_completed_monitor start")

    def action_compelted_monitor(self):
        print("+++ action_completed_monitor wait")
        timeout = None

        if (self.timer): 
            timeout = self.timer.get_left()
            print("+++ left execute time ={:.3f}s **".format(timeout))

        # 动作有两种执行结束的条件
        # 1) 超时 timer存在，
        #    且下一个动作片段在timer内无法结束
        # 2) 无计时器，运行结束。
        #    运行期间，如果被trigger，本次执行会被设为
        #    COMPLETED，并且因为isSet()，没有设置END的资格
        exec_result = self._actual_action.wait_for_completed(timeout)

        print("+++ action completed")

        if (not sdk_handler.SECURITY_MONITOR.isSet()):
            sdk_handler.SECURITY_MONITOR.event_set_by('END')

        if (not exec_result):
            sdk_handler.flush_undefined_behavior()

    def run_action(self):
        while(True):
            self._cur_position_security_check()
            self._once_turn()
            if (self.is_completed): break
        
        print("total action {:.3f} {:.3f} {:.3f}".format(
            self._cur_x,self._cur_y,self._cur_z
        ))

    def _cur_position_security_check(self):
        dis = sdk_handler.PHY_INFO.get_sensor_data_info()[:]
        min_id = 0
        for i in range(4):
            if dis[i]<dis[min_id]: min_id=i

        if (dis[min_id]>210): return 
        
        # to adjust at beginning
        sdk_handler.PHY_SENDER.send_adjust_status(is_on=True)
        print("start at an danger place")
        self.move_adjust(is_manual=False)
    
    def _once_turn(self):
        print("--- start _once_turn")
        self._actual_action = self._generate_action()
        print("> start ",self._actual_action._encode_json)

        old_pos = sdk_handler.PHY_SENDER.query_position()
        print("old_pos = {:.3f} {:.3f} deg = {:.3f}".format(old_pos['x'],old_pos['y'],old_pos['deg']))

        # send action
        self._start_security_monitor()
        self._start_action_completed_monitor()

        # SafeAction的第一个动作片段需要
        if (self._state == action.ACTION_IDLE):
            self._changeto_state(action.ACTION_RUNNING)

        while (sdk_handler.CAR_HANDLER._adjust_state.value == 1):
            pass
        
        self._chassis._action_dispatcher.send_action(self._actual_action)
        # print("send actual action")

        # one of monitor will set
        sdk_handler.SECURITY_MONITOR.wait_for_trigger()
        if not sdk_handler.SECURITY_MONITOR.is_accessable(self):
            pass
            # raise PlatformException("SECURITY_MONITOR not accessable for SafeAction{}".format(self._encode_json))

        # 获取从start pos 到当前位置的移动距离

        new_pos = sdk_handler.SECURITY_MONITOR.get_set_position()

        self._update_current(old_pos,new_pos)

        # 下一次动作迭代        
        set_reason = sdk_handler.SECURITY_MONITOR.get_set_reason()
        print("[safe_action] set_reason =",set_reason)

        if (set_reason == "ADJUST"):
            # set by _auto_distance_security_check()
            # _actual_action stop but not set completed,
            # action_compelted_monitor() still wait! 
            sdk_handler.PHY_SENDER.send_adjust_status(is_on=True)
            self._actual_action._changeto_state(action.ACTION_SUCCEEDED)
            
            print("+++ set actual_action completed")
            self.move_adjust()

        elif (set_reason == "END"):
            # set by action_compelted_monitor()
            # _auto_distance_security_check() has been stop by set()
            print("+++ set total action completed")
            self._changeto_state(action.ACTION_SUCCEEDED)
        else:
            raise PlatformException("Unexpected set_reason in SafeAction")

        print("--- end _once_turn")
        return    

    def move_adjust(self,is_manual=False):
        sdk_handler.SECURITY_MONITOR.security_monitor_adjust(api='move',obj=self,is_manual=is_manual)

