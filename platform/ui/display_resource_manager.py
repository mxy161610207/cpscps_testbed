class DispalyResourceManager():
    def __init__(self) -> None:
        self._location_server = None
        # self._button_ui_lock=threading.Lock()
    
    # declare current location_server is on service
    def register_location_server(self, location_server):
        print("Register location_server")
        self._location_server = location_server

    # flush resources's loc_server
    # old loc_server shutdown
    # wait for manager.py raise a new loc_server
    def shutdown_location_server(self):
        tmp_server = self._location_server
        self._location_server = None
        tmp_server.set_shutdown()

    def get_display_info(self,tag):
        if (tag=='grd'):
            return self._location_server.get_grd_display_info(5)
        else:
            return self._location_server.get_sim_display_info(5)
    
    # None active location server on service now.
    # Maybe is RESETing..
    # Can't be porperty [in BaseManager]
    def location_server_empty(self):
        return self._location_server is None or self._location_server.is_shutdown()

    def has_location_server(self):
        return not self.location_server_empty()

    def reset_simulate_position(self):
        self._location_server.calculater.location_sim.reset()
        return
    
    ##### tkinter's button event processing in sequence
    ##### so no need additional lock
    # # get lock without blocking,
    # # if other button is working, just reject.
    # @property
    # def button_is_busy(self):
    #     get_lock=self._button_ui_lock.acquire(blocking=False)
    #     return get_lock
    
    # # current button working end.
    # def release_button(self):
    #     self._button_ui_lock.release()
    #     return
