import math

from .location_config import CALC_LOG

from .position import Position
from . import position_config as pc

class PositionCands:
    # 默认使用 irs_center 作为pos
    def __init__(self,_p) -> None:
        # self._fig_list = []
        self._car_fig = []

        assert(isinstance(_p,Position))

        if (_p.is_irs_center):
            self._pos = _p 
        else:
            self._pos = _p._calc_sensor_center()

        self._cands_irs_pos = []

        # self._parent = None
        self._select_kid = None
        self._is_fake_point = False

        self._gap_times = 1

        # list of Position(irs)
        self._cands_kids = []
        
        self._is_root = False

        self._print_while_del = True
        return

    def __del__(self):
        ''' TODO 输出到指定文件。
        '''
        if self._print_while_del:
            if (self._pos):
                for _ in range(1): 
                    # print("***del {}".format(self._pos.pos_str))
                    pass

    def set_is_fake_point(self):
        ''' 判断是否是假节点
            假节点: 初始时在中心 朝右上方的节点
        '''
        self._is_fake_point = True

    @property
    def init_irs(self):
        return [0,1,2,3]
    
    @property
    def is_root(self):
        return self._is_root

    @staticmethod
    def create_pos_fig(ax,pos,color = 'b',arrow_color = 'k',marker='o'):
        if (ax is None): return 
        '''
        return (scatter, arrow) to show a car's position
        '''
        assert(isinstance(pos,Position))
        dx = 20*math.cos(pos.rad)
        dy = 20*math.sin(pos.rad)

        pt = ax.scatter([pos.x],[pos.y],
                        s=50,c=color,marker=marker,alpha=0.5)
        pt_aw =ax.arrow(pos.x,pos.y,dx,dy,color=arrow_color,width=1)

        return (pt,pt_aw)

    def remove_figs(self):
        for fig in self._car_fig: fig.remove()

    def print_position(self,prefix_str = "",file=None):
        assert(self._pos!=None)
        # print(self._pos.pos_detail_str(prefix_str),file=file)
        return

    def print_conn_status(self,file=None):
        # print(self._pos.irs_inter_detail_str,file=file)
        pass

    def expand_next_conn_status(self):
        ''' 调用_generate_rand_next_pos，寻找下一步可能的车辆位置
            并由此推断可能的交点情况。
                _gap_times 用于放大fake move的倍数，
                如果当前处于L，并且丢失追踪一次，下一次需要假设选择角度位2倍

            TODO 
        '''
        # TODO use self._gap_times as action base
        # recover函数写完之后，这个应该会变得复杂一些
        if (self._is_fake_point):
            return [self.init_irs]

        self._cands_irs_pos = []
        self._generate_rand_next_pos()

        # 计算交点情况并去重，最后返回list of [_,_,_,_]
        conn_map_status = {}
        for irs_pos in self._cands_irs_pos:
            assert(isinstance(irs_pos,Position) and irs_pos.is_irs_center)
            conn_map_status[irs_pos.irs_status_str] = irs_pos.irs_inter_list

        conn_status = []
        for key in conn_map_status:
            conn_status.append(conn_map_status[key])

        return conn_status

    def _generate_rand_next_pos(self):
        '''
            [output]:下一次 ir_center可能的位置 List of Position(irs)

            - 计算当前真实车辆位置
            - 预测下一次的传感器中心位置
                [原本打算]
                通过预测ideal_move，或者历史执行history_move 
                对车辆的下一个位置进行预测。
                [现在]
                直接xy[-15,+15]范围内按步长3画网格,取网格中心点
                角度[-10,10]按步长2修改。
                生成随机的下一次定位。

        '''
        cur_car_pos = self._pos._calc_car_center()

        cur_x = cur_car_pos.x
        cur_y = cur_car_pos.y
        cur_deg = cur_car_pos.deg
        base = self._gap_times

        assert(base<=pc.LOSS_TIME)

        for dx in range(-pc.xy_nosiy_range,pc.xy_nosiy_range+1,pc.xy_nosiy_step):
            for dy in range(-pc.xy_nosiy_range,pc.xy_nosiy_range+1,pc.xy_nosiy_step):
                for ddeg in range(-pc.deg_nosiy_range,pc.deg_nosiy_range+1,pc.deg_nosiy_step):
                    nxt_x = cur_x + dx * base
                    nxt_y = cur_y + dy * base
                    nxt_deg = cur_deg + ddeg * base

                    tmp = {'x':nxt_x,'y':nxt_y,'deg':nxt_deg}
                    nxt_car_pos = Position(tmp,is_irs_center=False)
                    nxt_irs_pos = nxt_car_pos._calc_sensor_center()
                    self._cands_irs_pos.append(nxt_irs_pos)

        # ''' 旧的fake move，过度依赖api参数进行推断 
        # '''
        # if action is None:
        #     self._cands_irs_pos.append(self._pos)
        #     return
        
        # assert(isinstance(action,ActionMonitor))
        # self._cands_irs_pos.extend(action._fake_move(cur_car_pos,self._gap_times))
        return

    def _filter_illegal_cands(self,cands):
        '''
            filter out too far position 

            [input] cands: list of Position(irs)
            [result] self._cands_kids: list of legal Position(irs)
        '''
        if (self._is_fake_point):
            self._cands_kids = cands[:]
            return

        too_far_dist = 150
        too_far_deg_diff = 15 

        cur = self._pos
        self._cands_kids = []

        for can_pos in cands:
            assert(isinstance(can_pos,Position) 
                and can_pos.is_irs_center)
            # print("",file=CALC_LOG)
            diff_dis = Position.calc_distance(cur,can_pos)
            diff_deg = Position.calc_degree_diff(cur,can_pos)

            # print("wait ftr [{}] irs={}".format( can_pos.pos_str,can_pos.irs_status_str),file=CALC_LOG)
            # print("diff_dis = {:.3f} diff_deg = {:.3f}".format(diff_dis,diff_deg),file=CALC_LOG)

            if (diff_dis > too_far_dist * self._gap_times):
            # or math.fabs(diff_deg)>too_far_deg_diff): 
                # print("[-] ftr out, too diff dist > {}*{} gap".format(too_far_deg_diff,self._gap_times),file=CALC_LOG)
                continue

            # print("[+] ftr left",file=CALC_LOG)
            self._cands_kids.append(can_pos)

        # print("ftr left cnt =", len(self._cands_kids))
        for i,can in enumerate(self._cands_kids):
            # print("[{}] {}".format(i,can.pos_str))
            pass
        # print()

        return

    def _select_simillest_kid(self,pivot_irs_pos,msg):
        ''' 以当前pivot_irs_pos为标准，相似度评分，寻找最相似的位置
            [返回值]:int 一个选择结果
        '''
        assert(len(self._cands_kids)!=0)

        msg.append("")

        tmp_cho = -1
        tmp_raw_diff = 0
        tmp_tor_diff = 0

        tolerate_dist_diff = 10
        tolerate_deg_diff = 3

        for i,can in enumerate(self._cands_kids):
            dist = Position.calc_distance(pivot_irs_pos,can)
            ddeg = math.fabs(Position.calc_degree_diff(pivot_irs_pos,can))

            tor_dist = max(0,dist - tolerate_dist_diff)
            tor_ddeg = max(0,ddeg - tolerate_deg_diff)

            cur_diff = dist*10 + ddeg *500 
            tor_diff = tor_dist*10 + tor_ddeg *500

            msg.append("[{}] score: {:.3f} + {:.3f} = {:.3f} / tor = {:.3f}".format(
                i,dist,ddeg,cur_diff,tor_diff))
            # print("[{}] score: {:.3f} + {:.3f} = {:.3f} / tor = {:.3f}".format(i,dist,ddeg,cur_diff,tor_diff),file=CALC_LOG)

            if (tmp_cho==-1 
            or(tor_diff < tmp_tor_diff)
            or(tor_diff == tmp_tor_diff and cur_diff < tmp_raw_diff)):
                tmp_cho = i
                tmp_raw_diff = cur_diff
                tmp_tor_diff = tor_diff
            
        msg.append("try select = {}".format(tmp_cho))
        return tmp_cho

    def _select_best(self, nxt_irs_pos, msg):
        '''
            从现有候选kids中选择最合适的位置（和nxt_irs_pos最相似）
            [执行结束]: self._choice : int, 选择结果, 当kids为空时值为0
            [返回值]:self._choice为准
                当kids为空时，self._choice为0
        '''
        self._choice = 0
        if len(self._cands_kids)==0:
            return self._choice

        if (self._is_fake_point):
            choice = 0
            for i,can in enumerate(self._cands_kids):
                if (0<can.deg and can.deg<90):
                    choice = i
                    break
            self._choice = choice
        else:
            self._choice = self._select_simillest_kid(nxt_irs_pos,msg)
        return self._choice
    
    def _make_select(self,choice:int):
        '''
            [执行结果]: select_kid 被赋值，
                       _cands_kids.pop(choice)
            [返回值]: 被选择的孩子PositionCands
        '''
        assert (choice<len(self._cands_kids))

        be_select = PositionCands(self._cands_kids[choice])
        self._select_kid = be_select
        
        self._cands_kids.pop(choice)

        return be_select
