import matplotlib.pyplot as plt
import math 
import random
import time

random.seed()

dot = None
arw = None
ar_len = 0.2
step_len = 1

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

def update_color(color = 'blue'):
    global dot
    dot.set_color(color) # 将颜色更改为红色

def deg_noisy(n=1):
    return random.randint(-n,n)

# 读入迷宫信息
with open('maze.txt', 'r') as f:
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
ax.set_xlim([-1,W+1])
ax.set_ylim([-1,H+1])
for x1, y1, x2, y2 in walls:
    ax.plot([x1, x2], [y1, y2], color='black')
    
draw_car(ax,x,y,deg)


plt.show()