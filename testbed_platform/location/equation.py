import time
import math

from .position import Position
from . import position_config as pc
from .location_config import CALC_LOG


class MyEq:
    def __init__(self,dir,wid,d):
        self._is_about_x = True if (wid%2==1) else False
        self._is_about_sin = True if (wid%2==dir%2) else False
        self._is_E_minutes = True if (wid<2) else False
        self._D = d
        self._D_tag = 'FRBL'[dir]
    
    def to_string(self,is_num=False):
        s =  "{} = ({}{}) / ({})".format(
                "sin a" if self._is_about_sin else "cos a",
                "E - " if self._is_E_minutes else "",
                "x" if self._is_about_x else "y",
                self._D_tag if not is_num else self._D
            )
        return s

    def get_coef(self,base=1.0):
        # (pc.E - y) / (F)  ^ 2
        # (y) / (L)
        base = base / (self._D*self._D)
        base = float(base)
        A = 1 
        B = -2*pc.E if self._is_E_minutes else 0
        C = pc.E**2 if self._is_E_minutes else 0

        return [A*base,B*base,C*base]

    def solve_with_left_eq(self,left_val):
        lv = left_val*self._D
        lv = lv if not self._is_E_minutes else pc.E-lv
        assert(0<=lv and lv<=pc.E)
        return lv
    
    def solve_with_right_eq(self,right_val):
        rv = (pc.E-right_val) if self._is_E_minutes else right_val
        rv /= self._D
        assert(0<=rv and rv<=1)
        return rv
    
class MyEqSet:
    _mute = False
    def __init__(self,ir_inter_point,ir_dist):

        self._TODO_four = False
        self._TODO_strict = False
        self._TODO_fuzzy = False

        self.eqs = []
        self._ir_inter = ir_inter_point[:]
        self._ir_dist = ir_dist[:]
        self._other_irs = []
        self._cur_irs = ""
        for dir in range(4):
            d = ir_dist[dir]
            wid = ir_inter_point[dir]
            self.eqs.append(MyEq(dir,wid,d))
        
    def print_total(self):
        for eq in self.eqs:
            assert(isinstance(eq,MyEq))
            print(eq.to_string(),file=CALC_LOG)
            # print(eq.to_string())
        self.check_eqs(self.eqs)
        print(file=CALC_LOG)

    def _eq_group_to_string(self,eq_group,is_num=False):
        s=""
        for eq in eq_group:
            assert(isinstance(eq,MyEq))
            s+=eq.to_string(is_num)+' | '
        return s

    def solve_with_ideal_degree(self,ideal_degree):
        '''
            计算红外交点中心, 将大疆角作为当前sin和cos值
            
            对四个方程求解的x和y取平均。
            如果只有x或者只有关于y的方程， return None

            否则返回唯一解。
        '''
        st = time.time()
        ideal_rad = math.radians(ideal_degree)

        ideal_sin = math.fabs(math.sin(ideal_rad))
        ideal_cos = math.fabs(math.cos(ideal_rad))

        raw_sols = {'x':[],'y':[]}
        for eq in self.eqs:
            assert(isinstance(eq,MyEq))
            key = 'x' if eq._is_about_x else 'y'
            val = eq.solve_with_left_eq(
                ideal_sin if eq._is_about_sin else ideal_cos
            )
            raw_sols[key].append(val)

        if (not raw_sols['x'] or  not raw_sols['y']):
            if (not self._mute):
                print("[TODO] equations LACK {}".format( 'x' if not raw_sols['x'] else 'y'),file=CALC_LOG)
                pass
            
            return None

        avg_x = sum(raw_sols['x'])/len(raw_sols['x'])
        avg_y = sum(raw_sols['y'])/len(raw_sols['y'])
        
        ed = time.time()
        
        p = {'x':avg_x,'y':avg_y,'rad':ideal_rad}
        tmp_pos = Position(p,is_irs_center=True)

        return tmp_pos 

    def solve(self):
        '''
            计算红外交点中心
            - solve_three(): get 4 solution of 3eq_groups
                [output] raw_cands: 
                    list of {'x':x,'y':y,'abs_sin':abs_sin}
            - solve_legal_combine(): 
                combine 4 groups solutions to the sol of 4eq_groups
                and use _rot_rad() to get legal degree

                [output] self.legal_cands: 
                    list of Position, which _pos_kind = IRS_CENTER
        '''
        # eqs group solver
        st = time.time()
        raw_cands = {}
        for rm in range(4):
            to_solve = []
            for i in range(4):
                if (i!=rm): to_solve.append(self.eqs[i])

            if (not self._mute): 
                print("[Group {}]".format(rm),file=CALC_LOG)
                pass

            sols = self.solve_three(to_solve)
            raw_cands[rm] = sols
            # # print(sols)
        
        # 
        md = time.time()
        if (not self._mute): 
            print("solve time = {:.6f}s".format(md-st),file=CALC_LOG)
            pass

        # solution legal check
        self.legal_cands = []
        self._raw_cands = raw_cands
        self.solve_legal_combine(raw_cands)
        
        ed = time.time()
        if (not self._mute):
            print("check time = {:.6f}s".format(ed-md),file=CALC_LOG)
            print(file=CALC_LOG)
            print("total time = {:.6f}s".format(ed-st),file=CALC_LOG)
            print("-"*50,file=CALC_LOG)
            pass
        
        # print("total time = {:.6f}s".format(ed-st))
        # print("-"*50)
        return      

    def _cands_diff(self,base,cand):
        pos_diff = math.fabs(base['x']-cand['x'])+math.fabs(base['y']-cand['y'])
        deg_diff = math.fabs(base['abs_sin']-cand['abs_sin'])

        diff = pos_diff
        return diff

    def _rot_rad(self,fin_cands,to_check_rad):
        if (to_check_rad<0): to_check_rad+=math.pi/2
        if (to_check_rad>math.pi/2): to_check_rad-=math.pi/2
        
        cands_cnt = 0
        for rot in range(4):
            if (not self._rot_mute): 
                print("-",file=CALC_LOG)
                pass
            new_rad = (rot//2)*math.pi + ((-1)**(rot%2) )*to_check_rad
            if (new_rad>2*math.pi): new_rad-=2*math.pi
            if (new_rad<0): new_rad+=2*math.pi

            tmp_dict = {'x':fin_cands['x'],'y':fin_cands['y'],'rad':new_rad}
            tmp_irs_pos = Position(tmp_dict)
            tmp_irs_str = tmp_irs_pos.irs_status_str

            if (tmp_irs_str in self._other_irs):
                self.legal_cands.append(tmp_irs_pos)
                if (not self._rot_mute):
                    print("[+] {}".format(tmp_irs_pos.pos_str),file=CALC_LOG)
                    print("ir check success",file=CALC_LOG)
                    pass
                cands_cnt+=1
            else:
                if (not self._rot_mute):
                    print("[+] {}".format(tmp_irs_pos.pos_str),file=CALC_LOG)
                    print(tmp_irs_str,'vs.', self._other_irs,file=CALC_LOG)
                    print("ir check fail",file=CALC_LOG)
                    pass
                pass
        return cands_cnt

    def solve_legal_combine(self,sols):
        sol_cnt=0
        for i in range(4):
            sol_cnt+=len(sols[i])
        if (sol_cnt==0):
            self._TODO_four = True
            if (not self._mute):
                print("[TODO] four eqs no solution!!",file=CALC_LOG)
                pass
            return

        avg_cands = {'x':0, 'y':0, 'abs_sin':0} # x,y,abs_sin
        avg_cnt = 0
        
        # combine single solution 
        for i in range(4):
            sol = sols[i]
            if (sol and len(sol)==1):
                tmp = dict(sol[0])
                for k in avg_cands:
                    avg_cands[k]+=tmp[k]
                avg_cnt+=1
        
        assert(avg_cnt!=0)

        tmp_cands = {'x':0, 'y':0, 'abs_sin':0}
        for k in avg_cands:
            tmp_cands[k]= avg_cands[k]/avg_cnt
        
        if (not self._mute):  
            print("===> tmp x={:.3f} y={:.3f} abs_sin={:3f}".format(tmp_cands['x'],tmp_cands['y'],tmp_cands['abs_sin']),file=CALC_LOG)
            pass

        # combine one of the two solution 
        _select_mute = False or self._mute
        for i in range(4):
            sol = sols[i]
            if (sol and len(sol)>1):
                if not _select_mute: 
                    print("select one in:",file=CALC_LOG)
                    pass
                cand0 = dict(sol[0])
                cand1 = dict(sol[1])
                if not _select_mute: 
                    print("  cand0","[x={:.3f} y={:.3f} abs_sin={:3f}]".format(cand0['x'],cand0['y'],cand0['abs_sin']),file=CALC_LOG)
                    pass
                if not _select_mute: 
                    print("  cand1","[x={:.3f} y={:.3f} abs_sin={:3f}]".format(cand1['x'],cand1['y'],cand1['abs_sin']),file=CALC_LOG)
                    pass
                diff0 = self._cands_diff(tmp_cands,cand0)
                diff1 = self._cands_diff(tmp_cands,cand1)

                be_select = cand1
                if (diff0<=diff1):
                    be_select = cand0
                if not _select_mute: 
                    print("be_select {}\n".format(0 if be_select == cand0 else 1),file=CALC_LOG)
                    pass

                for k in avg_cands:
                    avg_cands[k]+=be_select[k]
                avg_cnt+=1
        
        # final solution x,y,abs_sin

        fin_cands = {'x':0, 'y':0, 'abs_sin':0} 
        for k in avg_cands:
            fin_cands[k]= avg_cands[k]/avg_cnt
        if (not self._mute):
            print("===> fin x={:.3f} y={:.3f} abs_sin={:3f}".format(fin_cands['x'],fin_cands['y'],fin_cands['abs_sin']),file=CALC_LOG)
            print(file=CALC_LOG)
            pass
        
        rad_sin = math.asin(fin_cands['abs_sin'])
        
        self._rot_mute=False or self._mute
        self._rot_rad(fin_cands,rad_sin)
        self._rot_mute=True or self._mute

        if (len(self.legal_cands)==0):
            self._TODO_strict = True

            # fuzzy rad check
            # self._rot_rad(tmp_cands,rad_sin)
            # self._rot_rad(tmp_cands,rad_sin-0.01)
            # self._rot_rad(tmp_cands,rad_sin+0.01)

            # self._rot_rad(fin_cands,rad_sin-0.01)
            # self._rot_rad(fin_cands,rad_sin+0.01)

            # use single cands check
            self._rot_mute=False or self._mute
            if (not self._rot_mute):
                print("\n\nsingle cands check",file=CALC_LOG)
                pass
            for i in range(4):
                for sol in sols[i]:
                    sol = dict(sol)
                    if (not self._rot_mute): 
                        print(sol,file=CALC_LOG)
                        pass
                    sol_sin = math.asin(sol['abs_sin'])
                    self._rot_rad(sol,sol_sin)

            if (len(self.legal_cands)==0):
                print("no legal",file=CALC_LOG)
                self._TODO_fuzzy = True
                return 
            
            
        assert(len(self.legal_cands)!=0)
        print("legal_cnt = {}, irs = {}".format(len(self.legal_cands),self._ir_inter),file=CALC_LOG)
        for _ in self.legal_cands:
            print("{}".format(_.pos_str),file=CALC_LOG)
            pass
        print("",file=CALC_LOG)

        return

    def solve_legal_check(self,sols):
        self._rot_mute=False or self._mute
        for i in range(4):
            for sol in sols[i]:
                sol = dict(sol)
                if (not self._rot_mute): 
                    print(sol,file=CALC_LOG)
                    pass
                sol_sin = math.asin(sol['abs_sin'])
                self._rot_rad(sol,sol_sin)

        if (len(self.legal_cands)==0):
            self._TODO_strict = True
            print("no legal",file=CALC_LOG)

        return

    def solve_three(self,to_solve):

        lack_sybs = self.check_eqs(to_solve)
        if ('x' in lack_sybs or 'y' in lack_sybs):
            if (not self._mute):
                print("Error: No soltion - Lack ",lack_sybs," UNDO!",file=CALC_LOG)
                print("",file=CALC_LOG)
                pass
            return []


        # '''
        can_solve = False
        sol = []
        # list of [x,y,abs_sin,abs_cos]

        # cs_cnt=0
        for i in range(3):
            for j in range(i+1,3):
                eq_i = to_solve[i]
                eq_j = to_solve[j]   
                eq_k = to_solve[3-i-j] # 0 1 2
                assert(isinstance(eq_i,MyEq))
                assert(isinstance(eq_j,MyEq))
                if (eq_i._is_about_x == eq_j._is_about_x):
                    # 2 about x eq | 2 about y eq
                    if (eq_i._is_about_sin==eq_j._is_about_sin):
                        # cs_cnt+=1
                        # linear equations             
                        
                        # return [x,y,abs_sin,abs_cos]
                        status, ukn = self.solve_linear_eqs(eq_i,eq_j,eq_k)
                        if (status):
                            can_solve = True
                            sol.append(ukn)
                            if (not self._mute): 
                                ukn = dict(ukn)
                                print("x={:.3f} y={:.3f} abs_sin = {:.3f}".format(ukn['x'],ukn['y'],ukn['abs_sin']),file=CALC_LOG)
                        else:
                            if (not self._mute): 
                                print("Error:", ukn,file=CALC_LOG)
                                pass
                    else:
                        # cs_cnt+=1
                        status, ukn = self.solve_quadratic_eqs(eq_i,eq_j,eq_k)
                        if (status):
                            can_solve = True
                            sol.extend(ukn)
                            if (not self._mute): 
                                for _ in ukn:
                                    _=dict(_)
                                    print("x={:.3f} y={:.3f} abs_sin = {:.3f}".format(_['x'],_['y'],_['abs_sin']),file=CALC_LOG)
                        else:
                            if (not self._mute): 
                                print("Error:", ukn,file=CALC_LOG)
                                pass
                        # quadratic equation
                    
        # '''
        if not can_solve:
            if (not self._mute):
                print("CANNOT SOLVE X or Y!!!!!!!!!!!!!",file=CALC_LOG)
                pass
        
        if (not self._mute): 
            print(file=CALC_LOG)
            pass
        return sol

    def check_eqs(self,eqs):
        x_eqs = []
        y_eqs = []
        sin_eqs = []
        cos_eqs = []
        for eq in eqs:
            assert(isinstance(eq,MyEq))
            if (eq._is_about_x): x_eqs.append(eq)
            else: y_eqs.append(eq)
            if (eq._is_about_sin): sin_eqs.append(eq)
            else: cos_eqs.append(eq)
        lack_symbols = []
        if (len(x_eqs)==0): 
            lack_symbols.append('x')
            # # print("Error! no eqs about x")
        if (len(y_eqs)==0):      
            lack_symbols.append('y') 
            # # print("Error! no eqs about y")
        if (len(sin_eqs)==0): 
            lack_symbols.append('sin')
            # # print("Warning! no eqs about sin")
        elif (len(sin_eqs)==3):
            lack_symbols.append('linear') 
        if (len(cos_eqs)==0): 
            lack_symbols.append('cos')
            # # print("Warning! no eqs about cos")
        elif (len(cos_eqs)==3):
            lack_symbols.append('linear') 
        return lack_symbols
    
    def solve_linear_eqs(self, eq_i,eq_j,eq_k):
        assert(isinstance(eq_i,MyEq))
        assert(isinstance(eq_j,MyEq))
        assert(isinstance(eq_k,MyEq))

        # # print("CONVERT TO linear ",self._eq_group_to_string([eq_i,eq_j],is_num=True))

        ukn = {}         
        assert(eq_i._is_E_minutes!=eq_j._is_E_minutes)
        l_val = pc.E/(float)(eq_i._D + eq_j._D)

        if (l_val>1):
            return False,"sum of two opposite dis < pc.E, unable on opposite walls"

        ukn['abs_sin' if eq_i._is_about_sin else 'abs_cos'] = l_val
        ukn['abs_sin' if not eq_i._is_about_sin else 'abs_cos'] = math.sqrt(1-l_val**2)
        
        r_val_i = eq_i.solve_with_left_eq(l_val)
        r_val_j = eq_j.solve_with_left_eq(l_val)
        assert(math.fabs(r_val_i-r_val_j)<1e-4)

        ukn['x' if eq_i._is_about_x else 'y'] = r_val_i

        assert(isinstance(eq_k,MyEq))
        kl_val = ukn['abs_sin' if eq_k._is_about_sin else 'abs_cos']

        k_syb = 'x' if eq_k._is_about_x else 'y'
        k_syb_val = eq_k.solve_with_left_eq(kl_val)
        if (k_syb in ukn):
            if (math.fabs(k_syb_val-ukn[k_syb])>100):
                return False,"Symbol {} solve by 2 ways has diff val {:.3f} & {:.3f}".format(k_syb,ukn[k_syb],k_syb_val)
            else:
                ukn[k_syb+'_chk'] = k_syb_val
        else:
            ukn[k_syb] = k_syb_val

        return True,sorted(ukn.items(), key=lambda d: d[0]) 

    def solve_quadratic_eqs(self, eq_i,eq_j,eq_k):
        assert(isinstance(eq_i,MyEq))
        assert(isinstance(eq_j,MyEq))
        assert(isinstance(eq_k,MyEq))
        
        # # print("CONVERT TO quadratic ",self._eq_group_to_string([eq_i,eq_j],is_num=True))
            
        # sin a = (pc.E - y) / (F) | cos a = (y) / (L) | 
        baseij = (eq_i._D*eq_j._D)**2
        i_mat = eq_i.get_coef(baseij)
        j_mat = eq_j.get_coef(baseij)
        mat = [i_mat[x]+j_mat[x] for x in range(3)]
        mat[2]-=baseij

        a,b,c = mat[0],mat[1],mat[2]
        det = b**2 - 4.0*a*c
        if det<0:
            print("E={}".format(pc.E),file=CALC_LOG)
            return False,"No solution - det < 0, {} {} {} {}".format(det,a,b,c)
        
        sqrt_det = math.sqrt(det)
        x1 = (b+sqrt_det)/(-2.0*a)
        x2 = (b-sqrt_det)/(-2.0*a)

        legal_syb = 'x' if eq_i._is_about_x else 'y'
        legal_val = []
        for x in [x1,x2]:
            if 0<=x and x<=pc.E: legal_val.append(x)
                
        if len(legal_val)==0:
            return False,"No solution - no legal {}".format(legal_syb)
        elif len(legal_val)>1:
            print("Warning! mul legal_value",file=CALC_LOG)
            pass
        
        ukn_group = []
        print("legal {}={}".format(legal_syb,legal_val),file=CALC_LOG)
        for x in legal_val:
            ukn = {}
            ukn[legal_syb] = x 
            for q in [eq_i,eq_j]:
                syb = 'abs_sin' if q._is_about_sin else 'abs_cos'
                val = q.solve_with_right_eq(x)
                ukn[syb]=val

            eqk_r_syb = 'x' if eq_k._is_about_x else 'y'
            eqk_l_syb = 'abs_sin' if eq_k._is_about_sin else 'abs_cos'
            eqk_r_val = eq_k.solve_with_left_eq(ukn[eqk_l_syb])
            ukn[eqk_r_syb] = eqk_r_val
            ukn = sorted(ukn.items(), key=lambda d: d[0]) 
            ukn_group.append(ukn)

        return True,ukn_group  