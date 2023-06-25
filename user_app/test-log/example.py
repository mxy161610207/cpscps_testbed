import robomaster
from robomaster import robot
import time

if __name__ == '__main__':
    ep_robot = robot.Robot()
    ep_robot.initialize(conn_type="ap")
    ep_robot.set_robot_mode(mode=robot.CHASSIS_LEAD)

    while True:
        front_dist = ep_robot.sensor.get_distance_info()[0]

        if (front_dist<2000):
            ep_robot.chassis.drive_speed(0,0,0)
            break
        else:
            ep_robot.chassis.drive_speed(0.6,0,0)

        time.sleep(0.5)

    ep_robot.close()