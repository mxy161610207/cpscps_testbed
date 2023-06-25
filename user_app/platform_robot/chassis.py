import time

from robot import Robot


class Chassis:
    def __init__(self, robot:Robot):
        self._robot = robot

    def drive_speed(self, x=0.0, y=0.0, z=0.0, timeout=None):
        cmd = f'IN: chassis speed x {x} y {y} z {z};'
        self._robot.helper.put_msg(cmd)
        if timeout is not None:
            time.sleep(timeout)
            cmd = f'IN: chassis speed x 0 y 0 z 0;'
            self._robot.helper.put_msg(cmd)