# modify some robomaster api
import imp
import module.robo_wrapper
import patch
import time
from robomaster import robot

def raise_platform(proc_name):
    print("Proc [{}] start".format(proc_name))
    
    # 获取车的handler，设置监视资源
    car_handler=module.robo_wrapper.RoboMasterEPWrapper()
    global CAR_HANDLER,PHY_INFO,PHY_SENDER

    CAR_HANDLER=car_handler
    PHY_INFO=car_handler._phy_msg_sender.info
    PHY_SENDER=car_handler._phy_msg_sender
    
    global SECURITY_MONITOR,TIME_MANAGER,DRIVE_SPEED_ADJUSTER
    SECURITY_MONITOR=car_handler._security_monitor
    TIME_MANAGER=car_handler._timer_manager
    DRIVE_SPEED_ADJUSTER = car_handler._drive_speed_adjuster

    # 和真实小车建立连接
    ep_robot=car_handler.get_initialized_robot()
    global EP_ROBOT
    # SIMULATE_MSG=car_handler._sim_msg_recver
    EP_ROBOT=car_handler._robomaster_ep


    ep_robot.set_robot_mode(mode=robot.CHASSIS_LEAD)
    ep_robot.led.set_led(comp="all", r=200, g=200, b=200)
    print("=====> start physical_platform_initialize")
    ep_chassis = ep_robot.chassis

    # 确保各种xxx_sub 正常运行
    while(1):
        F,R,B,L = PHY_INFO.get_sensor_data_info()[:]
        # print("sensor_init =",F,B,L,R)
        if (F or B or L or R):break

    # 手动调一下车的位置 
    # do_action是一系列简单的封装, 包含一个print W
    # xy_speed=0.5 move_dis=0.2
    # z_speed=60 rot_dis=45
    time.sleep(0.5)
    print("=====> recover car")
    ss="LLrF"
    for ch in ss:
        car_handler.do_action(ch,ep_chassis)
    
    time.sleep(0.5)
    
    # 获取车的初始位置[本次定位一定在4象限，且deg in [0,90)
    PHY_SENDER.location_server_reset()

    pos = PHY_SENDER.query_position()
    print("init = ({:.3f},{:.3f}) deg = {:.3f}".
        format(pos['x'],pos['y'],pos['deg']))

    # 平台初始化完成
    print("=====> end physical_platform_initialize")
    print("start run")

    user_program_part(EP_ROBOT)


    print("Proc [{}] end".format(proc_name))


def user_program_part(ep_robot):
    ep_chassis=ep_robot.chassis
    ep_chassis.move(4,0,0,0,0).wait_for_completed()
