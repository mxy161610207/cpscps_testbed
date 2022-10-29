import math

from .distance import Distance
from .equation import MyEqSet
from .position import Position
from .candidate import PositionCands
from .action_analysis import ActionMonitor,MotionQueue,ActionAnalysis
from .location_config import CALC_LOG, SystemState,OUTPUT_DIR
from .fixed_size_queue import FixedSizeQueue
from . import position_config as pc

class LocationQueue(FixedSizeQueue):
    def __init__(self, size=200) -> None:
        super().__init__(size)
    
    def put(self,elem):
        assert(isinstance(elem,PositionCands))
        super().put(elem)
        

class LocationList:
    def __init__(self,default_len=200,name='default',need_sim_pair=False) -> None:
        self.state = SystemState.INIT
        self.name = name
        
        if (need_sim_pair): 
            self._sim_pair = LocationList(50,name='Simulate',need_sim_pair=False)
        else:
            self._sim_pair = None

        # create two info queue
        self._loc_queue = LocationQueue(default_len)
        self._init_pos = None
        self._motion_queue = MotionQueue(3)

        self.reset()

    def reset(self):
        self.state = SystemState.INIT
        self._init_handle = None
        self._init_angle = False

        self._cur_sdk_angle = 0.0
        self._correcnt_sdk_deg = 0.0
        self._correcnt_loc_deg = 0.0

        self._loc_queue.clear()
        # create init point
        fake_point = LocationList._create_fake_point()
        if (self.is_simulate): 
            fake_point._is_fake_point = False
        self._loc_queue.put(fake_point)
        print("put one fake point,size = ",self.size)

        self._motion_queue.clear()

        self._action = None

        if (self.has_sim_pair): 
            self._sim_pair.reset()
        return

    @property
    def size(self):
        return self._loc_queue.size

    def get_latest_pos(self,sz):
        sz = min(sz,self.size)
        l = []
        for i in range(1,sz+1):
            pc = self._loc_queue._queue[-i]
            assert(isinstance(pc,PositionCands))
            
            l.append(pc._pos._calc_car_center().dict_style)
        return l


    @property
    def is_guard(self):
        return self.name=='Guard' or self.has_sim_pair

    @property
    def is_simulate(self):
        return self.name=='Simulate'
    
    @property
    def is_initialized(self):
        return self.state != SystemState.INIT

    # @property
    # def root(self):
    #     assert(not self._loc_queue.is_empty)
    #     assert(isinstance(self._loc_queue.head,PositionCands))
    #     return self._loc_queue.head

    @property
    def current(self):
        assert(not self._loc_queue.is_empty)
        assert(isinstance(self._loc_queue.tail,PositionCands))
        return self._loc_queue.tail

    @property
    def current_postion(self):
        return self.current._pos

    @property
    def is_unmovable(self):
        return self.location_analysis == ActionAnalysis.UNMOVABLE

    @property
    def location_analysis(self):
        return self._motion_queue.analysis()

    @property
    def previous(self):
        assert(not self._loc_queue.is_empty)
        if (self._loc_queue.size==1): 
            return None

        assert(isinstance(self._loc_queue._queue[-2],PositionCands))
        return self._loc_queue._queue[-2]

    @property
    def has_sim_pair(self):
        return not (self._sim_pair is None)

    def set_sdk_angle(self,mov_deg):
        # turn left angle be small
        # turn right angle be big
        self._cur_sdk_angle = -mov_deg
    
    def set_raw_sdk_angle(self,raw_angle):
        if not self._init_angle:
            self._init_angle = True
        # turn left angle be small
        # turn right angle be big
        self._raw_sdk_angle = Position.round_degrees(-raw_angle)
    
    def calc_ideal_angle(self):
        angle = 0.0
        if (self.is_initialized):
            angle = self._correcnt_loc_deg - self._correcnt_sdk_deg + self._cur_sdk_angle
        return Position.round_degrees(angle)
    
    def set_action(self,action_argv):
        recv_action =  ActionMonitor(
            self.current_postion,
            action_argv)     

        if recv_action.is_empty: 
            self._action = None
        else:
            
            if not (self._action is None):
                print("[TODO] self.action not None! to late end")
                self._action = None

            self._action = recv_action

        self.current._gap_times = 1
        return 

    def get_action_state(self,msg=None):
        analysis_result = self._motion_queue.analysis(msg)
        if msg: msg.append(analysis_result)
        return analysis_result,self.current._pos


    def change_state(self,next_state:SystemState):
        if next_state==SystemState.ADJUST:
            if (self.state!=SystemState.NORMAL and self.state!=SystemState.ADJUST):
                raise Exception("{} cannot convert to {}".format(self.state,next_state))
        elif next_state==SystemState.NORMAL:
            if (self.state!=SystemState.ADJUST and self.state!=SystemState.INIT):
                raise Exception("{} cannot convert to {}".format(self.state,next_state))
        elif next_state == SystemState.INIT:
            self.reset()

        self.state = next_state

    def append(self,pos_cand):
        '''
            将当前的handle移动到相邻位置
        '''
        assert(isinstance(pos_cand,PositionCands))

        # 如果这次移动是从fake节点第一次定位成功
        if (self.current._is_fake_point):
            self.change_state(SystemState.NORMAL)
            self._correcnt_sdk_deg = self._cur_sdk_angle
            self._correcnt_loc_deg = pos_cand._pos.deg
            # pop the fake location
            self._loc_queue.pop()
        
        # 移动并更新图标
        self._loc_queue.put(pos_cand)
        print(">>> {} [append] {}".format(self.name,pos_cand._pos.pos_detail_str()),file=CALC_LOG)
        print(">>> {} [append] {}".format(self.name,pos_cand._pos.pos_detail_str()))
        # ! location server log
        # print(">>> {} [append] {}".format(self.name,pos_cand._pos.pos_detail_str()))
        print("loc_size =",self.size,file=CALC_LOG)
        print(self.state,self.has_sim_pair,self.is_initialized,file=CALC_LOG)

        # TODO 如果这次移动应该映射到虚拟树上
        # 什么情况不应该映射：
        #  1. ADJUST 此时sim_tree被冻结
        #  2. 未初始化，或者本次初始化到一个虚拟节点。
        if (self.has_sim_pair and self.is_initialized):
            if (self.previous==None):
                cur_motion = (0,0,0)
            else:
                cur_motion = ActionMonitor.calc_motion_between_two_pos(
                    self.previous._pos,self.current._pos)
            print("cur_motion = ({:.3f},{:.3f},{:.3f})".format(cur_motion[0],cur_motion[1],cur_motion[2]),file=CALC_LOG)
            self._motion_queue.put(cur_motion)

            if (self.state == SystemState.NORMAL):
                self._sim_pair.apply_motion(cur_motion)
        
        print("="*50,file=CALC_LOG)

    @staticmethod
    def _create_fake_point(car_x=250,car_y=250,car_rad = math.pi/2):
    # def _create_fake_point(car_x=600,car_y=1200,car_rad = math.pi/2):
        car_pos = Position({'x':car_x,'y':car_y,'rad':car_rad},
            is_irs_center=False)
        cur_pos_cand = PositionCands(car_pos)
        cur_pos_cand.set_is_fake_point()
        return cur_pos_cand

    def apply_motion(self,motion):
        '''
            only for sim_tree
        '''
        nxt_irs_pos = ActionMonitor.act_motion(self.current._pos,motion)
        next_pos_cand = PositionCands(nxt_irs_pos)
        
        self._motion_queue.put(motion)
        self._loc_queue.put(next_pos_cand)
        next_pos_cand.print_position("{} [append]".format(self.name))

    def advance_once(self,sensor_data,msg):
        if (self.state == SystemState.LOSS): 
            raise Exception("NEED RECOVER")

        self._expand_once(sensor_data,msg)
        self._try_select_best(msg)

        cho = self.current._choice
        print("choice =",cho,file=CALC_LOG)

        if (len(self.current._cands_kids)==0):
            print("choice =",-1,file=CALC_LOG)
        else:
            self._make_select(cho)

    def _expand_once(self,sensor_data,msg):
        ''' 对当前handle 扩展求解一次，扩展结果为下一步满足sensor_data的位置
            [执行结束]: current._cands_kids 保存扩展结果
            [返回值]: 如果有kids返回True, 否则返回False
        '''
        if (len(sensor_data)!=4): 
            raise Exception("error sensor info {}".format(sensor_data))
            
        F,B,L,R =  int(sensor_data[0]),int(sensor_data[1]),int(sensor_data[2]),int(sensor_data[3])
        print("calc with",sensor_data,file=CALC_LOG)

        # 列出当前节点经过扩展后的交点情况
        self.current.print_position("[last]",file=CALC_LOG)
        assert(isinstance(self.current,PositionCands))
        cand_irs = self.current.expand_next_conn_status()
        
        # 将[0,1,2,3] -> "0123"
        total_irs_mark = []
        for irs in cand_irs:
            s = "{}{}{}{}".format(irs[0],irs[1],irs[2],irs[3])
            total_irs_mark.append(s)
        
        if (self._action):
            print(self._action.action_state_str,file=CALC_LOG)
        
        print(total_irs_mark,file=CALC_LOG)

        # 设置当前真实距离边界的值
        raw_dis = [F,R,B,L]
        md_dis = Distance(raw_dis)._distance
        msg.append("modified distance FRBL = {}".format(md_dis))
        msg.append("> ir_cnt = {}".format(len(cand_irs)))
        
        # 列方程求解，求解结果
        #   legal_cands : list of Position(irs)
        # TODO 对 _TODO_four 修改下一次的扩展base
        legal_cands = []

        # only_calc_xy = False
        # if (self._init_angle):
        #     ideal_degree = self._raw_sdk_angle
        #     legal_cands_with_ideal_degree = []
        #     only_calc_xy = True
        # else:
        #     self.current._filter_illegal_cands([])
        #     return False

        _TODO_four = 0

        self._mute = True

        # for irs in cand_irs:
        #     msg.append("> maybe {}".format(irs))
        #     cur_eqs = MyEqSet(irs,md_dis)
        #     # cur_eqs._mute = self._mute
        #     cur_eqs._cur_irs = irs
        #     cur_eqs._other_irs = total_irs_mark[:]
        #     sol = cur_eqs.solve_with_ideal_degree(ideal_degree)
        #     if sol:
        #         assert(isinstance(sol,Position))
        #         tmp = sol.dict_style
        #         msg.append("[New] x={:.3f} y={:.3f} deg={:.3f}".format(tmp['x'],tmp['y'],tmp['deg']))
        #         legal_cands_with_ideal_degree.append(sol)

        for irs in cand_irs:
            msg.append("> maybe {}".format(irs))
            # msg.append(">> irs = {}".format(irs))

            cur_eqs = MyEqSet(irs,md_dis)
            # cur_eqs._mute = self._mute
            cur_eqs._cur_irs = irs
            cur_eqs._other_irs = total_irs_mark[:]
            if (not self._mute):
                cur_eqs.print_total()
                cur_eqs._mute = False
            cur_eqs.solve()

            _TODO_four += 1 if cur_eqs._TODO_four else 0

            for rm in range(4):
                for sol in cur_eqs._raw_cands[rm]:
                    sol=dict(sol)
                    msg.append("[G{}] x={:.3f} y={:.3f} abs_sin={:.3f}".format(rm,sol['x'],sol['y'],sol['abs_sin']))

            # for can in cur_eqs.legal_cands:
            #     assert(isinstance(can,Position) and can.is_irs_center)
                # print("{} irs={}".format(can.pos_str,can.irs_status_str))
                # msg.append("{} irs={}".format(can.pos_str,can.irs_status_str))
            
            legal_cands.extend(cur_eqs.legal_cands)

        # 记录当前求解的可行结果到cur_pos_cand._cands_kids
        #   cur_pos_cand._cands_kids : list of Position(irs)
        if (self.current._is_fake_point):
            # assert(len(legal_cands)!=0)
            print("init_select__")
        
        # 去除距离相差太远的
        self.current._filter_illegal_cands(legal_cands)
        # self.current._filter_illegal_cands(legal_cands_with_ideal_degree)

        # 如果本次无解
        if (len(self.current._cands_kids)==0):
            print("choice =",-1)
            self.current._gap_times +=1
            if (self._action and self.current._gap_times == pc.LOSS_TIME):
                self.state = SystemState.LOSS
            return False

        return True

    # def _append_cands_info(self,msg):
    #     msg.append("-"*10)
    #     msg.append("gap time = {}".format(self.current._gap_times))
    #     if (not self.current._is_fake_point):
    #         # show last irs center & cars center info
    #         msg.append("[last]{} irs={}".format(
    #             self.cur_pos.pos_str,self.cur_pos.irs_inter_list))

    #         tmp = self.cur_pos._calc_car_center()
    #         msg.append("[last]{}".format(tmp.pos_str))
    #     else:
    #         # have not initialized, no past data
    #         msg.append("[last] __init__ init_irs={}".format(
    #             PositionCands.init_irs))
    
    #     msg.append("")
    #     assert(isinstance(self.current,PositionCands))
    #     for i,can in enumerate(self.current._cands_kids):
    #         assert(isinstance(can,Position) and can.is_irs_center)
    #         if (self.draw_car_center):
    #             tmp = can._calc_car_center()
    #         else:
    #             tmp = can
    #         irs = can.irs_status_str
    #         msg.append("[{}]{} irs={}".format(
    #                 i,tmp.pos_str,irs))

    def _try_select_best(self,msg):
        ''' 根据现在的Action生成预测位置，并寻找和预测位置最相近的下一步位置
            [执行结束]: current._choice 保存定位结果，没有候选位置值为0
        '''
        # self._append_cands_info(msg)
        msg.append("-"*10)

        if (self.is_initialized):
            print("sdk angel = {:.3f}".format(self._raw_sdk_angle),file=CALC_LOG)
            msg.append("sdk angel = {:.3f}".format(self._raw_sdk_angle))
        else:
            msg.append("sdk angel not initialized")

        # 预测 下一次的位置
        cur_car_pos = self.current._pos._calc_car_center()
        nxt_car_pos = None
        if (self._action is None):
            nxt_car_pos = cur_car_pos
        else:
            assert(isinstance(self._action,ActionMonitor))
            motion = self._action.ideal_motition(msg)
            msg.append("motion = ({:.3f},{:.3f},{:.3f})".format(
                motion[0],motion[1],motion[2]))
            nxt_car_pos = ActionMonitor.act_motion(cur_car_pos,motion,msg=msg)
            assert(nxt_car_pos.is_car_center == True)
        
        nxt_irs_pos = nxt_car_pos._calc_sensor_center().dict_style

        # 通过SDK的sub_angle修正预测位置
        if (self.is_initialized):
            nxt_irs_pos['rad'] = math.radians(self._raw_sdk_angle)
        nxt_irs_pos = Position(nxt_irs_pos,is_irs_center=True)
        
        msg.append("[ideal]{} irs = {}".format(nxt_irs_pos.pos_str,nxt_irs_pos.irs_inter_list))

        print("[last]",cur_car_pos._calc_sensor_center().pos_str,file=CALC_LOG)
        print("[idea]",nxt_irs_pos.pos_str,file=CALC_LOG)

        # 选择和预测位置最相似的位置
        self.current._select_best(nxt_irs_pos,msg)
        return 

    def _make_select(self,choice):
        '''步骤：
            1.将handle._cands_kids[choice]作为本次的定位结果。
            2.修改当前树上的位置指针handle
            3.如果超层数，移除根和非选择孩子的节点
            4.更新action
           [执行结果]: 
            建立父子关系，被选择孩子从cands中pop (Positon->PositionCands)
            handle指向该孩子
        '''
        # 从cur_pos_cand._cands_kids 选择最合适的位置
        # global system_state
        # system_state = TO_SELECT
        # state, choice = self._try_select_best(msg)
        next_pos_cand = self.current._make_select(choice)

        self.append(next_pos_cand)

        if (self._action):
            self._action.update_state(self.current._pos)
            if self._action.is_finished:
                    self._action = None

    @property
    def need_recover(self):
        return self.state==SystemState.LOSS


    
    # def get_last_motition(self,msg):
    #     if (self._sim_motion):
    #         s = "\n\n{:.3f} {:.3f} {:.3f}".format(self._sim_motion[0],self._sim_motion[1],self._sim_motion[2])
    #     else:
    #         s = "None"
    #     # for _ in range(20):
    #     #     print("sim motion {}".format(s))
    #     if (msg):
    #         msg.append(s)

    # @staticmethod
    # def get_location_message(cur_tree):
    #     assert(isinstance(cur_tree,LocationList))
    #     msg = "{},{:.3f},{:.3f},{:.3f}".format(
    #         cur_tree.motion_queue.analysis(),
    #         cur_tree.cur_pos.x,
    #         cur_tree.cur_pos.y,
    #         cur_tree.cur_pos.deg,
    #     )
    #     print("location pos=",msg)
    #     return msg

    # @staticmethod
    # def get_action_explore(cur_tree,argv):
    #     assert(isinstance(cur_tree,LocationList))
    #     action = ActionMonitor(cur_tree.cur_pos,argv)
    #     state,condition = action.explore()
    #     msg = "{},{},{},{},{}".format(
    #         state,
    #         condition[0],condition[1],condition[2],condition[3]
    #     )
    #     print("action check=",msg)
    #     return msg

