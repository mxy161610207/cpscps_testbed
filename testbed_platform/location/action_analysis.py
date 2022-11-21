
import math

from . import position_config as pc
from .position_config import ActionState, ActionAnalysis
from .position import Position

from .location_queue import FixedSizeQueue


class MotionQueue(FixedSizeQueue):
    def __init__(self, size=3) -> None:
        super().__init__(size)

    def analysis(self,msg=None):
        if (self.is_empty): 
            # print("ActionAnalysis = EMPTY")
            return ActionAnalysis.EMPTY
        average_motion = [0,0,0]
        for mot in self._queue:
            if (msg):
                msg.append("({:.3f},{:.3f},{:.3f})".
                    format(mot[0],mot[1],mot[2]))
            for i in range(3):
                average_motion[i] += math.fabs(mot[i])

        for i in range(3):
            average_motion[i] /= self.size
        
        x,y,deg = average_motion
        dist = (x**2+y**2)**0.5
        if (msg): msg.append("dis = {:.3f}, deg = {:.3f}".format(dist,deg))
        if (dist<2.4 and deg<2):
            # print("! unmovable")
            return ActionAnalysis.UNMOVABLE
        else:
            return ActionAnalysis.NOISY

class ActionMonitor:
    def __init__(self,start_pos,action_argv) -> None:
        self._bgn_pos = start_pos
        self._end_pos = None
        self._cur_pos = self._bgn_pos

        self.action_state = ActionState.INIT
        self.action_str = str(action_argv)

        self._action_mov = False
        self._action_rot = False

        self._mov_dir_x = 0.0
        self._mov_dir_y = 0.0
        self._mov_spd = 0.5 * 500 * 0.1

        self._rot_dir = 0.0
        self._rot_deg = 60 * 0.1

        self.update_str = ""

        self._action_classify(action_argv)



    def _calc_move(self,nxt_pos):
        cur_pos = self._cur_pos
        det_x,det_y = Position.calc_location_diff(cur_pos,nxt_pos)
        det_deg = Position.calc_degree_diff(cur_pos,nxt_pos)

        return (det_x,det_y,det_deg)

    # unused
    def _consistent_score(self,motion):
        ''' 分析本次动作和先前动作的一致程度[0,1]
            - 理想动作
            - 历史动作
        '''
        det_x,det_y,det_deg = motion    
        return 1

    # unused
    def _motion_analysis(self,motion):
        ''' 分析本次动作的类型
            分析思路：
            - 静止: 位置和角度几乎不变。
            - 其他情况：相似得分 > 0.5 一致

        '''
        det_x,det_y,det_deg = motion
        det_dist = (det_x**2 +det_y**2)**0.5
        if (det_dist<1 and math.fabs(det_deg)<2):
            return ActionAnalysis.UNMOVABLE
        elif (self._consistent_score(motion)>0.5):
            return ActionAnalysis.EXPECTABLE
        else:
            return ActionAnalysis.NOISY
 
    def update_state(self,nxt_pos):
        '''
            通过两次位置的差值，判断当前动作的状态(静止/符合预期/噪声点)
            并由此更新当前ActionMonitor的状态：
            | cur_state | cur_motion_type   | nxt_state |

            | INIT      | UNMOVABLE         | INIT      |
            | INIT      | EXPECTABLE        | DOING     |
            | INIT      | NOISY             | uknown... |

            | DOING     | UNMOVABLE         | FINISH    |
            | DOING     | EXPECTABLE        | DOING     |
            | DOING     | NOISY             | uknown... |

            | FINISH    | UNMOVABLE         | FINISH    | * remove action
            | FINISH    | EXPECTABLE        | uknown... |
            | FINISH    | NOISY             | uknown... |

        '''
        self.update_str = "wait update..."
        cur_motion = self._calc_move(nxt_pos)
        cur_motion_type = self._motion_analysis(cur_motion)

        if (self.action_state==ActionState.INIT):
            if (cur_motion_type==ActionAnalysis.UNMOVABLE):
                self.action_state = ActionState.INIT
                self.update_str = "wait for action start..."
            elif (cur_motion_type==ActionAnalysis.EXPECTABLE):
                self.action_state = ActionState.DOING
                self.update_str = "start move..."
            else:
                #TODO
                pass
        
        elif (self.action_state==ActionState.DOING):
            if (cur_motion_type==ActionAnalysis.UNMOVABLE):
                self.action_state = ActionState.FINISH
                self.update_str = "move end!"
            elif (cur_motion_type==ActionAnalysis.EXPECTABLE):
                self.action_state = ActionState.DOING
                self.update_str = "keep going..."
            else:
                #TODO
                pass
        
        else:
            pass
            
        self._cur_pos = nxt_pos

    @property
    def is_empty(self):
        return self.action_state == ActionAnalysis.EMPTY

    @property
    def cur_pos(self):
        return self._cur_pos

    @property
    def is_finished(self):
        return self.action_state==ActionState.FINISH
    
    # used
    @property
    def action_state_str(self):
        if (self._cur_pos):
            x,y = ActionMonitor._after_rot_matrix(self._cur_pos.rad,self._mov_dir_x,self._mov_dir_y)
        else:
            x,y=0,0

        s = "action: {}\nstate = {}\nupdate state: {}\nstart_pos = {}\ncurrent_pos = {}\n{} {}".format(
                self.action_str,
                self.action_state,
                self.update_str,
                self._bgn_pos.pos_str,
                self._cur_pos.pos_str,
                x,y)
        return s

    # used by cand_tree
    def ideal_motition(self,msg=None):
        ''' 在action not None的时候，推测小车下一步的可能位置(静止or移动)
            base 是动作扩展的倍数，base = k 一次扩展

            motion 是三元组(x,y,deg)
            表示以当前位置为原点！！！, x y deg的偏移量。
            因此需要对当前位置使用旋转四元组，才能显示效果位置。
        '''
        if self._action_rot:
            md_deg = self._rot_deg * self._rot_dir
            return (0,0,md_deg)
        elif self._action_mov:
            md_x = self._mov_dir_x * self._mov_spd
            md_y = self._mov_dir_y * self._mov_spd
            return (md_x,md_y,0)
        
        return (0,0,0)
    
    # used
    @staticmethod
    def _after_rot_matrix(rad,dx,dy,msg=None):
        # rad = (rad - math.pi/2.0)
        if msg: msg.append("md_deg = {}".format(math.degrees(rad)))
        rot_mat = [ [math.cos(rad), -math.sin(rad)],
                    [math.sin(rad), math.cos(rad)]]
        # print("rot_mat =",rot_mat)
        # print("dx dy =",dx,dy)
        tx = rot_mat[0][0]*dx + rot_mat[0][1]*dy
        ty = rot_mat[1][0]*dx + rot_mat[1][1]*dy
        # print("tx ty =",tx,ty)

        return (tx,ty)

    # used
    @staticmethod
    def act_motion(pos,motion,msg=None,base=1):
        assert(isinstance(pos,Position))
        dx,dy,ddeg = motion

        dx*=base
        dy*=base
        ddeg*=base

        nxt_pos_dic = pos.dict_style
        if (dx!=0 or dy!=0):
            tx,ty = ActionMonitor._after_rot_matrix(pos.rad,dx,dy,msg)
            nxt_pos_dic['x']+=tx
            nxt_pos_dic['y']+=ty
        if (ddeg!=0):
            nxt_deg = Position.round_degrees(
                nxt_pos_dic['deg']+ddeg)
            nxt_pos_dic['deg'] = nxt_deg
            nxt_pos_dic['rad'] = math.radians(nxt_deg)
        
        return Position(nxt_pos_dic,is_irs_center=pos.is_irs_center)
    
    # used
    @staticmethod
    def calc_motion_between_two_pos(cur_pos,nxt_pos):
        assert(isinstance(cur_pos,Position))
        assert(isinstance(nxt_pos,Position))
        assert(cur_pos.is_irs_center == nxt_pos.is_irs_center)
        det_x,det_y = Position.calc_location_diff(cur_pos,nxt_pos)
        det_deg = Position.calc_degree_diff(cur_pos,nxt_pos)

        dx,dy = ActionMonitor._after_rot_matrix(-cur_pos.rad,det_x,det_y)
        return (dx,dy,det_deg)

        
    #TODO used
    @staticmethod
    def ideal_move(cur_pos,action,base=1):
        ''' 是否需要静态方法类还未知。。。

            在action not None的时候，推测小车下一步的执行动作(静止or移动)
            并根据API参数，生成移动时的小车位置
        '''
        assert(isinstance(cur_pos,Position))
        if (action is None):
            # 静止的时候
            tmp = cur_pos.dict_style
            nxt_pos = Position(tmp)
        else:
            assert(isinstance(action,ActionMonitor))
            motion = action.ideal_motition()
            nxt_pos = ActionMonitor.act_motion(cur_pos,motion,base)
        return nxt_pos

    # used
    def _action_classify(self,action_argv):
        ''' 针对 api,argv的分析
            eg: move,x,y,z,xy_spd,z_spd 
            
            需要分析的结果：
            动作状态(方向)
            - 旋转动作: self._rot_dir, 
            - 平移动作: self._mov_dir_x,self._mov_dir_y,
            动作距离:
                self._rot_deg
                self._mov_spd
        '''
        self.action_api = action_argv['api']
        if (self.action_api=='move'):
            self._x,self._y,self._z,self._xy_spd,self._z_spd = action_argv['x'],action_argv['y'],action_argv['z'],action_argv['spd_xy'],action_argv['spd_z']

            if (self._x==0 and self._y==0 and self._z==0):
                self.action_state = ActionAnalysis.EMPTY
                return 
                
            if (self._x!=0 or self._y!=0):
                self._action_mov = True
                self._mov_dir_x,self._mov_dir_y = self._normalize_vector(self._x,-self._y)
                self._mov_spd = self._xy_spd * 500 * 0.1
            
            if (self._z!=0):
                self._action_rot = True
                # z>0 L Z<0 R
                self._rot_dir = 1.0 if self._z<0 else -1.0
                self._rot_deg = self._z_spd * 0.1
        return 

    def _normalize_vector(self,x,y):
        l = (x**2 + y**2)**0.5
        return (x/l,y/l)

    def explore(self):
        motion = (self._x,self._y,self._z)
        nxt_pos = ActionMonitor.act_motion(self._bgn_pos,motion)
        range_check = True 
        if (not nxt_pos.xy_in_range):
            range_check = False

        condition = [0,0,0,0]
        
        return range_check,condition

    @staticmethod
    def get_action_state(action,motion):
        if (action is None):
            return ActionAnalysis.EMPTY
        
        assert(isinstance(action,ActionMonitor))
        action._motion_analysis(motion)


    # def _action_classify(self,action:str):
    #     ''' 简化版的动作分析，只针对WASD,之后action str 会复杂\n
            
    #         需要分析的结果：
    #         动作状态(方向)
    #         - 旋转动作: self._rot_dir, 
    #         - 平移动作: self._mov_dir_x,self._mov_dir_y,
    #         动作距离:
    #             self._rot_deg
    #             self._mov_spd
    #     '''
    #     if ('L' in action) or ('R' in action):
    #         self._action_rot = True
    #         self._rot_dir = 1.0 if ('L' in action) else -1.0
        
    #     if ('W' in action) or ('A' in action) \
    #     or  ('S' in action) or ('D' in action):
    #         self._action_mov = True
    #         self._calc_move_dir(action)
    
    # used
    # def _calc_move_dir(self,action:str):
    #     '''对动作长度进行归一化
    #     '''
    #     mv_vec_list = []
    #     if ('W' in action): mv_vec_list.append((1,0))
    #     if ('S' in action): mv_vec_list.append((-1,0))
    #     if ('A' in action): mv_vec_list.append((0,1))
    #     if ('D' in action): mv_vec_list.append((0,-1))

    #     mv_x = 0.0
    #     mv_y = 0.0
    #     for v in mv_vec_list:
    #         mv_x+=v[0]
    #         mv_y+=v[1]

    #     if (len(mv_vec_list)!=0):
    #         mv_len = (mv_x**2+mv_y**2)**0.5
    #         mv_x/=mv_len
    #         mv_y/=mv_len

    #     self._mov_dir_x = mv_x
    #     self._mov_dir_y = mv_y

    #     return True

    # unused
    # def _fake_move(self,cur_car_pos,gap_time):
    #     '''
    #         返回 list of Position(irs)
    #         弃用原因：过度依赖API参数，平移时不变deg，
    #           旋转时不变xy，忽略了很多方程情况
    #     '''
    #     if (gap_time>30): gap_time = 30
    #     assert(isinstance(cur_car_pos,Position) 
    #     and cur_car_pos.is_car_center)
        
    #     nxt_car_pos_cands = []
    #     if self._action_rot:
    #         for i in range(pc.deg_rot_epsilon * gap_time):
    #             md_rad = math.radians(i)*self._rot_dir
                
    #             tmp_pos = cur_car_pos.dict_style
    #             tmp_pos['rad'] = Position.round_radians(tmp_pos['rad']+md_rad)

    #             nxt_pos = Position(tmp_pos,is_irs_center=False)
    #             nxt_car_pos_cands.append(nxt_pos)
        
    #     elif self._action_mov:
    #         for i in range(pc.move_epsilon * gap_time): 
    #             md_x = self._mov_dir_x *i
    #             md_y = self._mov_dir_y *i
                
    #             tmp_pos = cur_car_pos.dict_style
    #             tmp_pos['x'] += md_x
    #             tmp_pos['y'] += md_y

    #             nxt_pos = Position(tmp_pos,is_irs_center=False)
                
    #             if (nxt_pos.xy_in_range): 
    #                 nxt_car_pos_cands.append(nxt_pos)
                
    #     else:
    #         nxt_car_pos_cands.append(cur_car_pos)

    #     nxt_irs_pos_cands = []
    #     for car_pos in nxt_car_pos_cands:
    #         nxt_irs_pos_cands.append(car_pos._calc_sensor_center())
        
    #     return nxt_irs_pos_cands



        


