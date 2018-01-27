#!/usr/bin/env python

import numpy as np
import math
try:
    from app.ok_trade import *
except Exception as e:
    from ok_trade import *

class Analysis:

    def __init__(self):
        params = {'dif': 1.5}
        params = {'m5m10': 0.2}
        params = {'risk_rate': 0.5}
        params = {'amount': 2}

        self._ok_maker = OK_MAKER(params)
    def get_avg(self,symbol,period = 'ma5'):
        data ={}
        result = self._ok_maker.get_ma_data(symbol)
        if result['status']:
            data['avg'] = result['data'][period]
            data['price']=result['data']['price']
        return data

    def get_fc(self,symbol,period = 'ma5'):
        data = self.get_avg(symbol,period)
        print(data['price']-data['avg'])
        if data:
            fa =math.pow(data['price']-data['avg'],2)

        return fa


    def get_pd(self):
        pass

    def get_fd(self):
        pass



if __name__ == '__main__':
    fa = Analysis()
    result = fa.get_avg('eth_usdt')
    print(result)
    result = fa.get_fc('eth_usdt')
    print(result)


