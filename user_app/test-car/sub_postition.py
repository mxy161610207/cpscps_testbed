import robomaster
from robomaster import robot
import os,time


def do_action(ep_chassis,action, move_dis=0.5,rot_deg=90,mute=False):
    xy_speed=0.6
    z_speed=60
    if (action == 'W'):
        # ep_chassis.move(move_dis,0,0,xy_speed,z_speed).wait_for_completed()
        ep_chassis.drive_speed(x=0.2)
        time.sleep(2.25)
        ep_chassis.move(0,0,0).wait_for_completed()

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
        ep_chassis.move(0,0,180,xy_speed,z_speed).wait_for_completed()


position = {'x':0,'y':0,'deg':0}
init_angle=0
init=False
F=0

def sub_sensor_handler(distance_info):
    global F,fp
    F,_,_,_ = distance_info
    print(distance_info,f=fp)

def sub_position_handler(position_info):
    x, y, z = position_info

    global position,fp
    # print("chassis position: x:{0}, y:{1}, z:{2}".format(x, y, z))

    # move x=1 (1,0) 0
    # move y=1 (0,-1) 0

    position['x']=x
    position['y']=-y
    print(position,f=fp)

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
    global fp 
    fp = open("a-{}.txt".format(time.time()),"w")
    ep_robot = robot.Robot()
    try:
        ep_robot.initialize(conn_type="sta")
    except:
        print("initialize fail!")
        os._exit(0)

    ep_robot.set_robot_mode(mode=robot.CHASSIS_LEAD)

    ep_chassis = ep_robot.chassis
    ep_sensor = ep_robot.sensor
    ep_gimbal = ep_robot.gimbal

    # 订阅底盘位置信息
    ep_chassis.sub_position(freq=50, callback=sub_position_handler)
    ep_sensor.sub_distance(freq=50, callback=sub_sensor_handler)
    ep_gimbal.sub_angle(freq=50, callback=sub_data_handler)

    time.sleep(1)
    d=0.45

    while(True):
        s = input("action>")
        if s=='Q' or s=='q':
            break
        
        for ch in s:
            do_action(ep_chassis,ch,move_dis=d)
    
    time.sleep(1)

    ep_gimbal.unsub_angle()
    ep_sensor.unsub_distance()
    ep_chassis.unsub_position()

    ep_robot.close()
