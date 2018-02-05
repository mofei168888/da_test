#!/usr/bin/env python


try:
    from app.Logger import *
except Exception as e:
    from Logger import *

import pandas as pd
import datetime

class A:
    def __init__(self):
        print('A')

class B(A):
    def __init__(self):
        super(B,self).__init__()
        print("B")

if __name__ == '__main__':
    b = B()
    time = datetime.datetime.now()
    print(time)

