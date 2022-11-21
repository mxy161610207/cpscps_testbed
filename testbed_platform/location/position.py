import math

from . import position_config as pc

class Position:
    def __init__(self,_p,is_irs_center=True) -> None:
        if isinstance(_p,dict):
            self._x = _p['x']
            self._y = _p['y']
            if ('rad' in _p):
                self._rad = Position.round_radians(_p['rad'])
            else:
                self._rad = Position.round_radians(math.radians(_p['deg']))
        else:
            self._x = _p[0]
            self._y = _p[1]
            self._rad = Position.round_radians(_p[2])

        # if not self.xy_in_range:
        #     return

        if (is_irs_center):
            self._pos_kind = pc.IRS_CENTRE
            self._calc_conn_status()
        else:
            self._pos_kind = pc.CAR_CENTER
        return

    def _calc_conn_status(self):
        assert(self.is_irs_center)
        self._ir_inter_walls = [-1,-1,-1,-1]
        for id in range(4):
            # print("=== "+"FRBL"[dir]+":")
            vec_dir = self._dir_id(id)
            # print(to_string(vec_dir))
            x, y = self.x, self.y
            for wi in range(4):
                vec1 = (pc.walls[wi][0][0]-x,pc.walls[wi][0][1]-y)
                vec2 = (pc.walls[wi][1][0]-x,pc.walls[wi][1][1]-y)

                if (Position.cross_mul(vec1,vec_dir)<0 
                and Position.cross_mul(vec1,vec_dir)*Position.cross_mul(vec_dir,vec2)>0):
                    # dir between vec1,vec2
                    # print("Wi = ",wi)
                    self._ir_inter_walls[id]=wi
                    break
        return

    def _calc_car_center(self):
        assert(self.is_irs_center)

        x,y = self.x,self.y
        dx,dy = self.B_dir()
        l = pc.CENTER_DIST

        nx,ny = x+dx*l,y+dy*l
        return Position({'x':nx,'y':ny,'rad':self.rad},is_irs_center=False)

    def _calc_sensor_center(self):
        assert(self.is_car_center)
        
        x,y = self.x,self.y
        dx,dy = self.F_dir()
        l = pc.CENTER_DIST

        nx,ny = x+dx*l,y+dy*l
        return Position({'x':nx,'y':ny,'rad':self.rad},is_irs_center=True)

    def _dir_id(self,id):
        dir_rad = self.rad - id*(math.pi/2.0)
        vec_dir = (math.cos(dir_rad),math.sin(dir_rad))
        return vec_dir

    def F_dir(self):
        return self._dir_id(0)
    
    def R_dir(self):
        return self._dir_id(1)
    
    def B_dir(self):
        return self._dir_id(2)
    
    def L_dir(self):
        return self._dir_id(3)

    def pos_detail_str(self,prefix_str = ""):
        s = "{} position ({:.3f},{:.3f}), rad = {:.2f}, deg = {:.3f}, abs_sin = {}".format(
            prefix_str,
            self.x,self.y,self.rad,self.deg,
            math.fabs(math.sin(self.rad)))
        return s

    @property
    def x(self):
        return self._x
  
    @property
    def y(self):
        return self._y    

    @property
    def rad(self):
        return self._rad
    
    @property
    def deg(self):
        return math.degrees(self._rad)

    @property
    def is_car_center(self):
        return self._pos_kind == pc.CAR_CENTER

    @property
    def is_irs_center(self):
        return self._pos_kind == pc.IRS_CENTRE
    
    @property
    def dict_style(self):
        return {'x':self.x,'y':self.y,'rad':self.rad,'deg':self.deg}

    @property
    def list_style(self):
        return [self.x,self.y,self.deg]

    @property
    def irs_inter_list(self):
        assert(self.is_irs_center)
        return self._ir_inter_walls[:]
    
    @property
    def irs_status_str(self):
        assert(self.is_irs_center)
        s = "{}{}{}{}".format(self._ir_inter_walls[0],self._ir_inter_walls[1],self._ir_inter_walls[2],self._ir_inter_walls[3])
        return s
    
    @property
    def irs_inter_detail_str(self):
        assert(self.is_irs_center)
        s = "[F,R,B,L] on walls {}".format(self._ir_inter_walls)
        return s

    @property
    def pos_str(self):
        s = "<{}> x={:.3f} y={:.3f} deg={:.3f}".format(
            'S' if self.is_irs_center else 'C',
            self.x,self.y,self.deg)
        return s   
    
    @property
    # TODO: 区分car_center和irs_center的有效区域。
    def xy_in_range(self):
        for _ in (self.x,self.y):
            if (0<_ and _<pc.E):continue
            else:
                return False
        return True

    @staticmethod 
    def cross_mul(vec1,vec2):
        return vec1[0]*vec2[1]-vec1[1]*vec2[0]
    
    @staticmethod 
    def calc_degree_diff(pos1,pos2):
        assert(isinstance(pos1,Position))
        assert(isinstance(pos2,Position))
        assert(pos1._pos_kind == pos2._pos_kind)
            
        deg1,deg2 = pos1.deg,pos2.deg
        if (deg2<deg1): deg2+=360

        diff_deg = deg2 - deg1

        if (diff_deg>180): diff_deg -= 360
        return diff_deg

    @staticmethod
    def calc_distance(pos1,pos2):
        assert(isinstance(pos1,Position))
        assert(isinstance(pos2,Position))
        assert(pos1._pos_kind == pos2._pos_kind)
        
        diff_x = math.fabs(pos1.x-pos2.x)
        diff_y = math.fabs(pos1.y-pos2.y)

        dist = (diff_x**2 + diff_y**2)**0.5
        return dist

    @staticmethod
    def calc_location_diff(pos1,pos2):
        assert(isinstance(pos1,Position))
        assert(isinstance(pos2,Position))
        assert(pos1._pos_kind == pos2._pos_kind)
        
        det_x = pos2.x-pos1.x
        det_y = pos2.y-pos1.y

        return det_x,det_y

    @staticmethod
    def calc_diff_pair(pos1,pos2):   
        assert(isinstance(pos1,Position))
        assert(isinstance(pos2,Position))
        assert(pos1._pos_kind == pos2._pos_kind)

        # if (not isinstance(pos1,Position)): pos1=Position(pos1)
        # if (not isinstance(pos2,Position)): pos2=Position(pos2)

        diff_pos = Position.calc_distance(pos1,pos2)
        diff_deg = Position.calc_degree_diff(pos1,pos2)

        return (diff_pos,diff_deg)
    
    @staticmethod
    def round_radians(rad):
        if rad<0: rad+=math.pi*2.0
        if rad>math.pi*2.0: rad-=math.pi*2.0
        return rad

    @staticmethod
    def round_degrees(deg):
        if deg<0: deg+=360
        if deg>360: deg-=360
        return deg
    



        
        








