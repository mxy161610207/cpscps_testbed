import matplotlib.pyplot as plt
import math
import numpy as np

def calc_intersection(x, y, rad, E):
    # 判断垂直于 x 轴的情况
    if np.isclose(rad, math.radians(90)) or np.isclose(rad, math.radians(270)):
        return [x, -E/2], [x, E/2], ['L', 'R']
    
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
    # 如果交点在角上，则添加另一个角的位置信息
    if len(intersections) == 2 and np.isclose(intersections[0], [-E/2, -E/2]).all() and np.isclose(intersections[1], [E/2, E/2]).all():
        positions = ['UL', 'LR']
        
    return intersections, positions

# E = 2700
# x,y = 1337.8580201029656,906.2727816119449
# a = -130.60503830719253 # 直线的角度，单位是度

# print(calc_intersection(x,y,math.radians(a),E))