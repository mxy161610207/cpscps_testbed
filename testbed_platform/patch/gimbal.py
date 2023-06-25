import robomaster.gimbal as offical
from robomaster.gimbal import *

from robomaster import dds
from module import sdk_handler

'''
class GimbalPosSubject(dds.Subject):
'''
def usr_data_info(self):
    """ mxy_edit
    实现了虚函数 usr_data_info
    usr_data_info 根据虚拟端在线情况，返回真实值or虚拟值
    """
    data_source = None
    return sdk_handler.SIMULATE_MSG.get_angle()
#     if platform.is_online():
#         data_source =  platform.SIMULATE_MSG
#     else:
#         data_source =  platform.PHYSICAL_MSG
    
#     return data_source._pitch_angle, data_source._yaw_angle, data_source._pitch_ground_angle, data_source._yaw_ground_angle

'''
class Gimbal(module.Module):
'''
def sys_sub_handler(self, sub_info):
        """ mxy_edit
        真实角度传感器 sys_sub 的callback函数
        将真实测距值发送给server
        """
        sdk_handler.PHY_SENDER.set_angle_data_info(sub_info)
        pass

def sys_sub(self, *args, **kw):
        """ mxy_edit
        订阅云台姿态角信息 
        在robot.initialize中被首次使用

        :param freq: 订阅数据的频率，支持的订阅频率为1、5、10、20、50hz
        :param callback: 传入数据处理的回调函数，回调函数的参数为：

                        :pitch_angle: 相对底盘的pitch轴角度
                        :yaw_angle: 相对底盘的yaw轴角度
                        :pitch_ground_angle: 上电时刻pitch轴角度
                        :yaw_ground_angle: 上电时刻yaw轴角度
       

        :param args: 传入参数
        :param kw: 关键字参数
        :return:  bool: 数据订阅结果
        """
        print("开启platfrom订阅: gimbal")
        
        sub = self._robot.dds
        subject = offical.GimbalPosSubject()
        self._max_freq = 10
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

def md_sub_angle(self, freq=5, callback=None, *args, **kw):
        """ mxy_edit
        用户调用的 订阅云台姿态角信息

        原: 大疆提供的订阅接口，新增一个Subject
        改：在sys的Subject上 新增usr_sub信息
        """
        usr_loop = self._max_freq // freq
        return self._subject.set_usr_sub(usr_loop,callback,args,kw)

def md_unsub_angle(self):
        """ mxy_edit
        用户调用的 取消距离传感器的信息订阅。
        """
        return self._subject.set_usr_unsub()

# modify list
offical.GimbalPosSubject.usr_data_info = usr_data_info

offical.Gimbal.sys_sub_handler = sys_sub_handler
offical.Gimbal.sys_sub = sys_sub
offical.Gimbal.sys_unsub = sys_unsub

offical.Gimbal.sub_angle = md_sub_angle
offical.Gimbal.unsub_angle = md_unsub_angle

