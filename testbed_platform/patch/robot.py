import robomaster.robot as offical
from robomaster.robot import *

from robomaster import config
from robomaster import logger
from robomaster import client
from robomaster import action
from robomaster import conn

from module import sdk_handler
from module.platform_exception import PlatformException

"""
class Robot(robot.RobotBase):
"""
def md_initialize(self, conn_type=config.DEFAULT_CONN_TYPE, proto_type=config.DEFAULT_PROTO_TYPE, sn=None):
    """ 修改后的initialize

    :param conn_type: 连接建立类型: ap表示使用热点直连；sta表示使用组网连接，rndis表示使用USB连接
    :param proto_type: 通讯方式: tcp, udp

    注意：如需修改默认连接方式，可在conf.py中指定DEFAULT_CONN_TYPE
    """
    print("[SDK] __call__ 修改后的initialize")

    try:
        self._dij_initialize(conn_type, proto_type, sn)
    except Exception as e:
        print(e)
        print("[platform] DJI SDK的initialize 运行失败!")
        return False
    
    """ 
    默认以最大频率开启所有订阅 mxy_edit

    _dis_sensor: 距离传感器
    _camera: 相机

    """
    sdk_handler.PHY_SENDER.set_online()
    sdk_handler.PHY_SENDER.sys_add_sub_module(self.sensor)
    sdk_handler.PHY_SENDER.sys_add_sub_module(self.gimbal)
    # sdk_handler.PHY_SENDER.sys_add_sub_module(self.chassis)
    sdk_handler.PHY_SENDER.sys_sub_all()

    # """ 
    # 小车在矩形场地中进行同步 mxy_edit
    # """
    # sdk_handler.physical_platform_initialize(self)

    print("[SDK] __success__ 修改后的initialize")
    return True

def md_close(self):
        """ 修改后的close
        关闭所有系统订阅 mxy_edit
        sys_unsub_all
        """
        sdk_handler.PHY_SENDER.sys_unsub_all()

        self._ftp.stop()
        if self._initialized:
            self._enable_sdk(0)
            self._stop_heart_beat_timer()
        for name in list(self._modules.keys()):
            if self._modules[name]:
                self._modules[name].stop()
        if self.client:
            self._client.stop()
        if self._sdk_conn:
            self._sdk_conn.close()
        self._initialized = False
        logger.info("Robot close")
        print("修改后的close")


# modify list

offical.Robot._dij_initialize = offical.Robot.initialize

offical.Robot.initialize = md_initialize
offical.Robot.close = md_close