import math 

# 返回值：
# x - 向前移动距离
# y - 向左移动距离
# deg - 逆时针旋转角度
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


last = {
    'x':829.2,
    'y':428.3,
    'deg':52.4
}

cur = {
    'x':857.9,
    'y':460.9,
    'deg':50.7
}

diff = get_diff_json(last,cur)
print(diff)