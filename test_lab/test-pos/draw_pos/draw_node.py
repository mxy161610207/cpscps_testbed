import matplotlib.pyplot as plt
import math
import numpy as np

E = 2720

fig, ax = plt.subplots()

def draw_one_node(x,y,a,ax,co,need_change=True):
    # x,y,a = map(float,"2246.1005226806365 1861.0300038254095 54.135683446763316".split(" "))

    # x,y = E//2,E//2
    # a = 45 # 直线的角度，单位是度

    # True 2218.047583779054 1820.0102542231562 50.555865444070555

    # 修饰和转换
    if (need_change):
        x-=E/2.0
        y-=E/2.0
    rad = math.radians(a)
    # 截距

    len=100
    dx = len*math.cos(rad)
    dy = len*math.sin(rad)
    ax.arrow(x,y,dx,dy,color='black',width=1)
    ax.scatter([x], [y],c=co,s=50)

ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_aspect('equal')
ax.set_xlim([-E//2,E//2])
ax.set_ylim([-E//2,E//2])


# x,y,a =  map(float,"2142.888 2077.385 62.437".split(" "))
# draw_one_node(x,y,a,ax,'gray')

# 历史定位
x,y,a =  map(float,"829.2 428.3 52.4".split(" "))
draw_one_node(x,y,a,ax,'gray',need_change=False)

x,y,a =  map(float,"857.9 460.9 50.7".split(" "))
draw_one_node(x,y,a,ax,'red',need_change=False)
x,y,a =  map(float,"782.9 717.4 62.4".split(" "))
draw_one_node(x,y,a,ax,'blue',need_change=False)

# plt.axvline(x=0, color='gray', linestyle='--')
# plt.axhline(y=0, color='gray', linestyle='--')

plt.show()

plt.savefig('node.png')