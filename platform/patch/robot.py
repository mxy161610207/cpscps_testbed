import robomaster.robot as offical
from robomaster.robot import *

from robomaster import config
from robomaster import logger
from robomaster import client
from robomaster import action
from robomaster import conn

import user_watcher

"""
class Robot(robot.RobotBase):
"""
def md_initialize(self, conn_type=config.DEFAULT_CONN_TYPE, proto_type=config.DEFAULT_PROTO_TYPE, sn=None):
    """ 修改后的initialize

    :param conn_type: 连接建立类型: ap表示使用热点直连；sta表示使用组网连接，rndis表示使用USB连接
    :param proto_type: 通讯方式: tcp, udp

    注意：如需修改默认连接方式，可在conf.py中指定DEFAULT_CONN_TYPE
    """
    print("修改后的initialize")
    self._proto_type = proto_type
    self._conn_type = conn_type
    if not self._client:
        logger.info("Robot: try to connection robot.")
        conn1 = self._wait_for_connection(conn_type, proto_type, sn)
        if conn1:
            logger.info("Robot: initialized with {0}".format(conn1))
            self._client = client.Client(9, 6, conn1)
        else:
            logger.info("Robot: initialized, try to use default Client.")
            try:
                self._client = client.Client(9, 6)
            except Exception as e:
                logger.error("Robot: initialized, can not create client, return, exception {0}".format(e))
                return False

    try:
        self._client.start()
    except Exception as e:
        logger.error("Robot: Connection Create Failed.")
        raise e

    self._action_dispatcher = action.ActionDispatcher(self.client)
    self._action_dispatcher.initialize()
    # Reset Robot, Init Robot Mode.
    self._scan_modules()

    # set sdk mode and reset
    self._enable_sdk(1)
    self.reset()

    self._ftp.connect(self.ip)

    # start heart beat timer
    self._running = True
    self._start_heart_beat_timer()
    self._initialized = True

    """ 
    默认以最大频率开启所有订阅 mxy_edit

    _dis_sensor: 距离传感器
    _camera: 相机

    """
    user_watcher.PHY_SENDER.set_online()
    user_watcher.PHY_SENDER.sys_add_sub_module(self.sensor)
    user_watcher.PHY_SENDER.sys_add_sub_module(self.gimbal)
    user_watcher.PHY_SENDER.sys_sub_all()

    # """ 
    # 小车在矩形场地中进行同步 mxy_edit
    # """
    # user_watcher.physical_platform_initialize(self)

    return True

def md_close(self):
        """ 修改后的close
        关闭所有系统订阅 mxy_edit
        sys_unsub_all
        """
        user_watcher.PHY_SENDER.sys_unsub_all()

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
offical.Robot.initialize = md_initialize
offical.Robot.close = md_close