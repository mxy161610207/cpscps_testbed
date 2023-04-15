import time

def run(ep_robot,sensor):
    edge_len = 1
    ep_chassis = ep_robot.chassis

    ep_chassis.drive_speed(0.3,0,0)
    while True:
        dis_F = sensor['F']
        if (dis_F<300):
            ep_chassis.move(-edge_len,0,0).wait_for_completed()
            break
        time.sleep(0.1)

    # while True:
    #     dis_F = sensor['F']
    #     dis_R = sensor['R']
    #     print("**********", dis_F,dis_R)
    #     if dis_R<600:
    #         if (dis_F<300):
    #             # ep_chassis.drive_speed(0,0,0)
    #             ep_chassis.move(0,0,0,0.5).wait_for_completed()
    #             ep_chassis.move(0,0,93,0.5).wait_for_completed()
    #         else:
    #             ep_chassis.move((dis_F-300)*0.001,0,0,0.5).wait_for_completed()
    #     else:
    #         ep_chassis.move(0,0,-90,0.5).wait_for_completed()
    #         ep_chassis.move(0.6,0,0,0.5).wait_for_completed()
    #     time.sleep(1)