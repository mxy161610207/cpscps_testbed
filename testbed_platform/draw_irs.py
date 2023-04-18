import matplotlib.pyplot as plt
import math
import numpy as np

from location.location_list import LocationList
from location.position import Position
from location.candidate import PositionCands

def calc_intersection(cx,cy,crad,E,irs_status):
    irs = []
    for i in range(4):
        wid = irs_status[i]
        if (i%2==0):
            tanx = math.tan(crad)
        else:
            tanx = math.tan(crad+math.radians(90))

        if wid == 0 or wid == 2:
            iy = E/2 if wid==0 else -E/2
            dy = iy - cy
            dx = dy/tanx
            ix = dx+cx
        else:
            ix = E/2 if wid==1 else -E/2
            dx = ix - cx
            dy = tanx*dx
            iy = dy+cy

        irs.append([ix,iy])
        # print([ix,iy])
    return irs

def euclidean_distance(p_car, p_inter):
    return ((p_car[0] - p_inter[0])**2 + (p_car[1] - p_inter[1])**2)**0.5

def get_irs_status(cx,cy,ca,E):
    car_pos = Position({'x':cx,'y':cy,'rad':math.radians(ca)},
                is_irs_center=True)
    irs_status = car_pos._ir_inter_walls[:]
    print(irs_status)
    return irs_status

E = 2720
# Positon 用的坐标系是(0,E)
cx,cy,ca = 2088.5835404216114,688.2698481247011,-40.198228277783095+360
nx,ny,na = 2054.7728776352565,675.2291694299308,-46.35585991638837+360


cur_irs_status = get_irs_status(cx,cy,ca,E)
nxt_irs_status = get_irs_status(nx,ny,na,E)

# 转为[-E/2, E/2]下的坐标
cx-=E/2
cy-=E/2
nx-=E/2
ny-=E/2
print(cx,cy,ca)
print(nx,ny,na)

cur_irs_point = calc_intersection(cx,cy,math.radians(ca),E,cur_irs_status)
nxt_irs_point = calc_intersection(nx,ny,math.radians(na),E,nxt_irs_status)


cur_dist = []
nxt_dist = []

md_dist = [131,99,119,119]
for i,p in enumerate(cur_irs_point):
    # 算红外线长度
    d = round(euclidean_distance([cx,cy],p))
    d -=md_dist[i]
    cur_dist.append(d)
print(cur_dist)

for i,p in enumerate(nxt_irs_point):
    # 算红外线长度
    d = round(euclidean_distance([nx,ny],p))
    d -=md_dist[i]
    nxt_dist.append(d)
print(nxt_dist)


# 画图
fig, ax = plt.subplots()

ax.scatter(cx,cy,c='gray',s=50)
ax.scatter(nx,ny,c='red',s=50)

for i,p in enumerate(cur_irs_point):
    ax.scatter(p[0], p[1],c='gray',s=50)
    ls = '--'
    if (i==0): ls = '-'
    ax.plot([cx,p[0]],[cy,p[1]],linewidth=1, color='gray',linestyle=ls)

for i,p in enumerate(nxt_irs_point):
    ax.scatter(p[0], p[1],c='red',s=50)
    ls = '--'
    if (i==0): ls = '-'
    ax.plot([nx,p[0]],[ny,p[1]],linewidth=1, color='red',linestyle=ls)

plt.axis('scaled')
ax.set_xlim([-E//2-10,E//2+10])
ax.set_ylim([-E//2-10,E//2+10])
plt.axvline(x=0, color='gray', linestyle='--')
plt.axhline(y=0, color='gray', linestyle='--')

plt.show()
