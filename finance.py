#!/usr/bin/env python

import numpy as np
import math
try:
    from app.ok_trade import *
except Exception as e:
    from ok_trade import *

if __name__ == '__main__':
   a = [2,2,3,4,7]
   result = np.percentile(a,100)
   print(result)

