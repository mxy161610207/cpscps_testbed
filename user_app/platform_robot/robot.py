from platform_robot import chassis
from platform_robot import sensor_adapter
from platform_robot import java_communication_helper

# mode, copied from robomaster.robot
FREE = "free"
GIMBAL_LEAD = "gimbal_lead"
CHASSIS_LEAD = "chassis_lead"

class Robot:
    def __init__(self):
        # flag for identifying platform robot
        self.is_platform = None

        self._chassis = chassis.Chassis(self)
        self._sensor_adapter = sensor_adapter.SensorAdapter(self)

        self.helper = java_communication_helper.JavaCommunicationHelper(self._sensor_adapter)

    def __del__(self):
        self.helper.put_msg("EXIT")

    def initialize(self, **kwargs):
        return True

    @property
    def chassis(self):
        return self._chassis

    @property
    def sensor(self):
        return self._sensor_adapter
    
    def is_register_action(self,action_id):
        return self._sensor_adapter._watch_action == action_id