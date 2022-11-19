from .candidate import PositionCands

class FixedSizeQueue:
    def __init__(self,size=3) -> None:
        self._queue = []
        self._fixed_size = size
        self._size = 0

    @property
    def size(self):
        return self._size

    @property
    def is_full(self):
        return (self.size>=self._fixed_size)
    
    @property
    def is_empty(self):
        return self.size==0

    @property
    def tail(self):
        return self._queue[-1]
    
    @property
    def head(self):
        return self._queue[0]

    def put(self,elem):
        if (self.is_full): self.pop()
        self._queue.append(elem)
        self._size+=1

    def pop(self):
        if (self.is_empty): return
        self._queue.pop(0)
        self._size-=1
    
    def clear(self):
        self._queue.clear()
        self._size=0

class LocationQueue(FixedSizeQueue):
    def __init__(self, size=200) -> None:
        super().__init__(size)
        self._sync_queue = None

    def put(self,elem):
        assert(isinstance(elem,PositionCands))
        super().put(elem)

    def peek(self,sz):
        sz = min(sz,self.size)
        l = []
        for i in range(1,sz+1):
            pc = self._loc_queue._queue[-i]
            assert(isinstance(pc,PositionCands))
            
            l.append(pc._pos._calc_car_center().dict_style)
        return l