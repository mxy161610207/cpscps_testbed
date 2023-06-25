import json
class SensorAdapter:
    def __init__(self, robot=None):
        self._distance = None
        self._angle=0.0
        self._watch_action = -1

    def sub_distance(self, freq=5, callback=None, *args, **kw):
        distance_logger = kw.get('distance_logger',None)
        self._distance = distance_logger

        return True

    def unsub_distance(self):
        self._distance = None

    def update(self,msg:str):
        info_json = json.loads(msg)
        
        if 'ir_distance' in info_json and self._distance is not None:
            for key in self._distance:
                self._distance[key] = info_json['ir_distance'][key]
        
        if 'chassis_action_id' in info_json:
            id = info_json['chassis_action_id']
            if id==-1:
                self._watch_action=None
            else:
                self._watch_action=id