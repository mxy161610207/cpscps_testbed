from . import position_config as pc

class Distance:
    _distance = []
    _is_math_distance = True
    # md_dist = [131,99,119,119]
    def __init__(self,_d,handle = 'modify'):
        self._distance = _d[:]  # F R B L
        if (handle=='modify'):
            self._modify()
        elif (handle=='recover'):
            self._recover()
        pass

    def _modify(self):
        self._distance[pc.F]+=131
        self._distance[pc.B]+=99
        self._distance[pc.L]+=119
        self._distance[pc.R]+=119
        self._is_math_distance = True

    def _recover(self):
        self._distance[pc.F]-=131
        self._distance[pc.B]-=99
        self._distance[pc.L]-=119
        self._distance[pc.R]-=119
        self._is_math_distance = False
    
    @property
    def list_style(self):
        return self._distance
