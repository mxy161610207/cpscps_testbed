import trace
import sys
from importlib import reload

with open('user_register.py', 'w') as f:
    f.write('''
def run(a):
    a=2
    a=1
    b=5
    b=7
    print(a,b)
    ''')


import user_register
a = 2  # 初始化 a 变量
user_register.run(a)



with open('user_register.py', 'w') as f:
    f.write('''
def run(a):
    a=2
    b=5
    b=8
    print(a,b)
    ''')

reload(user_register)
user_register.run(a)

