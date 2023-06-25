import chassis
import gimbal
import java_communication_helper
import readings_proxy

# mode, copied from robomaster.robot
FREE = "free"
GIMBAL_LEAD = "gimbal_lead"
CHASSIS_LEAD = "chassis_lead"


class Robot:
    def __init__(self):
        # flag for identifying platform robot
        self.is_platform = None
        self._gimbal = gimbal.Gimbal(self)
        self._chassis = chassis.Chassis(self)
        self._readings_proxy = readings_proxy.ReadingsProxy(self)
        self.helper = java_communication_helper.JavaCommunicationHelper()

    def initialize(self, **kwargs):
        pass

    def set_robot_mode(self, mode):
        cmd = f'IN robot mode {mode};'
        self.helper.put_msg(cmd)

    @property
    def gimbal(self):
        return self._gimbal

    @property
    def readings_proxy(self):
        return self._readings_proxy
