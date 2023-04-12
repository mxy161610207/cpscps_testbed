import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# 读入迷宫信息
with open('maze.txt', 'r') as f:
    M,W,H = map(int, f.readline().split())
    walls = []
    for _ in range(M):
        x1, y1, x2, y2 = map(int, f.readline().split())
        walls.append((x1, y1, x2, y2))

# 初始位置
x, y = 1, 1
dx, dy = 1, 0

# 绘制迷宫地图
fig, ax = plt.subplots()
ax.set_aspect('equal')
for x1, y1, x2, y2 in walls:
    ax.plot([x1, x2], [y1, y2], color='black')
point, = ax.plot(x, y, marker='o', color='blue', markersize=10)
arrow = ax.arrow(x, y, dx, dy, head_width=0.2, head_length=0.3, fc='blue', ec='blue')

# 解决迷宫问题
def solve(x, y, dx, dy):
    while True:
        # 判断是否到达终点
        if x == W and y == H:
            return [(x, y)]
        
        # 沿着右手边走
        if not (x+dy, y-dx) in walls:
            dx, dy = dy, -dx
        elif not (x+dx, y+dy) in walls:
            pass
        elif not (x-dy, y+dx) in walls:
            dx, dy = -dy, dx
        else:
            dx, dy = -dx, -dy
        
        # 移动到下一个位置
        x, y = x+dx, y+dy
        yield x, y

# 动画更新函数
def update(frame):
    x, y = frame
    point.set_data(x, y)
    arrow.set_positions([x, y, x+dx, y+dy])
    return point, arrow

# 创建动画
ani = FuncAnimation(fig, update, frames=solve(x, y, dx, dy), interval=100)
plt.show()
