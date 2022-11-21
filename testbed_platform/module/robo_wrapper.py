from robomaster import robot
from patch import all
import time

# platform
from .platform_exception import PlatformException
from .platform_timer import PlatformTimerManager
from .physical_info_handler import PhysicalInfoHandler
from .security_monitor import SecurityMonitor
from .drive_adjuster import DriveSpeedAdjuster

class RoboMasterEPWrapper:
    def __init__(self,server_addr,phy_sender_addr,sim_sender_addr=None):
        print("__init__ RoboMasterEPWrapper start")
        self._status = 1
        self._rot_flip=-1
        
        # connect and handle
        self._has_active_car=False
        self._robomaster_ep=None

        self._phy_msg_sender = PhysicalInfoHandler(phy_sender_addr,server_addr,self)
        self._sim_msg_recver = None

        self._timer_manager = PlatformTimerManager(self)
        self._security_monitor = SecurityMonitor(self)
        self._drive_speed_adjuster = DriveSpeedAdjuster(self)

        print("__init__ RoboMasterEPWrapper end")
    
    @property
    def has_active_car(self):
        return self._has_active_car

    def close(self):
        if (self.has_active_car):
            self._robomaster_ep.close()

    def get_initialized_robot(self):
        if (self.has_active_car):
            return self._robomaster_ep
        
        try:
            self._robomaster_ep=robot.Robot()
            self._robomaster_ep._platform_hander=self
            self._robomaster_ep.initialize(conn_type="sta")
            self._robomaster_ep.set_robot_mode(mode=robot.CHASSIS_LEAD)
        except:
            raise PlatformException("[platform] connect error!")
        
        self._has_active_car=True
        return self._robomaster_ep

    def flush_undefined_behavior(self):
        # drive_speed(0,0,0) 会有UB，
        # 使用_dij_move(0,0,0).wait_for_completed刷新一下
        # 注意必须在底盘没有Action时，调用该函数。
        # 判断方法：报错 Robot is already performing action(s)
        # EP_ROBOT.chassis._dij_move(0,0,0).wait_for_completed()
        pass

    def led_behavior(self,state):
        if (state=='adjust'):
            r,g,b=200,200,0
        elif (state=='normal'):
            r,g,b=0,200,0
        else:
            r,g,b=200,200,200

        if (not self.has_active_car): return
        self._robomaster_ep.led.set_led(comp="all", r=r, g=g, b=b)    
        self.flush_undefined_behavior()

    # # 询问虚拟小车位置
    # def query_sim_position(self):
    #     # [x,y,deg]
    #     if (not self._sim_msg_recver.is_online):
    #         raise PlatformException("[platform] query illegal sim_msg_recver")
        
    #     #TODO
    #     self._sim_msg_recver.query_position()

    def query_phy_position(self):
        # [x,y,deg]
        if (not self._phy_msg_sender.is_online):
            raise PlatformException("[platform] query illegal _phy_msg_sender")
        
        return self._phy_msg_sender.query_position()

    def send_adjust_status(self,is_on=False):
        if (not self._phy_msg_sender.is_online):
            raise PlatformException("[platform] query illegal _phy_msg_sender")
        
        self._phy_msg_sender.send_adjust_status(is_on)

    def adjust(self,is_manual=False):
        if (not self._has_active_car): return
        if self._timer_manager.adjust_status_start():
            return 

        if is_manual:
            while True:
                ss = input("adjust_action>")
                if (ss=='Q' or ss=='q'):
                    break
                for ch in ss:
                    self.do_action(ch)
        else:
            # step1  
            time.sleep(0.5)
            match_action = "SAWD"
            dis_dir = "FRBL"
            while(1):
                dis = self._phy_msg_sender.info.get_sensor_data_info()[:]
                min_id = 0
                for i in range(4):
                    if dis[i]<dis[min_id]: min_id=i

                if (dis[min_id]>400): break
                match_distance = 400 - dis[min_id]
                match_distance = max(100,match_distance)

                print(">>> adjust {} {} {}".format(dis_dir[min_id],
                dis[min_id],match_action[min_id]))
                self.do_action(match_action[min_id],
                    move_dis=max(0.1,match_distance*0.001))

            # step2 
            self.do_action('B',self._robomaster_ep)

        # stop adjust status

        self._timer_manager.adjust_status_end()

    def do_action(self,action, move_dis=0.5,rot_deg=45,mute=False):

        ep_chassis=self._robomaster_ep.chassis
        
        xy_speed=0.3
        z_speed=60
        if (action == 'W'):
            ep_chassis._dij_move(move_dis,0,0,xy_speed,z_speed).wait_for_completed()
        elif (action == 'S'):
            ep_chassis._dij_move(-move_dis,0,0,xy_speed,z_speed).wait_for_completed()
        elif (action == 'A'):
            ep_chassis._dij_move(0,-move_dis,0,xy_speed,z_speed).wait_for_completed()
        elif (action == 'D'):
            ep_chassis._dij_move(0,move_dis,0,xy_speed,z_speed).wait_for_completed()
        elif (action == 'L'):
            ep_chassis._dij_move(0,0,rot_deg,xy_speed,z_speed).wait_for_completed()
        elif (action == 'R'):
            ep_chassis._dij_move(0,0,-rot_deg,xy_speed,z_speed).wait_for_completed()
        elif (action == 'l'):
            ep_chassis._dij_move(0,0,10,xy_speed,z_speed).wait_for_completed()
        elif (action == 'r'):
            ep_chassis._dij_move(0,0,-10,xy_speed,z_speed).wait_for_completed()
        elif (action == 'w'):
            ep_chassis._dij_move(0.1,0,0,xy_speed,z_speed).wait_for_completed()
        elif (action == 'B'):
            ep_chassis._dij_move(0,0,180*self._rot_flip,xy_speed,z_speed).wait_for_completed()
            self._rot_flip=-self._rot_flip
        elif (action == 'F'):
            self._phy_msg_sender.location_server_reset()
            # pos = self._phy_msg_sender.query_position()
            # print("init = ({:.3f},{:.3f}) deg = {:.3f}".
            #     format(pos['x'], pos['y'], pos['deg']))
        else:
            pass
        
        print("[sdk_handler] dji action success")

    def do_usr_action(self,action,move_dis=2,rot_deg=45,mute=False):
        ep_chassis=self._robomaster_ep.chassis
        
        xy_speed=0.6
        z_speed=60
        if (action == 'W'):
            ep_chassis.move(move_dis,0,0,xy_speed,z_speed).wait_for_completed()
        elif (action == 'S'):
            ep_chassis.move(-move_dis,0,0,xy_speed,z_speed).wait_for_completed()
        elif (action == 'A'):
            ep_chassis.move(0,-move_dis,0,xy_speed,z_speed).wait_for_completed()
        elif (action == 'D'):
            ep_chassis.move(0,move_dis,0,xy_speed,z_speed).wait_for_completed()
        elif (action == 'L'):
            ep_chassis.move(0,0,rot_deg,xy_speed,z_speed).wait_for_completed()
        elif (action == 'R'):
            ep_chassis.move(0,0,-rot_deg,xy_speed,z_speed).wait_for_completed()
        elif (action == 'l'):
            ep_chassis.move(0,0,10,xy_speed,z_speed).wait_for_completed()
        elif (action == 'r'):
            ep_chassis.move(0,0,-10,xy_speed,z_speed).wait_for_completed()
        elif (action == 'w'):
            ep_chassis.move(0.1,0,0,xy_speed,z_speed).wait_for_completed()
        elif (action == 'B'):
            ep_chassis.move(0,0,180*self._rot_flip,xy_speed,z_speed).wait_for_completed()
            self._rot_flip=-self._rot_flip
        else:
            pass
        
        print("[sdk_handler] usr action success")
