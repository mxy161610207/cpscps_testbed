from platform_robot import robot
# from robomaster import robot
import time

def get_neighour(sensor,edge_len):
    dir = ['F','B','L','R']
    print('[APP]',sensor)
    status = [0]*4
    for i in range(4):
        dis = sensor[dir[i]]
        if dis>edge_len*0.8*1000:
            status[i]=1

    return status

def dfs(px,py,vis,act,
        ep_chassis,sensor,edge_len):
    
    global finished,dx,dy 
    if (px==0 and py==0):
        finished=True
        return
  
    vis.append((px,py))
    
    # 四个方向哪些可行
    dir = "FBLR"
    status = get_neighour(sensor,edge_len)
    for d,state in enumerate(status):
        if (state==0):continue
        nx=px-dx[d]
        ny=py+dy[d]
        if ((nx,ny) in vis):continue

        # 当前方向可行，确定前进距离
        if (sensor[dir[d]]>edge_len*2):
            dis = edge_len
        else:
            dis = sensor[dir[d]]
            left = 170
            if (dis>left and dis-left>200):
                dis-=left
            dis=dis/1000

        act.append(dir[d])
        for _ in range(3):
            print(dir[d],dx[d]*dis,dy[d]*dis)
        ep_chassis.move(dx[d]*dis,dy[d]*dis,0,0.6,0).wait_for_completed()
        time.sleep(1)
        dfs(nx,ny,vis,act,ep_chassis,sensor,edge_len)
        if not finished:
            act.pop(-1)
            ep_chassis.move(-dx[d]*dis,-dy[d]*dis,0,0.6,0).wait_for_completed()
            time.sleep(1)
        else:
            return

    vis.remove((px,py))

def run(ep_robot,sensor):
    ep_chassis = ep_robot.chassis
    edge_len=1.0
    maze_size=6

    global finished,dx,dy  
    finished=False  
    # 定义四个方向的偏移量
    # 前后左右
    dx = [1, -1, 0, 0]
    dy = [0, 0, -1, 1]

    px,py=maze_size-1,maze_size-1
    vis = []
    act = []

    dfs(px,py,vis,act,ep_chassis,sensor,edge_len)
    
    with open('decision.txt', 'w') as f:
        print(vis,file=f)
        print(act,file=f)

def run1(ep_robot,sensor):
    ep_chassis = ep_robot.chassis
    ep_chassis.move(0,0,90).wait_for_completed()
    time.sleep(1)
    ep_chassis.move(0.5,0,0).wait_for_completed()
    time.sleep(1)
    ep_chassis.move(-0.5,0,0).wait_for_completed()
    time.sleep(1)

def run2(ep_robot,sensor):
    for _ in range(3):
        print(sensor)
        time.sleep(0.3)

# ------- 下面是将论文中的usr_register 函数转为一个大疆程序的辅助代码 --------

def sub_data_handler(distance,distance_logger):
    distance_logger['F'] = distance[0]
    distance_logger['R'] = distance[1]
    distance_logger['B'] = distance[2]
    distance_logger['L'] = distance[3]

if __name__ == '__main__':
    ep_robot = robot.Robot()
    ep_robot.initialize(conn_type='sta')

    distance_logger = {'F':0, 'B':0, 'L':0, 'R':0 }
    ep_sensor = ep_robot.sensor
    ep_sensor.sub_distance(5, sub_data_handler, distance_logger)

    run(ep_robot,distance_logger)

    ep_sensor.unsub_distance()