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
                  'amount': 2,
                  'symbol': 'eth_usdt',
                  'size': 120,
                  'point':0.1,
                  'profit':8,
                  'lose':2
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
            print('(买入做多)当前价格;%s,五个交易单元高价:%s'%(self._trader._buffer[-1],np.amax(self._trader._buffer[-6:-2])))
            signal=2

        # 当价格向下突破前五个交易单的收盘价时，执行挂单做空
        if self._trader.new_price < np.amin(self._trader._buffer[-6:-2])-self._trader._params['point']:
            print('(买入做空)当前价格;%s,五个交易单元低价:%s' % (self._trader._buffer[-1],  np.amin(self._trader._buffer[-6:-2])))
            signal = -2

        return signal

    def trade_system(self,symbol,period='1min',size = 60,contract_type='this_week'):
        orders = {}
        user_pos = self._trader.get_user_position(symbol)
        if user_pos['status']:
            signal = self.get_trade_signal(symbol,period,size,contract_type)
            print('交易信号：%s'%signal)
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
            price = self._trader.get_price_depth(symbol)
            new_buy = self._trader.new_price
            new_sell = self._trader.new_price
            if price[0]!=0:#表示取到数据
                new_buy = price[0]
            if price[1]!=0:#表示取到数据
                new_sell = price[1]
            #执行利润收割，减少回撤,止赢,保持利润,每10个点收割一次
            if user_pos['buy_amount'] > 0:#表示持有做多头寸
                if new_buy - user_pos['buy_cost'] < self._trader._params['lose']:#执行做多订单止损
                    pd_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['PD'],
                                                                          match_price=1, price=0.005,
                                                                          amount=user_pos['buy_available'])
                    if pd_order:
                        orders = pd_order
                        print('做多平仓订单已下单(市价)：%s' % pd_order)
                if new_buy - user_pos['buy_cost'] >self._trader._params['profit']:#执行做多订单止赢
                    pd_amount = int(user_pos['buy_available'] * 0.2)
                    if pd_amount < 1:
                        pd_amount = user_pos['sell_available']

                    pd_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['PD'],
                                                                          match_price=1, price=0.005,
                                                                          amount=pd_amount)
                    if pd_order:
                        orders = pd_order
                        print('做多平仓订单已下单(市价)：%s' % pd_order)

            if user_pos['sell_amount'] > 0:#表示持有做空头寸
                if user_pos['sell_cost'] - new_sell < self._trader._params['lose']:#做空头寸止损

                    pk_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['PK'],
                                                                          match_price=1, price=0.005,
                                                                          amount=user_pos['sell_available'])
                    if pk_order:
                        orders = pk_order
                        print('做空平仓订单已下单(市价)：%s' % pk_order)
                if user_pos['sell_cost'] - new_sell>self._trader._params['profit']:#做空头寸止赢
                    pk_amount = int(user_pos['sell_available'] * 0.2)
                    if pk_amount < 1:
                        pk_amount = user_pos['sell_available']
                    pk_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['PK'],
                                                                          match_price=1, price=0.005,
                                                                          amount=pk_amount)
                    if pk_order:
                        orders = pk_order
                        print('做空平仓订单已下单(市价)：%s' % pk_order)

        return orders


if __name__ == '__main__':
    ts = Trade_Strategy()
    while True:
        try:
            ts.trade_system('eth_usdt')
            ts.stop_less_profit('eth_usdt')
        except Exception as e:
            print('发生异常:%s'%e)
