# this module help calc data

import queue
import threading
import time

from . import location_list
from .location_config import SystemState

class LocationCalculater:
    def __init__(self,server):
        print("__init__ LocationCalculater start")
        self.system_state=SystemState.INIT

        self.info_queue = queue.Queue(-1) # recv json format
        self.query_queue = queue.Queue(-1)

        self.sensor_lock = threading.Lock()
        self.sensor_info = queue.Queue(5)

        self.server = server
        self.bind_map = None

        self.location_grd = location_list.LocationList(200,name='Guard',need_sim_pair=True)
        self.location_sim = self.location_grd._sim_pair

        print("self.location_grd size =",self.location_grd.size)
        print("self.location_sim size =",self.location_sim.size)

        self.update_lock = threading.Lock()
        self.need_recover = False


        self.location_log = queue.Queue(2000)

        # self.updata_thread stop with server's recv_thread stop
        self.update_thread=threading.Thread(target=self._location_update,args=())
        self.update_thread.daemon = True 
        self.update_thread.start()

        self.start_timer = False
        self.time_list = {"send":-1,"calc":-1,"sim":-1}

        print("__init__ LocationCalculater end")


    def _location_update(self):
        while True:
            recv_json = self.info_queue.get()
           
            self.system_update(recv_json)
            
            #todo if has simulate map update

            # if (self.start_timer):
            #     if (self.time_list["calc"]>0):
            #         self.time_list["sim"] = time.time()
            #         self._print_delay()
            #         self.start_timer = False
                
            if (self.server.is_shutdown()):break
            # print(1)
            # time.sleep(2)
        # print('end')
    
    def _print_delay(self):
        a,b,c = self.time_list['send'],self.time_list['calc'],self.time_list['sim']
        if (c-a > 0.2): 
            s = "delay: {:.6f} {}".format(c-a,self.time_list)
            # warnings.warn(s,UserWarning)
        print("delay\n"*10)
        print(self.time_list)
        print(b-a,c-b,c-a)
    
    def bind_map_update(self):
        if self.bind_map:
            sim_irs_pos = self.location_sim.current_postion
            self.bind_map.update(sim_irs_pos.dict_style,self.start_timer,self.time_list["send"])

    def switch_system_state(self,next_state:SystemState):
        if next_state==SystemState.ADJUST:
            if (self.state!=SystemState.NORMAL and self.state!=SystemState.ADJUST):
                raise Exception("{} cannot convert to {}".format(self.state,next_state))
        elif next_state==SystemState.NORMAL:
            if (self.state!=SystemState.ADJUST and self.state!=SystemState.INIT):
                raise Exception("{} cannot convert to {}".format(self.state,next_state))
        elif next_state == SystemState.INIT:
            self.location_grd.reset()
            if (self.location_sim): self.location_sim.reset()

        self.state = next_state

    def get_sensor_group(self):
        sensor_data = [0,0,0,0]

        response_ids = []
        group_cnt=0

        while(not self.sensor_info.empty()):
            distance,need_location,term_id = self.sensor_info.get()
            group_cnt+=1
            
            for i in range(4):
                sensor_data[i] += distance[i]

            if need_location: response_ids.append(term_id)
        
        for i in range(4):
            sensor_data[i]/=group_cnt

        return sensor_data,response_ids

    def system_update(self, recv_json):
        term_id = recv_json['term_id']
        data_type = recv_json['type']
        info = recv_json['info']
        
        if data_type == "SYSTEM_TYPE":
            self.handle_system_data(info)
            return 

        elif data_type == "SENSOR_TYPE":
            # 1) get 4 sensor
            sensor_info = [int(x) for x in info['sensor_info']]
            # 2) if has tag
            need_location = info['need_location']
            # 3) get send timestamp
            send_time = recv_json['time']

            if (need_location):
                print("[SNAPSHOT] need location_grd\n"*10)         

            if (not self.start_timer and self.sensor_info.empty()):  
                self.start_timer = True
                for k in self.time_list:
                    self.time_list[k] = -1
                self.time_list["send"] = send_time

            # 4) append sensor recv_json, if full advance once
            self.sensor_lock.acquire()

            self.sensor_info.put([sensor_info,need_location,term_id])
            if (self.sensor_info.full()):
                sensor_data,respond_ids = self.get_sensor_group()
                msg = []

                self.location_grd.advance_once(sensor_data,msg)

                if (self.start_timer):
                    self.time_list["calc"] = time.time()
            
                if (self.location_grd.is_unmovable):
                    while (not self.query_queue.empty()):
                        qid = self.query_queue.get()
                        self.make_unmovable_reply(qid)

                for rid in respond_ids:
                    self.make_snapshot_reply(rid)

            self.sensor_lock.release()

            #5) if has tag, should apply a msg "SYSTEM_TYPE,ADJUST,on"
            if need_location:
                self.switch_system_state(SystemState.ADJUST)
            return
            
        elif data_type == "ACTION_TYPE":
            self.handle_action_data(info)
            return 

        elif data_type == "ANGLE_TYPE":
            self.handle_angle_data(info)
            return 

        elif data_type == "QUERY":
            print("[QUERY] need location_grd\n"*10)
            # TODO set an threading reply by the first unmovable
            query_type = info['query_type']
            if (query_type=='position'):
                self.query_queue.put(term_id)
            elif (query_type=='system_state'):
                pass
            else:
                raise Exception("unknown query {}".format(recv_json))

        elif data_type == "EOF":
            print("shutdown")
            self.server._shutdown = True
            return 

        else:
            # unknown legal type
            raise Exception("Unknown data type {}".format(recv_json))


    def handle_action_data(self,info):
        self.location_grd.set_action(info)
        pass

    def handle_angle_data(self,info):
        angle=info['angle']
        raw_angle=info['raw_angle']
        self.location_grd.set_sdk_angle(angle)
        self.location_grd.set_raw_sdk_angle(raw_angle)

    def handle_system_data(self,info):
        self.switch_system_state(SystemState[info['next_state']])

    def make_unmovable_reply(self,qid):
        assert(self.location_grd.is_unmovable)
        pos = self.location_grd.current_postion
        reply_json = {
            'query_id': qid,
            'type': 'position',
            'info': {
                'location_analysis': self.location_grd.location_analysis.name,
                'x': pos.x,
                'y': pos.y,
                'deg': pos.deg
            }
        }
        # print("reply_json",reply_json)
        self.server._send_msg_queue.put(reply_json)

    def make_snapshot_reply(self,qid):
        # assert(self.location_grd.is_unmovable)
        pos = self.location_grd.current_postion
        reply_json = {
            'query_id': qid,
            'type': 'snapshot',
            'info': {
                'location_analysis': self.location_grd.location_analysis.name,
                'x': pos.x,
                'y': pos.y,
                'deg': pos.deg
            }
        }
        self.server._send_msg_queue.put(reply_json)


