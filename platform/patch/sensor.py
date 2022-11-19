import robomaster.sensor as offical
from robomaster.sensor import *

from robomaster import dds

from module import sdk_handler

'''
class TofSubject(dds.Subject):
'''
def usr_data_info(self):
    """ mxy_edit
    实现了虚函数 usr_data_info
    usr_data_info 根据虚拟端在线情况，返回真实值or虚拟值
    """
    return sdk_handler.SIMULATE_MSG._distance
#     print("usr_info",platform.SIMULATE_MSG._distance)
#     if platform.is_online():    
#         # print("usr_info",platform.SIMULATE_MSG._distance)
#         return platform.SIMULATE_MSG._distance
#     else:
#         return platform.PHYSICAL_MSG._distance

'''
class DistanceSensor(module.Module):
'''
def sys_sub_handler(self, sub_info):
        """ mxy_edit
        真实距离传感器 sys_sub 的callback函数
        将真实测距值发送给server
        """
        # print("[- Phy] tof1:{0}  tof2:{1}  tof3:{2}  tof4:{3}".
        #       format(sub_info[0], sub_info[1], sub_info[2], sub_info[3]))
        sdk_handler.PHY_SENDER.set_sensor_data_info(sub_info)
        pass

def sys_sub(self, *args, **kw):
        """ mxy_edit
        订阅真实距离传感器测量的距离信息 
        在robot.initialize中被首次使用

        :param freq: 订阅数据的频率，支持的订阅频率为1、5、10、20、50hz
        :param callback: 传入数据处理的回调函数，回调函数的参数为：

                        :distance[4]: 4个tof的距离信息

        :param args: 传入参数。
        :return: 返回订阅结果。
        """
        print("开启platfrom订阅: sensor")
        sub = self._robot.dds
        subject = offical.TofSubject()
        self._max_freq = 50
        subject.freq = self._max_freq
        callback = self.sys_sub_handler

        self._subject = subject
        
        return sub.add_subject_info(subject, callback, args, kw)

def sys_unsub(self):
        """ mxy_edit
        取消真实距离传感器的信息订阅。
        """
        sub_dds = self._robot.dds
        return sub_dds.del_subject_info(dds.DDS_TOF)

def md_sub_distance(self, freq=5, callback=None, *args, **kw):
        """ mxy_edit
        用户调用的 订阅距离传感器测量的距离信息

        原: 大疆提供的订阅接口，新增一个Subject
        改：在sys的Subject上 新增usr_sub信息
        """
        usr_loop = self._max_freq // freq
        return self._subject.set_usr_sub(usr_loop,callback,args,kw)

def md_unsub_distance(self):
        """ mxy_edit
        用户调用的 取消距离传感器的信息订阅。
        """
        return self._subject.set_usr_unsub()

# modify list
offical.TofSubject.usr_data_info = usr_data_info

offical.DistanceSensor.sys_sub_handler = sys_sub_handler
offical.DistanceSensor.sys_sub = sys_sub
offical.DistanceSensor.sys_unsub = sys_unsub

offical.DistanceSensor.sub_distance = md_sub_distance
offical.DistanceSensor.unsub_distance = md_unsub_distance

