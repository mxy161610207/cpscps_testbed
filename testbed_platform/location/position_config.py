from enum import Enum

# global_value
FB_MODIFY = 112
LR_MODIFY = 118

# E = 2420
E = 2720

LOSS_TIME = 30

# position type
CAR_CENTER = 0
IRS_CENTRE = 1 
CENTER_DIST = 14

# direction enum
F = 0
R = 1
B = 2
L = 3 

# walls
walls = [
    [[0,E],[E,E]], # wid 0 
    [[E,E],[E,0]], # wid 1 
    [[E,0],[0,0]], # wid 2 
    [[0,0],[0,E]]  # wid 3 
    ]

# nosiy range - 即使车辆不移动，测距nosiy也会导致车辆定位在这个范围漂移

xy_nosiy_range = 15
xy_nosiy_step = 5
deg_nosiy_range = 10
deg_nosiy_step = 2

#####################################################

# change range
# move_epsilon = 15
# deg_rot_epsilon = 15

# action monitor state
class ActionState(Enum):
    INIT = 0
    DOING = 1
    FINISH = 2

class ActionAnalysis(Enum):
    UNMOVABLE=0
    EXPECTABLE=1
    NOISY=2

    EMPTY = 3


#####################################################
# matplotlib.pyplot set
full_map = True
# windows size
plt_size = 5
font_size = 6
# part map size
partx = 700
party = 600
size = 400