import json

from robot import Robot


class ReadingsProxy:
    def __init__(self,robot:Robot):
        self._robot = robot

    def __getattr__(self, item):
        # Notice: this cmd is not compliant with DJI text protocol
        cmd = f'IN: sensor_readings?;'
        self._robot.helper.put_msg(cmd)
        readings = json.loads(self._robot.helper.get_msg())
        return readings[item]

