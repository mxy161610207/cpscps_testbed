from robomaster import robot
from patch import all
import time
import math,random

# platform
from .platform_exception import PlatformException
from .platform_timer import PlatformTimerManager
from .physical_info_handler import PhysicalInfoHandler
from .simulate_info_handler import SimulateInfoHandler
from .security_monitor import SecurityMonitor
from .drive_adjuster import DriveSpeedAdjuster

class RoboMasterEPWrapper:
    def __init__(self,adjust_state,
        location_server_addr, phy_sender_addr, grd_syncer,sdk_syncer,
        simluate_engine_addr, sim_sender_addr, sim_syncer,sim_distance):
        print("__init__ RoboMasterEPWrapper start")
        self._status = 1
        self._rot_flip=-1
        self._sdk_syncer = sdk_syncer

        self._adjust_state = adjust_state
        self._adjust_state.value = 0
        
        # connect and handle
        self._has_active_car=False
        self._robomaster_ep=None

        self._phy_msg_sender = PhysicalInfoHandler(grd_syncer, phy_sender_addr, 
                                                   location_server_addr,self,sdk_syncer)
        self._sim_msg_sender = SimulateInfoHandler(sim_syncer, sim_sender_addr, 
                                                   simluate_engine_addr,self,sim_distance)

        self._timer_manager = PlatformTimerManager(self)
        self._security_monitor = SecurityMonitor(self)
        self._drive_speed_adjuster = DriveSpeedAdjuster(self)

        print("__init__ RoboMasterEPWrapper end")
    
    @property
    def has_active_car(self):
        return self._has_active_car

    def close(self):
        if (self.has_active_car):
            self._robomaster_ep.chassis.unsub_position()
            self._robomaster_ep.close()

    def update_position(self,data):
        x,y,z = data
        self._sdk_syncer['x'] = int(x*1000) + 2700//2
        self._sdk_syncer['y'] = int(-y*1000) + 2700//2

        # mxy noisy here
        self._sdk_syncer['x'] +=(random.random()-0.5)*4 # 8
        self._sdk_syncer['y'] +=(random.random()-0.5)*4 # 8

    def update_angle(self,angle):
        self._sdk_syncer['deg'] = angle
        self._sdk_syncer['deg']+=(random.random()-0.5)*6 # 10
        self._sdk_syncer['rad'] = math.radians(angle)

    def get_initialized_robot(self):
        if (self.has_active_car):
            return self._robomaster_ep
        
        try:
            self._robomaster_ep=robot.Robot()
            self._robomaster_ep._platform_hander=self
            self._robomaster_ep.initialize(conn_type="sta")
            self._robomaster_ep.set_robot_mode(mode=robot.CHASSIS_LEAD)
            self._robomaster_ep.chassis.sub_position(cs=1,freq=20,callback = self.update_position)
        except:
            raise PlatformException("[platform] connect error!")
        
        self._has_active_car=True
        return self._robomaster_ep

    def flush_undefined_behavior(self):
        # drive_speed(0,0,0) 会有UB，
        # 使用_dij_move(0,0,0).wait_for_completed刷新一下
        # 注意必须在底盘没有Action时，调用该函数。
        # 判断方法：报错 Robot is already performing action(s)
        # self._robomaster_ep.chassis._dij_move(0,0,0).wait_for_completed()
        pass

    def global_stop(self):
        self._robomaster_ep.chassis._dij_drive_speed(0,0,0)
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

    def query_phy_position(self):
        # {'x':x,'y':y,'deg':deg,'rad':rad}
        if (not self._phy_msg_sender.is_online):
            raise PlatformException("[platform] query illegal _phy_msg_sender")
        
        return self._phy_msg_sender.query_position()
    
    def query_sim_position(self):
        # {'x':x,'y':y,'deg':deg,'rad':rad}

        # if (not self._phy_msg_sender.is_online):
        #     raise PlatformException("[platform] query illegal _phy_msg_sender")
        
        return self._sim_msg_sender.query_position()

    def reset_simulate_syncer(self,pos_info):
        self._phy_msg_sender.simulate_syncer_update(pos_info)
        pass

    def send_adjust_status(self,is_on=False):
        if (not self._phy_msg_sender.is_online):
            raise PlatformException("[platform] query illegal _phy_msg_sender")
        
        self._phy_msg_sender.send_adjust_status(is_on)

    def adjust(self,is_manual=False):
        if (not self._has_active_car): return
        self._timer_manager.adjust_status_start()

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
                max_id = 0
                for i in range(4):
                    if dis[i]<dis[min_id]: min_id=i
                    if dis[i]>dis[max_id]: max_id=i

                away_dis = 600
                if (dis[min_id]>away_dis): break

                # 尝试放松最小距离 30cm
                match_distance = away_dis - dis[min_id]
                match_distance = max(300,match_distance)

                # 这个距离如果对侧不能移动，放弃
                rev_id = (2+min_id)%4
                can_mov_max = dis[rev_id]

                if (can_mov_max-300 > match_distance):
                    # 移动
                    print(">>> adjust-1 {} {} {}".format(
                        dis_dir[min_id],
                        dis[min_id],
                        match_action[min_id]))
                    
                    self.do_action(match_action[min_id],
                        move_dis=max(0.1,match_distance*0.001))
                else: # 从最大距离移动一段
                    match_distance = min(300,dis[max_id]-300)

                    rev_id = (2+max_id)%4
                    can_mov_max = dis[rev_id]

                    print(">>> adjust-2 {} {} {}".format(
                        dis_dir[max_id],
                        dis[max_id],
                        match_action[rev_id]))
                    self.do_action(match_action[rev_id],
                        move_dis=max(0.1,match_distance*0.001))


            # step2 
            self.do_action('B',self._robomaster_ep)
            time.sleep(1)

        # stop adjust status

        self._timer_manager.adjust_status_end()

    def do_action(self,action, move_dis=0.5,rot_deg=45,mute=False):

        ep_chassis=self._robomaster_ep.chassis
        
        xy_speed=0.6
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
        
        # print("[sdk_handler] dji action success")

    def convert(self, action):
        large_move_dis = 0.8
        small_move_dis = 0.2
        large_rot_deg = 90
        small_rot_deg = 10
        if (action == 'W'):
            return large_move_dis,0,0
        elif (action == 'S'):
            return -large_move_dis,0,0
        elif (action == 'A'):
            return 0,-large_move_dis,0
        elif (action == 'D'):
            return 0,large_move_dis,0
        elif (action == 'w'):
            return small_move_dis,0,0
        elif (action == 's'):
            return -small_move_dis,0,0
        elif (action == 'a'):
            return 0,-small_move_dis,0
        elif (action == 'd'):
            return 0,small_move_dis,0
        elif (action == 'L'):
            return 0,0,large_rot_deg
        elif (action == 'R'):
            return 0,0,-large_rot_deg
        elif (action == 'l'):
            return 0,0,small_rot_deg
        elif (action == 'r'):
            return 0,0,-small_rot_deg
        elif (action == 'w'):
            return small_move_dis,0,0
        elif (action == 'B'):
            self._rot_flip=-self._rot_flip
            return 0,0,180*-self._rot_flip
            # pos = self._phy_msg_sender.query_position()
            # print("init = ({:.3f},{:.3f}) deg = {:.3f}".
            #     format(pos['x'], pos['y'], pos['deg']))
        else:
            pass
        

    def do_move_api(self,args):
        ep_chassis=self._robomaster_ep.chassis

        print(args)
        if 'x' in args:
            x,y,z = args['x'],args['y'],args['z']
        else:
            try:
                x,y,z = self.convert(args)
            except Exception:
                return
        print(x,y,z,"converted")
        xy_speed=0.6
        z_speed=60

        ep_chassis.move(x,y,z,xy_speed,z_speed).wait_for_completed()
        
        print("[sdk_handler] usr action success")

    def do_drive_api(self,args,timeout=2):
        ep_chassis=self._robomaster_ep.chassis

        x,y,z = args['x'],args['y'],args['z']
        ep_chassis.drive_speed(x,y,z,)

        print("[sdk_handler] usr drive success")
