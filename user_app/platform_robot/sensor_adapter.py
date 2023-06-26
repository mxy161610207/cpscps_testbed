import json
import time
class SensorAdapter:
    def __init__(self, robot=None):
        self._distance = None
        self._distance_logger_tag = False
        self._angle=0.0
        self._chassis_status = 0

    def sub_distance(self, freq=5, callback=None, distance_logger = None, *args, **kw):
        # print("GEET",distance_logger)
        self._distance = distance_logger
        self._distance_logger_tag = True
        print("[DRIVER] distance_logger register")
        time.sleep(1)

        return True

    def unsub_distance(self):
        self._distance = None
        self._distance_logger_tag = False

    def update(self,msg:str):
        info_json = json.loads(msg)
        
        # print("*****",self._distance)
        if 'ir_distance' in info_json and self._distance is not None:
            if (self._distance_logger_tag): 
                print("[DRIVER] distance_logger load data...")
                self._distance_logger_tag = False
            for key in self._distance:
                self._distance[key] = info_json['ir_distance'][key]
        
        if 'chassis_status' in info_json:
            next_status= info_json['chassis_status']
            if (next_status!=self._chassis_status):
                # print(f'[chassis_status]switch {self._chassis_status} to {next_status}, msg={msg}')
                self._chassis_status=next_status
