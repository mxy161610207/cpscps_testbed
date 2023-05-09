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

# x,y,a =  2246.1005226806365,1861.0300038254095,54.135683446763316

# True 2246.1005226806365 1861.0300038254095 54.135683446763316 -----
# True 2278.8229857269775 1903.1129795741658 49.49676692855967  
# True 2309.5167548312625 1940.091675968659 53.97584790185583

# cx,cy,ca =  map(float,"2189.2008905854314 1788.3591192298486 52.44174879161611".split(" "))
# nx,ny,na = map(float,"2218.047583779054 1820.0102542231562 56.555865444070555".split(" "))


cx,cy,ca =  map(float,"2218.047583779054 1820.0102542231562 65.44174879161611".split(" "))
# cx,cy,ca =  map(float,"2142.888 2077.385 65.44174879161611".split(" "))
nx,ny,na = map(float,"2218.047583779054 1820.0102542231562 50.555865444070555".split(" "))

# 这是FRBL的交点状态
cur_irs_status = get_irs_status(cx,cy,ca,E)
nxt_irs_status = get_irs_status(nx,ny,na,E)

# 转为[-E/2, E/2]下的坐标
cx-=E/2
cy-=E/2
nx-=E/2
ny-=E/2
print(cx,cy,ca)
print(nx,ny,na)



# 这是FRBL的交点
cur_irs_point = calc_intersection(cx,cy,math.radians(ca),E,cur_irs_status)
nxt_irs_point = calc_intersection(nx,ny,math.radians(na),E,nxt_irs_status)


cur_dist = []
nxt_dist = []

md_dist = [131,119,99,119] # FRBL的距离补偿
raw_dist = []
for i,p in enumerate(cur_irs_point):
    # 算红外线长度
    d = round(euclidean_distance([cx,cy],p))
    raw_dist.append(d)
    d -=md_dist[i]
    cur_dist.append(d)
print(cur_dist)
# print(cur_dist)

raw_dist = []
for i,p in enumerate(nxt_irs_point):
    # 算红外线长度
    d = round(euclidean_distance([nx,ny],p))
    raw_dist.append(d)
    d -=md_dist[i]
    nxt_dist.append(d)
print("FRBL",nxt_dist)
print("FBLR = [{},{},{},{}]".format(
    nxt_dist[0],nxt_dist[2],nxt_dist[3],nxt_dist[1]
))

# 画图
fig, ax = plt.subplots()

x1,x2,y1,y2 = nx-60,nx+60,ny-60,ny+60
ax.plot([x1, x1], [y1, y2], color='red')
ax.plot([x2, x2], [y1, y2], color='red')
ax.plot([x1, x2], [y1, y1], color='red')
ax.plot([x1, x2], [y2, y2], color='red')

# ax.scatter(cx,cy,c='orange',s=50)
# for i,p in enumerate(cur_irs_point):
#     ax.scatter(p[0], p[1],c='orange',s=50)
#     ls = '--'
#     if (i==0): ls = '-'
#     ax.plot([cx,p[0]],[cy,p[1]],linewidth=1, color='orange',linestyle=ls)

ax.scatter(nx,ny,c='blue',s=50)
for i,p in enumerate(nxt_irs_point):
    ax.scatter(p[0], p[1],c='blue',s=50)
    ls = '--'
    if (i==0): ls = '-'
    ax.plot([nx,p[0]],[ny,p[1]],linewidth=1, color='blue',linestyle=ls)

plt.axis('scaled')
ax.set_xlim([-E//2-10,E//2+10])
ax.set_ylim([-E//2-10,E//2+10])
plt.axvline(x=0, color='grey', linestyle='--')
plt.axhline(y=0, color='grey', linestyle='--')

plt.show()
