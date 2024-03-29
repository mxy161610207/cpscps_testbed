from threading import Lock,Thread,Event
import time

from . import sdk_handler

# 系统平台切换、计时器同步
# 一些计时器可能涉及adjust状态，需要设置时间补偿
class PlatformTimerManager():
    def __init__(self,car_handler):
        self._car_handler = car_handler
        self.register_timer = []
        # self.queue_lock = threading.Lock()
        self.start_time = None
        self.adjust_lock = Lock()

        self.total_adjust_time = 0
        self.total_run_start_time = 0
        self.adjust_count = 0

    def timer_register(self,timer):
        self.register_timer.append(timer)

    def timer_delete(self,timer):
        self.register_timer.remove(timer)

    def adjust_status_start(self):
        if not self.adjust_lock.acquire(blocking=False):
            print("[sdk] already in adjust_mode")
            return False
            
        print("[sdk] >>> ENTER adjust_mode")
        self.start_time = time.time()

        # into adjust status
        self._car_handler.led_behavior(state="adjust")

        for timer in self.register_timer:
            print(timer)
            timer.interval_lock.acquire()
        
        return True
    
    def adjust_status_end(self):
        pos = self._car_handler.query_phy_position()
        print("after adjust pos = {:.3f} {:.3f} deg = {:.3f}".format(pos['x'],pos['y'],pos['deg']))

        # exit adjust status
        self._car_handler.send_adjust_status(is_on=False)
        self._car_handler.led_behavior(state="normal")

        interval_append = time.time() - self.start_time
        self.total_adjust_time += interval_append
        
        print("append time {:.3f}s".format(interval_append))
        for timer in self.register_timer:
            timer.append(interval_append)
            
        for timer in self.register_timer:
            timer.interval_lock.release()

        self.adjust_lock.release()
        print("[sdk] <<< EXIT adjust_mode")

    def reset_timer(self):
        self.total_adjust_time = 0
        self.total_run_start_time = time.time()
        self.adjust_count = 0

    def print_timer(self):
        end_time = time.time()
        with open("timer_logger_{}.txt".format(int(end_time)),"w") as f:
            t_all = end_time - self.total_run_start_time
            print("Total time: {}".format(t_all))
            print("Adjust time: {}".format(self.total_adjust_time))
            print("Adjust count: {}".format(self.adjust_count))

            print("Total time: {}".format(t_all),file=f)
            print("Adjust time: {}".format(self.total_adjust_time),file=f)
            print("Adjust count: {}".format(self.adjust_count),file=f)
            print("Percent = {}".format(self.total_adjust_time/float(t_all)), file=f)


class PlatformTimer(Thread):
    def __init__(self, interval, function, args=None, kwargs=None):
        Thread.__init__(self)
        self.interval = interval
        self.interval_lock = Lock()

        self.total_interval = interval
        self.start_time = time.time()


        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.finished = Event()

        sdk_handler.TIME_MANAGER.timer_register(self)

    def cancel(self):
        """Stop the timer if it hasn't finished yet."""
        self.finished.set()
        sdk_handler.TIME_MANAGER.timer_delete(self)
        
    def get(self):
        self.interval_lock.acquire()
        tmp = self.interval
        self.interval = 0
        self.interval_lock.release()
        return tmp

    def append(self,append_interval):
        self.interval+=append_interval
        self.total_interval += append_interval

    def get_left(self):
        spend_time = time.time()-self.start_time
        return min(0,self.total_interval-spend_time)

    def run(self):
        while True:
            wait_time = self.get()
            if wait_time == 0: break

            self.finished.wait(wait_time)
            print("get & wait =",wait_time)
            if (self.finished.is_set()):break

        if not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
        self.finished.set()
        sdk_handler.TIME_MANAGER.timer_delete(self)
