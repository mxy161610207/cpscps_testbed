import json
class SensorAdapter:
    def __init__(self, robot=None):
        self._distance = None
        self._angle=0.0
        self._watch_action = -1

    def register_action(self,action):
        self._watch_action = action._action_id
        print(f'mxy Log: register_action id = {self._watch_action}')

    def sub_distance(self, freq=5, callback=None, *args, **kw):
        distance_logger = kw.get('distance_logger',None)
        self._distance = distance_logger

        return True

    def unsub_distance(self):
        self._distance = None

    def update(self,msg:str):
        info_json = json.loads(msg)