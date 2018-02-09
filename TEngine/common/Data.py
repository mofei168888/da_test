

import pandas as pd

try:
    from app.trade_base import *
except Exception as e:
    from trade_base import *

class Data(object):
    def __init__(self):
        self.tb = Trade_Base('params.json')

    def get_data(self):
        df = self.tb.get_kline('1min', 2)
        data = pd.Series(df['data']['close'])[::-1]
        return data