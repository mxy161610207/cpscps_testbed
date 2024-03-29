import matplotlib.pyplot as plt
import math
import numpy as np

from location.location_list import LocationList
from location.position import Position
from location.candidate import PositionCands

def calc_intersection(x, y, rad, E):    

    # 判断垂直于 x 轴的情况
    if np.isclose(rad, math.radians(90)) or np.isclose(rad, math.radians(270)):
        return [[x, -E/2], [x, E/2]], ['L', 'R']
    
    # 截距
    b = y - math.tan(rad) * x

    # 计算直线与方形四条边的交点
    x1 = (-E/2 - b) / math.tan(rad)
    x2 = (E/2 - b) / math.tan(rad)
    y1 = math.tan(rad) * (-E/2) + b
    y2 = math.tan(rad) * (E/2) + b
    
    intersections = []
    positions = []
    # 判断交点是否在上下边界上
    # UDLR 
    if x1 >= -E/2 and x1 <= E/2:
        intersections.append([x1, -E/2])
        positions.append('D')
    if x2 >= -E/2 and x2 <= E/2:
        intersections.append([x2, E/2])
        positions.append('U')
    # 判断交点是否在左右边界上
    if y1 >= -E/2 and y1 <= E/2:
        if not intersections:
            # 如果前面没有加入过交点，则直接添加
            intersections.append([-E/2, y1])
            positions.append('L')
        elif not np.isclose(intersections[0][1], y1):
            # 如果之前加入的交点和当前交点的 y 坐标不相等，则添加新的交点
            intersections.append([-E/2, y1])
            positions.append('L')
    if y2 >= -E/2 and y2 <= E/2:
        if not intersections:
            intersections.append([E/2, y2])
            positions.append('R')
        elif not np.isclose(intersections[0][1], y2):
            intersections.append([E/2, y2])
            positions.append('R')
        
    return intersections, positions


def euclidean_distance(p_car, p_inter):
    return ((p_car[0] - p_inter[0])**2 + (p_car[1] - p_inter[1])**2)**0.5

def draw_car_position(E,x,y,a,ax):
    # # 绘图时修饰和转换
    # x-=E/2.0
    # y-=E/2.0

    rad = math.radians(a)
    # 截距
    b = y - np.tan(rad) * x


    # 方型场地
    # square = plt.Rectangle((-E/2, -E/2), E, E, edgecolor='black', facecolor='none')
    # ax.add_patch(square)

    # 点
    ax.scatter(x, y,c='gray',s=50)

    # 计算直线与方型边界的交点
    wall_tag=[] # FBLR
    inter_points = []
    ps,tag = calc_intersection(x,y,rad,E)
    inter_points.extend(ps)
    wall_tag.extend(tag)

    ps,tag = calc_intersection(x,y,math.radians(a+90),E)
    inter_points.extend(ps)
    wall_tag.extend(tag)

    # 其他处理
    ir_tag = ['F','B','L','R']
    ir_color = ['red','purple','green','blue']

    print(ir_tag)
    print(wall_tag)

    dist = []
    md_dist = [131,99,119,119]

    for i,p in enumerate(inter_points):
        # 画线
        ls = '--'
        if (i==0): ls = '-'
        ax.plot([x,p[0]],[y,p[1]],linewidth=1, color=ir_color[i],linestyle=ls)
        # 画交点
        ax.scatter(p[0], p[1],c=ir_color[i],s=25)

        # 算红外线长度
        d = round(euclidean_distance([x,y],p))
        d -=md_dist[i]
        dist.append(d)


    print(dist)

    plt.axis('scaled')
    ax.set_xlim([-E//2,E//2])
    ax.set_ylim([-E//2,E//2])
    plt.axvline(x=0, color='gray', linestyle='--')
    plt.axhline(y=0, color='gray', linestyle='--')
    


syncer = {
    'x':0,
    'y':0,
    'deg':0,
    'rad':math.radians(0)
}


# True 2174.972118229169 1766.1383389725195 51.49781089490035
# True 2171.798091283207 1769.0778981953413 51.234350089705536
# True 2189.2008905854314 1788.3591192298486 52.441748791616114 -----
# True 2218.047583779054 1820.0102542231562 50.555865444070555
# True 2246.1005226806365 1861.0300038254095 54.135683446763316 
# True 2278.8229857269775 1903.1129795741658 49.49676692855967  
# True 2309.5167548312625 1940.091675968659 53.97584790185583
# True 2342.8067180252506 1984.8855965866753 49.226770922151985
# True 2380.806129591816 2029.0356720867628 53.754423150992615

x,y,a =  map(float,"2189.2008905854314 1788.3591192298486 52.44174879161611".split(" "))
nx,ny,na = map(float,"2218.047583779054 1820.0102542231562 50.555865444070555".split(" "))

print(x-2720//2,y-2720//2)
car_pos = Position({'x':x,'y':y,'rad':math.radians(a)},
            is_irs_center=True)
cur_pos_cand = PositionCands(car_pos)
print(car_pos._ir_inter_walls)
irs = cur_pos_cand.expand_next_conn_status()
# print(irs)
# modified distance FRBL = [909, 1566, 665, 2416]


lst = LocationList(syncer=syncer)
lst.append(cur_pos_cand)
print(lst.current_postion.pos_str)

# 前后左右的顺序
sensor_data = [659,2254,1299,532]
msg = []

lst.advance_once(sensor_data,msg)

# [2, 2, 0, 1]

print(lst.current_postion.pos_str)
# print("\n".join(msg))

fig, ax = plt.subplots()

print("ideal = ",nx,ny,na)


# x,y,a = 2266.5835404216114,688.2698481247011,-42.198228277783095
# x-=E//2
# y-=E//2
# draw_car_position(E,x,y,a,ax)

# x,y,a = 2264.7728776352565,686.2291694299308,-59.35585991638837
# x-=E//2
# y-=E//2
# draw_car_position(E,x,y,a,ax)


# plt.show()