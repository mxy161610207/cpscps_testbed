import robomaster
from robomaster import robot
import os,time


position = {'x':0,'y':0,'deg':0}
init_angle=0
init=False

def sub_position_handler(position_info):
    x, y, z = position_info

    global position
    # print("chassis position: x:{0}, y:{1}, z:{2}".format(x, y, z))

    # move x=1 (1,0) 0
    # move y=1 (0,-1) 0

    position['x']=x
    position['y']=-y
    print(position)


def sub_data_handler(angle_info):
    pitch_angle, yaw_angle, pitch_ground_angle, yaw_ground_angle = angle_info

    global position
    global init_angle,init
    if not init:
        init=True
        init_angle = yaw_ground_angle
        print("init",init_angle)
    # yaw_angle 云台和底盘角度
    # yaw_ground_angle 云台从开机后的角度
    
    # 初始0度 左转 z=90 angle变-90 所以取反 
    cur_angle = -(yaw_ground_angle-init_angle)
    if (cur_angle<0): cur_angle+=360
    position['deg'] = cur_angle

    # print(cur_angle)


    # print("gimbal angle: pitch_angle:{0}, yaw_angle:{1}, pitch_ground_angle:{2}, yaw_ground_angle:{3}".format(
    #     pitch_angle, yaw_angle, pitch_ground_angle, yaw_ground_angle))

if __name__ == '__main__':
    ep_robot = robot.Robot()
    try:
        ep_robot.initialize(conn_type="ap")
    except:
        print("initialize fail!")
        os._exit(0)

    ep_robot.set_robot_mode(mode=robot.CHASSIS_LEAD)

    ep_chassis = ep_robot.chassis

    ep_gimbal = ep_robot.gimbal

    # 订阅底盘位置信息
    ep_chassis.sub_position(freq=10, callback=sub_position_handler)
    ep_gimbal.sub_angle(freq=10, callback=sub_data_handler)

    time.sleep(1)
    input("pause>")


    # ep_chassis.move(z=90).wait_for_completed()
    # ep_chassis.move(x=0.1).wait_for_completed()
    # ep_chassis.move(y=0.1).wait_for_completed()

    print(position)
    # ep_chassis.move(x=0.1).wait_for_completed()
    # ep_chassis.move(z=90).wait_for_completed()
    # ep_chassis.move(x=0.1).wait_for_completed()
    time.sleep(1)
    print(position)
    # # ep_chassis.move(z=90).wait_for_completed()
    # time.sleep(1)
    # print(position)
    # # ep_chassis.move(z=90).wait_for_completed()
    # # ep_chassis.move(x=0.1).wait_for_completed()
    # time.sleep(1)
    # print(position)

    # input("pause>")

    ep_gimbal.unsub_angle()
    ep_chassis.unsub_position()

    ep_robot.close()
