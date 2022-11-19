# modify some robomaster api
import time
import json
from robomaster import robot

from .robo_wrapper import RoboMasterEPWrapper
from .platform_exception import PlatformException

def create_car_handler(location_server_addr,physical_sender_addr):
    # 获取车的handler，设置监视资源
    car_handler = RoboMasterEPWrapper(location_server_addr,physical_sender_addr)

    global CAR_HANDLER, PHY_INFO, PHY_SENDER

    CAR_HANDLER = car_handler
    PHY_INFO = car_handler._phy_msg_sender.info
    PHY_SENDER = car_handler._phy_msg_sender

    global SECURITY_MONITOR, TIME_MANAGER, DRIVE_SPEED_ADJUSTER
    SECURITY_MONITOR = car_handler._security_monitor
    TIME_MANAGER = car_handler._timer_manager
    DRIVE_SPEED_ADJUSTER = car_handler._drive_speed_adjuster

    # 和真实小车建立连接
    global EP_ROBOT
    EP_ROBOT = car_handler.get_initialized_robot()

    EP_ROBOT.set_robot_mode(mode=robot.CHASSIS_LEAD)
    EP_ROBOT.led.set_led(comp="all", r=200, g=200, b=200)

    # 确保各种xxx_sub 正常运行
    while(1):
        F, R, B, L = PHY_INFO.get_sensor_data_info()[:]
        # print("sensor_init =",F,B,L,R)
        if (F or B or L or R):
            break

    print("=====> get sdk car_handler success")

    return


def raiser(
    proc_name, 
    platform_status_resources,
    platform_message_resources,
    platform_socket_address):

    print("Proc [{}] start".format(proc_name))

    sdk_platform_status = platform_status_resources['sdk']
    sdk_platform_message = platform_message_resources['sdk']

    display_platform_message = platform_message_resources['display']

    physical_sender_addr = platform_socket_address['phy_sender']
    # simluate_sender_addr = platform_socket_address['sdk']
    location_server_addr = platform_socket_address['location']

    if sdk_platform_status.value == 0:
        time.sleep(4)
        # create_car_handler(location_server_addr,physical_sender_addr)
        sdk_platform_status.value = 1

    while True:
        # if (sdk_platform_status.value==3):
        #     continue

        # action_json_str = sdk_platform_message.get()
        # action_json = json.loads(action_json_str)
        action_json = sdk_platform_message.get()

        action_type, action_info = action_json['type'], action_json['info']

        if action_type == 'SYSTEM_STATUS':
            if (action_info['status'] == 'init_success'):
                sdk_platform_status.value = 2

                global PHY_SENDER
                PHY_SENDER.location_server_reset()
                pos = PHY_SENDER.query_position()
                print("init = ({:.3f},{:.3f}) deg = {:.3f}".
                      format(pos['x'], pos['y'], pos['deg']))
                pass

            elif (action_info['status'] == 'shutdown'):
                break

        elif action_type == 'ACTION':
            if action_info['api_version'] == 'DJI':
                if (sdk_platform_status.value != 1):
                    raise PlatformException(
                        "sdk_platform_status = {}, but run DJI sdk".format(
                            sdk_platform_status.value))

                action = action_info['api_info']
                global CAR_HANDLER
                # CAR_HANDLER.do_action(action)
                time.sleep(3)
                print("success now\n"*10)
                display_platform_message.put("success")

            elif action_info['api_version'] == 'USER':
                if (sdk_platform_status.value != 2):
                    raise PlatformException(
                        "sdk_platform_status = {}, but run USER sdk".format(
                            sdk_platform_status.value))

                # TODO
                pass

        elif action_type == 'SENSOR':
            if action_info['sensor_module'] == 'ir_sensor':
                # TODO
                pass
        
        
    print("Proc [{}] end".format(proc_name))






#     # 手动调一下车的位置
#     # do_action是一系列简单的封装, 包含一个print W
#     # xy_speed=0.5 move_dis=0.2
#     # z_speed=60 rot_dis=45
#     time.sleep(0.5)
#     print("=====> recover car")
#     # ss="LLrF"
#     # for ch in ss:
#     #     car_handler.do_action(ch,ep_chassis)

#     time.sleep(0.5)

#     # 获取车的初始位置[本次定位一定在4象限，且deg in [0,90)
#     PHY_SENDER.location_server_reset()

#     pos = PHY_SENDER.query_position()
#     print("init = ({:.3f},{:.3f}) deg = {:.3f}".
#           format(pos['x'], pos['y'], pos['deg']))

#     # 平台初始化完成
#     print("=====> end physical_platform_initialize")
#     print("start run")

#     user_program_part(EP_ROBOT)

#     print("Proc [{}] end".format(proc_name))


# def user_program_part(ep_robot):
#     ep_chassis = ep_robot.chassis
#     ep_chassis.move(4, 0, 0, 0, 0).wait_for_completed()
