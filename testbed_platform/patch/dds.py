import robomaster.dds as offical
from robomaster.dds import *

"""
class Subject(metaclass=offical._AutoRegisterSubject)
修改了相关函数 

set_usr_sub 在sys_sub上新增用户订阅
set_usr_unsub 在sys_sub上删除用户订阅

exec 默认执行sys_sub的callback, 当计时器到usr_sub执行时，执行usr的callback
"""
def __md_init__(self):
    self._task = None
    self._subject_id = 1
    self._callback = None
    self._cb_args = None
    self._cb_kw = None
    
    '''
    new add for sys sub
    '''
    self._usr_sub = False
    self._usr_loop = 0
    self._usr_callback = None
    self._usr_cb_args = None
    self._usr_cb_kw = None
    self._usr_term_id = 0

def md_exec(self):
    # print("has usr:",self._usr_sub)
    self._callback(self.data_info(), *self._cb_args, **self._cb_kw)
    # print("Try usr")
    if self._usr_sub:
        self._usr_term_id = self._usr_term_id+1
        # print("term_id = {}".format(self._usr_term_id))
        if (self._usr_term_id == self._usr_loop):
            self._usr_term_id = 0
            
            self._usr_callback(self.usr_data_info(),*self._usr_cb_args,**self._usr_cb_kw)

def set_usr_sub(self,usr_loop, usr_callback, usr_args, usr_kw):
    self._usr_sub = True
    self._usr_loop = usr_loop
    self._usr_callback = usr_callback
    self._usr_cb_args = usr_args
    self._usr_cb_kw = usr_kw

    self._usr_term_id = 0
    # self._usr_callback(self.usr_data_info(),*self._usr_cb_args,**self._usr_cb_kw)
    return True

def set_usr_unsub(self):
    self._usr_sub = False
    self._usr_term_id = 0
    return True

@abstractmethod
def usr_data_info(self):
    return None

# modify list
offical.Subject.__init__ = __md_init__
offical.Subject.exec = md_exec

offical.Subject.set_usr_sub = set_usr_sub
offical.Subject.set_usr_unsub = set_usr_unsub
offical.Subject.usr_data_info = usr_data_info

