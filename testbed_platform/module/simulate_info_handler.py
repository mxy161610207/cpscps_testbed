class SimulateMsg(SensorSourceHandler):
    def __init__(self):
        super(SimulateMsg,self).__init__(port=,tag="Sim")
    
    '''
    explore for different action API:
        format: "? action [action_api] *args"
    
    1) move
        ? action move {x} {y} {z} {xy_spd} {z_spd}
    2) drive_speed #TODO
        ? action drive_speed {x_spd} {y_spd} {z_spd}
    '''
    def handle_query_reply(self,reply_data):
        reply_data = eval(reply_data)
        # print("SIM:",reply_data)
        F,B,L,R,time_tag,t = reply_data
        self.set_sensor_data_info([F,R,B,L])
        if (time_tag):
            time_gap = time.time()-t
            if (time_gap > 0.15): 
                s = "\ncycle: {:.6f}".format(time_gap)
                # warnings.warn(s,UserWarning)
