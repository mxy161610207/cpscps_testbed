from . import sdk_handler

class PlatformException(Exception):
    def __init__(self, msg):
        self.msg = msg
        self.platform_error_handle()
    
    def platform_error_handle(self):
        if sdk_handler.CAR_HANDLER.has_active_car:
            sdk_handler.CAR_HANDLER._robomaster_ep.close()

    def __str__(self):
        return str(self.msg)