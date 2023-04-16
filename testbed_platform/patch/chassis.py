import robomaster.chassis as offical
from robomaster.chassis import *

import threading,time,math

from robomaster import dds
from robomaster import module
from robomaster import logger
from robomaster import protocol
from robomaster import util
from robomaster import action

from module import sdk_handler
from patch.safe_action import SafeChassisMoveAction
from module.platform_timer import PlatformTimer
'''
class Chassis(module.Module):
'''

def _md_auto_stop_timer(self, api="drive_speed"):
    if api == "drive_speed":
        logger.info("Chassis: drive_speed timeout, auto stop!")
        # drive_speed issue：缓慢顺时针旋转。所以这里用drive_wheels
        # https://github.com/dji-sdk/RoboMaster-SDK/issues/47
        self.drive_wheels(0, 0, 0, 0)
    elif api == "drive_wheels":
        logger.info("Chassis: drive_wheels timeout, auto stop!")
        self.drive_wheels(0, 0, 0)
    else:
        logger.warning("Chassis: unsupported api:{0}".format(api))

    # sdk_handler.DRIVE_SPEED_ADJUSTER.proto_clear()
    sdk_handler.SECURITY_MONITOR.event_set_by("END")

def md_drive_speed(self, x=0.0, y=0.0, z=0.0, timeout=None):
    """ 修改后的drive_speed
    """
    print("__modify__ drive_speed")
    proto = protocol.ProtoChassisSpeedMode()
    proto._x_spd = util.CHASSIS_SPD_X_CHECKER.val2proto(x)
    proto._y_spd = util.CHASSIS_SPD_Y_CHECKER.val2proto(y)
    proto._z_spd = util.CHASSIS_SPD_Z_CHECKER.val2proto(z)
    
    logger.info("x_spd:{0:f}, y_spd:{1:f}, z_spd:{2:f}".format(proto._x_spd, proto._y_spd, proto._z_spd))

    return sdk_handler.DRIVE_SPEED_ADJUSTER.register_proto(self, proto,timeout)


def md_move(self, x=0.0, y=0.0, z=0.0, xy_speed=0.5, z_speed=30):
    """ 修改后的move
    """
    action = SafeChassisMoveAction(self, x, y, z, xy_speed, z_speed)
    return action


# 订阅位置
def sys_sub_handler(self, sub_info):
        """ mxy_edit
        真实位置传感器 sys_sub 的callback函数
        将真实位置值发送给server
        """
        sdk_handler.PHY_SENDER.set_position_data_info(sub_info)
        pass


# 数据订阅接口
def sys_sub(self, cs=0, freq=5, callback=None, *args, **kw):
    """ mxy_edit
    订阅底盘位置信息
    在robot.initialize中被首次使用

    :param cs: int: [0,1] 设置底盘位置的坐标系，0 机器人当前位置，1 机器人上电位置
    :param freq: enum: (1, 5, 10, 20, 50) 设置数据订阅数据的推送频率，单位 Hz
    :param callback: 回调函数，返回数据 (x, y, z):

                    :x: x轴方向距离，单位 m
                    :y: y轴方向距离，单位 m
                    :z: z轴方向旋转角度，单位 °

    :param args: 可变参数
    :param kw: 关键字参数
    :return: bool: 数据订阅结果
    """
    print("开启platfrom订阅: position")

    sub = self._robot.dds
    subject = offical.PositionSubject(cs)
    self._max_freq = 10
    subject.freq = self._max_freq
    callback = self.sys_sub_handler

    self._subject = subject

    return sub.add_subject_info(subject, callback, args, kw)

def sys_unsub(self):
    """ mxy_edit 
    取消订阅底盘位置信息

    :return: bool: 取消数据订阅的结果
    """
    sub_dds = self._robot.dds
    return sub_dds.del_subject_info(dds.DDS_POSITION)

def md_sub_position(self, cs=0, freq=5, callback=None, *args, **kw):
    """ mxy_edit
        用户调用的 订阅底盘位置信息

        原: 大疆提供的订阅接口，新增一个Subject
        改：在sys的Subject上 新增usr_sub信息
    """
    
    usr_loop = self._max_freq // freq
    return self._subject.set_usr_sub(usr_loop,callback,args,kw)

def md_unsub_position(self):
    """ mxy_edit
    用户调用的 取消订阅底盘位置信息
    """
    return self._subject.set_usr_unsub()

'''
class ChassisMoveAction(action.Action):
'''
@property
def _encode_json(self):
    # move,x,y,z,xy_spd,z_spd
    encode_json={
        'api':'move',
        'x':self._x,
        'y':self._y,
        'z':self._z,
        'spd_xy':self._spd_xy,
        'spd_z':self._spd_z,
    }
    return encode_json



# modify list
offical.Chassis._dij_drive_speed = offical.Chassis.drive_speed
offical.Chassis._dij_move = offical.Chassis.move

offical.Chassis._auto_stop_timer = _md_auto_stop_timer
offical.Chassis.drive_speed = md_drive_speed
offical.Chassis.move = md_move

# 位置传感器相关，没用。
# offical.Chassis.sys_sub_handler = sys_sub_handler
# offical.Chassis.sys_sub = sys_sub
# offical.Chassis.sys_unsub = sys_unsub

# offical.Chassis.sub_position = md_sub_position
# offical.Chassis.unsub_position = md_unsub_position

offical.ChassisMoveAction._encode_json = _encode_json

