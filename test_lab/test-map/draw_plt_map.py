import matplotlib.pyplot as plt
import math 
import random
import time

dot = None
arw = None
ar_len = 0.2
step_len = 1

map_name = "MapConfig_Large"

# len = 3
len=9

def draw_car(ax,x,y,deg):
    global dot,arw,ar_len

    dx = ar_len* math.cos(math.radians(deg))
    dy = ar_len* math.sin(math.radians(deg))

    print(x,y, dx,dy)

    if dot is None:
        dot = ax.scatter(x, y, marker='o', color='blue')
    else:
        dot.set_offsets([x,y])

    if arw is not None:
        arw.remove()
    arw = ax.arrow(x, y, dx, dy, head_width=0.1, fc='blue', ec='blue')

    return 

# 读入迷宫信息
with open('{}.txt'.format(map_name), 'r') as f:
    M,W,H = map(int, f.readline().split())
    walls = []
    for _ in range(M):
        x1, y1, x2, y2 = map(int, f.readline().split())
        walls.append((x1, y1, x2, y2))

# 初始位置
x, y = 0.5, 0.5
deg=0

# 绘制迷宫地图
fig, ax = plt.subplots()
ax.set_aspect('equal')
fig.set_size_inches(10,10)
ax.set_xlim([-1,11])
ax.set_ylim([-1,11])
# ax.set_xlim([-4,8])
# ax.set_ylim([-4,8])
for x1, y1, x2, y2 in walls:
    ax.plot([x1, x2], [y1, y2], color='black')


x1,y1,x2,y2 = 0.2,0.2,0.8,0.8
plt.plot([x1, x1, x2, x2, x1], [y1, y2, y2, y1, y1], color='green')
plt.text(0.5, 1, 'Start', ha='center', va='center', color = 'brown',fontsize=25)

# dx,dy=2,1
# dx,dy=4,5
dx,dy = 8,2
plt.plot([x1+dx, x1+dx, x2+dx, x2+dx, x1+dx], 
         [y1+dy, y2+dy, y2+dy, y1+dy, y1+dy], color='red')
plt.text(0.5+dx, dy+1, 'Midpoint', ha='center', va='center',color = 'brown', fontsize=25)

plt.plot([x1+len, x1+len, x2+len, x2+len, x1+len], [y1+len, y2+len, y2+len, y1+len, y1+len], color='blue')
plt.text(0.5+len, len, 'End', ha='center', va='center',color = 'brown',fontsize=25)


draw_car(ax,x,y,deg)

# 将键盘事件连接到回调函数
plt.savefig('{}_mid.png'.format(map_name),bbox_inches='tight', pad_inches=0)
plt.show()