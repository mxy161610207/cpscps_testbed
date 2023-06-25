import time

def get_neighour(sensor,edge_len):
    dir = ['F','B','L','R']
    status = [0]*4
    for i in range(4):
        dis = sensor[dir[i]]
        if dis>edge_len*800:
            status[i]=1

    return status

def run(ep_robot,sensor):
    ep_chassis = ep_robot.chassis
    edge_len=0.9

    # 定义四个方向的偏移量
    # 前后左右
    dx = [1, -1, 0, 0]
    dy = [0, 0, -1, 1]
    dir = "FBLR"

    with open('decision.txt', 'w') as f:
        action = "FLFRFLBRBLFLBLFRFLFLFLFRBRFRFL"
        for s in action:
            status = get_neighour(sensor,edge_len)
            dis = sensor[dis]

            left = 170
            if (dis>left and dis-left>200):
                dis-=left
                dis=dis/1000
                
                d=0
                for _ in range(4):
                    if (dir[_]==s):
                        d=_
                        break
                
                print(sensor,file=f)
                print(status,file=f)

                ep_chassis.move(dx[d]*dis,dy[d]*dis,0,0.6,0).wait_for_completed()
                time.sleep(1)

            