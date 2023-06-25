import threading

class ChassisMoveAction():
    _action_id_counter=0

    def __init__(self, x=0, y=0, z=0, spd_xy=0, spd_z=0, robot=None):
        self._x = x
        self._y = y
        self._z = z
        self._spd_xy = spd_xy
        self._spd_z = spd_z

        self._robot = robot

        self._action_id = self._action_id_counter+1
        self._action_id_counter+=1

        self._event = threading.Event()
        self._event.clear()

    def wait_for_completed(self, timeout=None):
        # 该动作运行，注册
        self._robot._sensor_adapter.register_action(self)

        cmd = f'SAFE: chassis move x {self._x} y {self._y} z{self._z} vxy {self._spd_xy} vz{self._spd_z} timeout {-1 if timeout is None else timeout};'
        self._robot.helper.put_msg(cmd)

        # 等待驱动完成
        self._event.wait()
        return True

class Chassis:
    def __init__(self, robot):
        self._robot = robot

    def drive_speed(self, x=0.0, y=0.0, z=0.0, timeout=None):
        if (not self._chassis_current_action_id):
            raise Exception(f'mxy: reject drive_speed, action id = {self._chassis_current_action_id} is running')
        cmd = f'SAFE: chassis speed x {x} y {y} z {z} timeout {-1 if timeout is None else timeout};'
        self._robot.helper.put_msg(cmd)

    def move(self, x=0, y=0, z=0, xy_speed=0.5, z_speed=30):
        if (not self._chassis_current_action_id):
            raise Exception(f'mxy: reject move, action id = {self._chassis_current_action_id} is running')
        
        action = ChassisMoveAction(x, y, z, xy_speed, z_speed)
        return action
    

    @property
    def _chassis_action_empty(self):
        return self._robot._sensor_adapter._watch_action == -1

    @property
    def _chassis_current_action_id(self):
        return self._robot._sensor_adapter._watch_action