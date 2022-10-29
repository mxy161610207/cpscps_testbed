import user_watcher
class PlatformException(Exception):
    def __init__(self, msg):
        self.msg = msg
        self.platform_error_handle()
    
    def platform_error_handle(self):
        if user_watcher.CAR_HANDLER.has_active_car:
            user_watcher.CAR_HANDLER._robomaster_ep.close()

    def __str__(self):
        return str(self.msg)