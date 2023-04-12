def get_distance(ep_sensor):
    print(ep_sensor)
    pass

def run(ep_robot):
    ep_sensor = ep_robot.sensor
    ep_chassis = ep_robot.chassis

    while True:
        dis_F,_,_,dis_R = get_distance(ep_sensor)
        if dis_R<0.1:
            if (dis_F<0.1):
                ep_chassis.drive_speed(0,0,0)
                ep_chassis.move(0,0,90).wait_for_completed()
            else:
                ep_chassis.drive_speed(0.3,0,0)
        else:
            ep_chassis.move(0,0,-90).wait_for_completed()
            ep_chassis.move(0.45,0,0).wait_for_completed()












