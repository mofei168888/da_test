#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from app.ok_trade import *
except Exception as e:
    from ok_trade import *

class Trade_Strategy:

    def __init__(self):
        params = {'dif': 1.5,
                  'period': '5min',
                  'risk_rate': 0.5,
                  'amount': 10,
                  'symbol': 'eth_usdt',
                  'size': 120,
                  'point':0.5
                  }
        self._trader = OK_Trade(params)

    def get_trade_signal(self,symbol,period='1min',size = 60,contract_type='this_week'):
        '''
        追涨杀跌策略
        :param symbol:
        :param period:
        :param size:
        :param contract_type:
        :return:2 表示做多买入，1平掉做多，-2表示做空买入，-1表示平掉做空
         '''
        signal = 0
        self._trader.get_calculates_values()  # 获取最新的价格，并进行相应的计算
        #print(self._trader.new_price)
        # 当价格向上突破前五个交易单元的收盘价时，执行挂单做多
        if self._trader.new_price > np.amax(self._trader._buffer[-6:-2])+self._trader._params['point']:
            #print('(买入做多)当前价格;%s,五个交易单元高价:%s'%(self._trader._buffer[-1],np.amax(self._trader._buffer[-6:-2])))
            signal=2
        #当价格向下跌到前五个交易单元收盘高价时，平掉做多仓位止损
        if self._trader.new_price < np.amax(self._trader._buffer[-6:-2])-self._trader._params['point']*5:
            #print('(做多平仓)当前价格;%s,五个交易单元高价:%s' % (self._trader._buffer[-1], np.amax(self._trader._buffer[-6:-2])))
            signal =1

        # 当价格向下突破前五个交易单的收盘价时，执行挂单做空
        if self._trader.new_price < np.amin(self._trader._buffer[-6:-2])-self._trader._params['point']:
            #print('(买入做空)当前价格;%s,五个交易单元低价:%s' % (self._trader._buffer[-1],  np.amin(self._trader._buffer[-6:-2])))
            signal = -2
        # 当价格向上涨到前五个交易单元收盘低价时，平掉做空仓位止损
        if self._trader.new_price > np.amin(self._trader._buffer[-6:-2])+self._trader._params['point']*5:
            #print('(做空平仓)当前价格;%s,五个交易单元低价:%s' % (self._trader._buffer[-1], np.amin(self._trader._buffer[-6:-2])))
            signal = -1

        return signal

    def trade_system(self,symbol,period='1min',size = 60,contract_type='this_week'):
        orders = {}
        user_pos = self._trader.get_user_position(symbol)
        if user_pos['status']:
            signal = self.get_trade_signal(symbol,period,size,contract_type)
            if signal ==2:#做多交易信号
                if user_pos['buy_amount'] == 0:  # 没有做多持仓
                    buy_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['KD'],
                                                                           match_price=1, price=0.005,
                                                                           amount=self._trader._params['amount'])
                    if buy_order:
                        orders = buy_order
                        print('做多订单已下单(市价)：%s' % buy_order)
            if signal ==-2:#做空交易信号
                if user_pos['sell_amount'] == 0 :  # 没有做空持仓
                    sell_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['KK'],
                                                                            match_price=1, price=0.005,
                                                                            amount=self._trader._params['amount'])
                    if sell_order:
                        orders = sell_order
                        print('做空订单已下单(市价)：%s' % sell_order)

        return orders

    def stop_less_profit(self,symbol,period='1min',size = 60,contract_type='this_week'):
        orders={}
        user_pos = self._trader.get_user_position(symbol)
        if user_pos['status']:
            signal = self.get_trade_signal(symbol, period, size, contract_type)
            #price = self._trader.get_price_depth(symbol)
            #print('盘口:%s,%s'%(price[0],price[0]))
            #print('交易信号:%s'%signal)
            if signal==1:#将做多持仓平仓
                if user_pos['buy_amount'] > 0:
                    pd_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['PD'],
                                                                           match_price=1, price=0.005,
                                                                           amount=user_pos['buy_available'])
                    if pd_order:
                        orders = pd_order
                        print('做多平仓订单已下单(市价)：%s' % pd_order)
            if signal==2:#行情依然在上涨
                pass
            if signal==-1:#将做空持仓平仓
                if user_pos['sell_amount'] > 0:
                    pk_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['PK'],
                                                                          match_price=1, price=0.005,
                                                                          amount=user_pos['sell_available'])
                    if pk_order:
                        orders = pk_order
                        print('做空平仓订单已下单(市价)：%s' % pk_order)

            if signal==-2:#行情依然在下跌

        return orders


if __name__ == '__main__':
    ts = Trade_Strategy()
    while True:
        try:
            ts.trade_system('eth_usdt')
            ts.stop_less_profit('eth_usdt')
        except Exception as e:
            print('发生异常:%s'%e)
