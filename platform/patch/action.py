import robomaster.action as offical
from robomaster.action import *
from robomaster.chassis import ChassisMoveAction

from module import sdk_handler

'''
class ActionDispatcher(object):
'''
def md_send_action(self, action, action_type=offical.ACTION_NOW):
        """ 发送任务动作命令 """
        action._action_id = action._get_next_action_id()

        if self.has_in_progress_actions:
            self._in_progress_mutex.acquire()
            for k in self._in_progress:
                act = self._in_progress[k]
                if action.target == act.target:
                    action = list(self._in_progress.values())[0]
                    offical.logger.error("Robot is already performing {0} action(s) {1}".format(len(self._in_progress), action))
                    print("mxy_edit: apply ",action._encode_json,"now")
                    raise Exception("Robot is already performing {0} action(s) {1}".format(
                        len(self._in_progress), action))
            self._in_progress_mutex.release()
        if action.is_running:
            raise Exception("Action is already running")

        action_msg = self.get_msg_by_action(action)
        action_key = action.make_action_key()
        self._in_progress[action_key] = action
        self._client.add_handler(self, "ActionDispatcher", self._on_recv)
        action._obj = self
        action._on_state_changed = self._on_action_state_changed

        '''mxy_edit
        此处修改，如果是ChassisMoveAction类型的程序，
        向Loction_server发送运行信息
        '''
        if isinstance(action, ChassisMoveAction):
            sdk_handler.PHY_SENDER.send_action_info(action._encode_json)
        '''edit end
        '''

        self._client.send_msg(action_msg)
        if isinstance(action, offical.TextAction):
            action._changeto_state(ACTION_STARTED)
        offical.logger.info("ActionDispatcher: send_action, action:{0}".format(action))


# modify list
offical.ActionDispatcher.send_action = md_send_action