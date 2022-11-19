from http.client import NON_AUTHORITATIVE_INFORMATION
import os
from enum import Enum

##### global variable ####
SERVER_IP = '127.0.0.1'
OUTPUT_DIR = os.path.dirname(os.path.realpath(__file__))+'/log/'
os.makedirs(os.path.dirname(OUTPUT_DIR), exist_ok=True)

CALC_LOG=None
if (CALC_LOG is None):
    CALC_LOG=open(OUTPUT_DIR+"calc_detail.txt","w")


class SystemState(Enum):
    NORMAL = 0
    LOSS = 1
    ADJUST = 2
    INIT = 3

##### preprocessing

# print(OUTPUT_DIR)
try:
    os.mkdir(OUTPUT_DIR)
except Exception as e:
    if (e.args[0]==17):
        pass
    else:
        raise RuntimeError(e)
