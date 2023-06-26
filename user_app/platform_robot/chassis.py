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
        # 该动作生成
        cmd = f'SAFE: chassis move x {self._x} y {self._y} z {self._z} vxy {self._spd_xy} vz {self._spd_z} timeout {-1 if timeout is None else timeout} uuid {self._action_id};'
        
        # 发送
        self._robot.helper.put_msg(cmd)

        # 等待注册成功
        while not self._robot.chassis._chassis_action_is_running:
            pass
        print("Action is running")
        # 等待驱动完成
        while not self._robot.chassis._chassis_action_empty:
            pass
        
        print("Action END")
        return True

class Chassis:
    def __init__(self, robot):
        self._robot = robot

    def drive_speed(self, x=0.0, y=0.0, z=0.0, timeout=None):
        if (not self._chassis_action_empty):
            raise Exception(f'mxy: reject drive_speed x {x} y {y} z {z}')
        cmd = f'SAFE: chassis speed x {x} y {y} z {z} timeout {-1 if timeout is None else timeout};'
        self._robot.helper.put_msg(cmd)

    def move(self, x=0, y=0, z=0, xy_speed=0.5, z_speed=30):
        if (not self._chassis_action_empty):
            raise Exception(f'mxy: reject move x {x} y {y} z {z} vxy {xy_speed} vz {z_speed} ')
        
        action = ChassisMoveAction(x, y, z, xy_speed, z_speed, self._robot)
        return action
    

    @property
    def _chassis_action_empty(self):
        return self._robot._sensor_adapter._chassis_status == 1 or self._robot._sensor_adapter._chassis_status == 0

    @property
    def _chassis_action_is_running(self):
        return self._robot._sensor_adapter._chassis_status == 2
