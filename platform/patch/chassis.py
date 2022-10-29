import robomaster.chassis as offical
from robomaster.chassis import *

import threading,time,math

from robomaster import module
from robomaster import logger
from robomaster import protocol
from robomaster import util
from robomaster import action

import user_watcher
from patch.safe_action import SafeChassisMoveAction
from module.platform_timer import PlatformTimer
'''
class Chassis(module.Module):
'''

def _md_auto_stop_timer(self, api="drive_speed"):
    if api == "drive_speed":
        logger.info("Chassis: drive_speed timeout, auto stop!")
        self._dij_drive_speed(0, 0, 0)
    elif api == "drive_wheels":
        logger.info("Chassis: drive_wheels timeout, auto stop!")
        self.drive_wheels(0, 0, 0)
    else:
        logger.warning("Chassis: unsupported api:{0}".format(api))

    # user_watcher.DRIVE_SPEED_ADJUSTER.proto_clear()
    user_watcher.SECURITY_MONITOR.event_set_by("END")

def md_drive_speed(self, x=0.0, y=0.0, z=0.0, timeout=None):
    """ 修改后的drive_speed
    """
    proto = protocol.ProtoChassisSpeedMode()
    proto._x_spd = util.CHASSIS_SPD_X_CHECKER.val2proto(x)
    proto._y_spd = util.CHASSIS_SPD_Y_CHECKER.val2proto(y)
    proto._z_spd = util.CHASSIS_SPD_Z_CHECKER.val2proto(z)
    
    logger.info("x_spd:{0:f}, y_spd:{1:f}, z_spd:{2:f}".format(proto._x_spd, proto._y_spd, proto._z_spd))

    return user_watcher.DRIVE_SPEED_ADJUSTER.register_proto(self, proto,timeout)


def md_move(self, x=0, y=0, z=0, xy_speed=0.5, z_speed=30):
    """ 修改后的move
    """
    action = SafeChassisMoveAction(self, x, y, z, xy_speed, z_speed)
    return action

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

offical.ChassisMoveAction._encode_json = _encode_json

