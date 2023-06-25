from robot import  Robot


class Gimbal:
    def __init__(self,robot:Robot):
        self._robot = robot

    def moveto(self, pitch=0, yaw=0, pitch_speed=30, yaw_speed=30):
        cmd = f'IN: gimbal moveto p {pitch} y {yaw} vp {pitch_speed} vy {yaw_speed};'
        self._robot.helper.put_msg(cmd)
