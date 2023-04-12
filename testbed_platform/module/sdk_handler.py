# modify some robomaster api
import time
import json,random
from robomaster import robot

from .robo_wrapper import RoboMasterEPWrapper
from .platform_exception import PlatformException

def create_car_handler(
        location_server_addr,physical_sender_addr,grd_syncer,
        simulate_engine_addr,simulate_sender_addr,sim_syncer):
    # 获取车的handler，设置监视资源
    car_handler = RoboMasterEPWrapper(
        location_server_addr,physical_sender_addr,grd_syncer,
        simulate_engine_addr,simulate_sender_addr,sim_syncer)

    global CAR_HANDLER, PHY_INFO, PHY_SENDER, SIM_SENDER

    CAR_HANDLER = car_handler
    PHY_INFO = car_handler._phy_msg_sender.info
    PHY_SENDER = car_handler._phy_msg_sender
    SIM_SENDER = car_handler._sim_msg_sender

    global SECURITY_MONITOR, TIME_MANAGER, DRIVE_SPEED_ADJUSTER
    SECURITY_MONITOR = car_handler._security_monitor
    TIME_MANAGER = car_handler._timer_manager
    DRIVE_SPEED_ADJUSTER = car_handler._drive_speed_adjuster

    # 和真实小车建立连接
    global EP_ROBOT
    
    EP_ROBOT = car_handler.get_initialized_robot()
    # EP_ROBOT.set_robot_mode(mode=robot.CHASSIS_LEAD)
    EP_ROBOT.led.set_led(comp="all", r=200, g=200, b=200)

    # 确保各种xxx_sub 正常运行
    while(1):
        F, R, B, L = PHY_INFO.get_sensor_data_info()[:]
        # print("sensor_init =",F,B,L,R)
        if (F or B or L or R):
            break

    print("=====> get sdk car_handler success")

    return


def closer(
    platform_status_resources,
    platform_message_resources,
    platform_socket_address):

    close_json={
        'type':'SYSTEM_STATUS',
        'info':{
            'status':'shutdown',
        }
    }
    
    sdk_platform_message = platform_message_resources['sdk']
    sdk_platform_message.put(json.dumps(close_json))
    return

def raiser(
    proc_name, 
    platform_status_resources,
    platform_message_resources,
    platform_socket_address):

    print("Proc [{}] start".format(proc_name))
    
    global_status = platform_status_resources['global']
    

    sdk_platform_status = platform_status_resources['sdk']
    sdk_platform_message = platform_message_resources['sdk']

    controller_message = platform_message_resources['control']

    physical_sender_addr = platform_socket_address['phy_sender']
    simulate_sender_addr = platform_socket_address['sim_sender']

    location_server_addr = platform_socket_address['location']
    simulate_engine_addr = platform_socket_address['sim_engine']
    
    grd_syncer = platform_message_resources['grd_position']
    sim_syncer = platform_message_resources['sim_position']

    real_car = True

    if sdk_platform_status.value == 0:
        if real_car:
            create_car_handler(
                location_server_addr,physical_sender_addr,grd_syncer,
                simulate_engine_addr,simulate_sender_addr,sim_syncer)
        else:
            # time.sleep(2)
            pass
        
        sdk_platform_status.value = 1

    do_action = True
    
    global CAR_HANDLER
    global PHY_SENDER,SIM_SENDER

    while True:
        action_json_str = sdk_platform_message.get()
        action_json = json.loads(action_json_str)

        if (global_status.value == -1):
            break
        
        # print("get {}".format(action_json_str))

        action_type, action_info = action_json['type'], action_json['info']
        reply_json={
            'status':'success',
            'type':action_type
        }

        if action_type == 'SYSTEM_STATUS':
            if (action_info['status'] == 'init_success'):
                sdk_platform_status.value = 2

                if real_car:
                    PHY_SENDER.location_server_reset()
                    pos = CAR_HANDLER.query_phy_position()
                    print("init = ({:.3f},{:.3f}) deg = {:.3f}".
                        format(pos['x'], pos['y'], pos['deg']))
                else:
                    time.sleep(2)
                    pass
                
                info = {
                    'msg':"init_success"
                }
                
                reply_json['info']=info
                controller_message.put(json.dumps(reply_json))
                
                pass

            elif (action_info['status'] == 'shutdown'):
                global_status.value == -1
                break

        elif action_type == 'SENSOR':
            sensor_type =  action_info['sensor_type']  
            sensor_info = "ERROR"          
            if (sensor_type == 'distance'):
                if real_car:
                    # info = SIM_SENDER.update_distance_data_info()
                    # sensor_info = PHY_INFO.get_sensor_data_info()
                    f_dir = open("D:\\GitHub\\cpscps_testbed\\unity_dir.txt","r")
                    sensor_info = f_dir.read()
                    f_dir.close()

                else:
                    sensor_info = "distance{}".format(random.randint(0,9999))

            elif sensor_type == 'angle':
                if real_car:
                    # info = SIM_SENDER.update_angle_data_info()
                    sensor_info = PHY_INFO.get_yaw_ground_angle()
                else:
                    sensor_info = "angle{}".format(random.randint(0,9999))

            
            info ={
                'sensor_type':sensor_type,
                'sensor_info':str(sensor_info)
            }
            reply_json['info']=info
            controller_message.put(json.dumps(reply_json))
        
        elif action_type == 'DRIVE':
            action_reply_message = "error"
            if (sdk_platform_status.value == 2):
                pass
            elif (sdk_platform_status.value == 3):
                print("sdk_platform_status = {}, ACTION is running, unable to run driven".format(
                            sdk_platform_status.value))
                raise PlatformException("")

            action = action_info['api_info']
            if real_car:
                CAR_HANDLER.do_drive_api(action,timeout=2)
                # print("get {}".format(action_json_str))
                # CAR_HANDLER.do_action(action)
            else:
                time.sleep(2)
                pass

            info = {
                'msg':"drive_action_success"
            }
                
            reply_json['info']=info
            controller_message.put(json.dumps(reply_json))

        elif action_type == 'MOVE':
            action_reply_message = "error"
            
            # 初始化阶段，动作全部直接执行
            if action_info['api_version'] == 'DJI':
                if (sdk_platform_status.value != 1):
                    print("sdk_platform_status = {}, but run USER sdk".format(
                            sdk_platform_status.value))
                    raise PlatformException("")

                action = action_info['api_info']

                # 执行动作
                if real_car:
                    # print("get {}".format(action_json_str))
                    CAR_HANDLER.do_action(action)
                else:
                    time.sleep(2)
                    pass
                
                action_reply_message = "dji_action_success"

            # 程序解析阶段
            elif action_info['api_version'] == 'USER':
                if (sdk_platform_status.value != 2):
                    print("sdk_platform_status = {}, but run DJI sdk".format(
                            sdk_platform_status.value))
                    raise PlatformException("")

                args = action_info['api_info']
                if real_car:
                    CAR_HANDLER.do_move_api(args)
                else:
                    # for _ in range(20):
                    #     grd_location_syncer['y']+=20
                    #     time.sleep(0.5)
                    time.sleep(2)
                    pass
                
                action_reply_message = "usr_action_success"
            
            info = {
                'msg':action_reply_message
            }
            reply_json['info']=info
            controller_message.put(json.dumps(reply_json))

        elif action_type == 'SIM_SYNCER':
            pos_info = action_info['api_info']
            if real_car:
                sensor_info = CAR_HANDLER.reset_simulate_syncer(pos_info)
                # info = SIM_SENDER.update_angle_data_info()
                # info = PHY_INFO.get_yaw_ground_angle()
                pass
            else:
                sensor_info = json.dumps(pos_info)

            info = {
                'msg':"sim_syncer_success"
            }
            
            reply_json['info']=info
            controller_message.put(json.dumps(reply_json))
            
            pass
    
    # 如果sdk不再运行，其他模块也需要退出
    global_status = platform_status_resources['global']
    global_status.value = -1
        
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

#     print("Proc [{}] end".format(proc_name)