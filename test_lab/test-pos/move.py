import math

def get_diff_json(last,cur):
    # rad = (rad - math.pi/2.0)
    rad = math.radians(last['deg'])

    dx = cur['x']-last['x']
    dy = cur['y']-last['y']
    ddeg = cur['deg']-last['deg']
    drad = math.radians(ddeg)

    rot_mat = [ [math.cos(rad), math.sin(rad)],     # 前方
                [-math.sin(rad), math.cos(rad)]]    # 左方
    # print("rot_mat =",rot_mat)
    # print("dx dy =",dx,dy)
    tx = rot_mat[0][0]*dx + rot_mat[0][1]*dy
    ty = rot_mat[1][0]*dx + rot_mat[1][1]*dy
    # print("tx ty =",tx,ty)

    diff_json={
        'x':tx,
        'y':ty,
        'deg':ddeg,
        'rad':drad
    }

    return diff_json

def generate_json(x,y,deg):
    tmp = {
    'x':x,      #  前后距离
    'y':y,      #  左右距离
    'deg':deg,
    'rad':math.radians(deg)
    }
    return tmp

curr = generate_json(0,0,45)
next = generate_json(1,1,30)

# curr = generate_json(1,2,-45)
# next = generate_json(3,2,-45)

diff = get_diff_json(curr,next)
print(diff)

# 假设小车的长度为L，宽度为W，则在自身坐标系下，前后方向的位移量为：

# $d_{f} = (x_{2}-x)\cos{a} + (y_{2}-y)\sin{a}$

# $d_{b} = -(x_{2}-x)\cos{a} - (y_{2}-y)\sin{a}$

# 左右方向的位移量为：

# $d_{l} = -(x_{2}-x)\sin{a} + (y_{2}-y)\cos{a}$

# $d_{r} = (x_{2}-x)\sin{a} - (y_{2}-y)\cos{a}$

# 其中，$d_{f}$表示小车前进的距离，$d_{b}$表示小车后退的距离，$d_{l}$表示小车向左移动的距离，$d_{r}$表示小车向右移动的距离。