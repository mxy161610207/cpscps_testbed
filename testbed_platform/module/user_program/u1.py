
# 判断前后左右是否可行
def get_neighour(sensor,edge_len):
    dir = ['F','B','L','R']
    status = [0]*4
    for i in range(4):
        dis = sensor[dir[i]]
        if dis>edge_len:
            status[i]=1
    return status

# 深度优先搜索函数
def dfs(x, y, maze, sensor , edge_len, N , ep_chassis):
    # 标记当前格子已访问
    maze[x][y] = 1

    if (x==N-1 and y==N-1):
        return True

    # 定义四个方向的偏移量
    # 前后左右
    dx = [1, -1, 0, 0]
    dy = [0, 0, -1, 1]

    status = get_neighour(sensor,edge_len)

    # 遍历四个方向的邻格
    for i in range(4):
        if (not status[i]): continue

        nx = x + dx[i]
        ny = y + dy[i]

        # 判断邻格是否在迷宫范围内
        if nx < 0 or nx >= N or ny < 0 or ny >= N:
            continue

        # 判断邻格是否已访问，若已访问，放弃
        if maze[nx][ny] == 1:
            continue
        
        # 移动车
        ep_chassis.move(dx*edge_len,dy*edge_len,0,0.3,0).wait_for_completed()
        can = dfs(nx,ny,maze,sensor,edge_len,N,ep_chassis)
        if (not can):
            ep_chassis.move(dx*edge_len,dy*edge_len,0,0.3,0).wait_for_completed()
        else:
            return True
    
    return False

def run(ep_robot,sensor):
    # 定义迷宫大小,单元格长度和迷宫数组
    N=4
    edge_len=0.9
    maze = [[0] * N for _ in range(N)]


    ep_chassis = ep_robot.chassis
    # 从起点开始搜索
    dfs(0, 0,maze,sensor,edge_len,N,ep_chassis)