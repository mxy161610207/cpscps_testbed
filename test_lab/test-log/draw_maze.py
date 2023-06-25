import matplotlib.pyplot as plt
import math 
import random
import time

random.seed()

dot = None
arw = None
ar_len = 0.2
step_len = 1

def is_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    # 判断两条线段所在直线是否平行
    dx1, dy1 = x2-x1, y2-y1
    dx2, dy2 = x4-x3, y4-y3
    det = dx1*dy2 - dx2*dy1
    if det == 0:
        return False
    
    # 计算交点参数 t1 和 t2
    dx3, dy3 = x3-x1, y3-y1
    t1 = (dy2*dx3 - dx2*dy3) / det
    t2 = (dy1*dx3 - dx1*dy3) / det
    
    # 判断交点是否在两条线段上
    if 0 <= t1 <= 1 and 0 <= t2 <= 1:
        return True
    else:
        return False


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


actions="FLFRFLFF"
idx=0

def update(act):
    global x, y, deg
    if act == 'F':
        new_x= x+step_len * math.cos(math.radians(deg))
        new_y= y+step_len * math.sin(math.radians(deg))

        hit_wall = False
        for x1, y1, x2, y2 in walls:
            if (is_intersect(x,y,new_x,new_y,x1,y1,x2,y2)):
                hit_wall = True
                break
        if not hit_wall:
            move_dis = step_len+ 0.05*deg_noisy()
            x = x+move_dis * math.cos(math.radians(deg))
            y = y+move_dis * math.sin(math.radians(deg))
            deg = deg+deg_noisy(1)
            update_color('blue')
        else:
            update_color('red')
    elif act == 'L':
        deg = (deg+90+deg_noisy())%360
    elif act== 'R':
        deg = (deg+270+deg_noisy())%360
    
    draw_car(ax,x,y,deg)
    plt.draw()

# 键盘事件回调函数
def on_key_press(event):
    global x, y, deg,idx,actions
    print (event.key)
    if (event.key=='enter'):
        if idx>=len(actions): 
            update_color('grey')
        else:
            update(actions[idx])
            idx+=1
        
        draw_car(ax,x,y,deg)
        plt.draw()

# 将键盘事件连接到回调函数
fig.canvas.mpl_connect('key_press_event', on_key_press)
plt.show()