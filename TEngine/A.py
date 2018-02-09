try:
    from app.trade_base import *
except Exception as e:
    from trade_base import *

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

if __name__== '__main__':
    tb = Trade_Base('ma_trade.json')
    df = tb.get_kline('1min',180)
    data = pd.DataFrame(df['data'])[::-1]
    print(data)

    '''
    
    fig = plt.figure(figsize=(12,8))
    ax1= fig.add_subplot(411)
    ax1.plot(label='price')
    data.plot(ax=ax1)

    #ax3 =fig.add_subplot(412)
    #dif =  pd.Series(tb.get_change_rate(df['data'])['dif'])[::-1]
    #dif = data.diff(1)
    #dif.plot(ax=ax3)

    ax2 =fig.add_subplot(412)
    #dif =  pd.Series(tb.get_change_rate(df['data'])['dif'])[::-1]
    dif = data.diff(1)
    dif.plot(ax=ax2)

    ax4 = fig.add_subplot(413)
    fig = sm.graphics.tsa.plot_acf(dif,lags=40,ax=ax4)

    ax5 = fig.add_subplot(414)
    fig = sm.graphics.tsa.plot_pacf(dif,lags=40,ax=ax5)

    plt.show()
    '''