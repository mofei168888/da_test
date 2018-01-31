#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from app.ok_trade import *
    from app.Logger import *
except Exception as e:
    from ok_trade import *
    from Logger import *

class Trade_Strategy:

    def __init__(self):
        params ={}
        # Windows will be : Windows
        # Linux will be : Linux
        if platform.system() == 'Windows':
            with open("D:\config\params.json",'r') as fr:
                params = json.load(fr)
        if platform.system() == 'Linux':
            with open("/home/params.json",'r') as fr:
                params = json.load(fr)
        self._trader = OK_Trade(params)
        self._last_pc_price={}

        self._last_pc_price['buy'] = self._trader._user_cost['buy_cost']#将当前成本价格初始最新平仓价格
        self._last_pc_price['sell'] = self._trader._user_cost['sell_cost']#将当前成本价格初始最新平仓价格

        self._log = Logger('ok.strategy.zzsd',logging.DEBUG)

    def set_log_level(self):
        relog = logging.getLogger('requests.packages.urllib3.connectionpool')
        relog.setLevel(logging.ERROR)
        trade_log = logging.getLogger('ok.strategy.zzsd')
        trade_log.setLevel(logging.DEBUG)

    def stop_less_profit(self,symbol,period='1min',size = 60,contract_type='this_week'):
        orders={}
        user_pos = self._trader.get_user_position(symbol)
        if user_pos['status']:
            price = self._trader.get_price_depth(symbol)
            new_buy = self._trader._new_price
            new_sell = self._trader._new_price

            #执行利润收割，减少回撤,止赢,保持利润,每10个点收割一次
            if user_pos['buy_amount'] > 0:#表示持有做多头寸
                if new_buy - user_pos['buy_cost'] < self._trader._params['lose']:#执行做多订单止损
                    #print('盘口价格:%s,成本价:%s,价格差异：%s,止损点位:%s'%(new_buy,user_pos['buy_cost'],new_buy - user_pos['buy_cost'],self._trader._params['lose']))
                    pd_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['PD'],
                                                                          match_price=1, price=0.005,
                                                                          amount=user_pos['buy_available'])
                    if pd_order:
                        orders = pd_order
                        print('做多止损订单已下单(市价)：%s' % pd_order)
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
                        print('做空止损订单已下单(市价)：%s' % pk_order)
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

    def move_lose_profit(self,symbol,period='1min',size = 60,contract_type='this_wek'):
        orders={}
        user_pos = self._trader.get_user_position(symbol)
        if user_pos['status']:
            self._trader.get_calculates_values()#更新价格
            if user_pos['buy_amount'] > 0:  # 表示持有做多头寸
                price_list=[]
                price_list.append(self._trader._new_price)
                price_list.append(self._trader._user_cost['buy_cost'])
                if len(price_list)==2:
                    self._trader._user_cost['buy_cost'] = np.amax(price_list)  # 更新最新价格
                wt_orders = self._trader.get_wt_orders(symbol)

                if OK_ORDER_TYPE['PD'] in wt_orders['type_list']:#表示有委托订单.
                    for order in wt_orders['orders']:
                        if order['type'] == OK_ORDER_TYPE['PD']:  # 表示平多未成交，摊销未成交订单
                            self._log.log_error(order)
                            if order['price']< self._trader._user_cost['buy_cost']-self._trader._params['lose']:#挂单价格小于最新价格
                                cancel_order = self._trader._OKServices.cancel_future_order(symbol, order['order_id'])
                                if cancel_order:  # 撤销订单成功 #执行移动止损，将止损挂单价格向上移动
                                    pd_order = self._trader._OKServices.send_future_order(symbol=symbol,
                                                                                  type=OK_ORDER_TYPE['PD'],
                                                                                  match_price=0,
                                                                                  price=self._trader._user_cost['buy_cost']+self._trader._params['lose'],
                                                                                  amount=user_pos['buy_available'])
                                    if pd_order:
                                        orders = pd_order
                                        self._log.log_info('设置做多止损(挂单)：%s' % pd_order)
                else:#表示没有委托订单
                    pd_order = self._trader._OKServices.send_future_order(symbol=symbol,
                                                                          type=OK_ORDER_TYPE['PD'],
                                                                          match_price=0,
                                                                          price=self._trader._user_cost['buy_cost'] +
                                                                                self._trader._params['lose'],
                                                                          amount=user_pos['buy_available'])
                    if pd_order:
                        orders = pd_order
                        self._log.log_info('设置做多止损(挂单)2：%s' % pd_order)

            if user_pos['sell_amount'] > 0:#表示持有做空头寸
                price_list = []
                price_list.append(self._trader._new_price)
                price_list.append(self._trader._user_cost['sell_cost'])
                if len(price_list)==2:
                    self._trader._user_cost['sell_cost'] = np.amin(price_list)  # 更新最新价格
                wt_orders = self._trader.get_wt_orders(symbol)

                self._log.log_info('New Cost：%s,需要设置的止损价格:%s'%(self._trader._user_cost['sell_cost'],self._trader._user_cost['sell_cost'] -
                                                                                self._trader._params['lose']))

                if OK_ORDER_TYPE['PK'] in wt_orders['type_list']:#存在平空委托订单，将平空委托订单撤销
                    for order in wt_orders['orders']:
                        if order['type'] == OK_ORDER_TYPE['PK']:  # 表示平多未成交，摊销未成交订单，执行市价成交

                            if order['price'] > self._trader._user_cost['sell_cost']+self._trader._params['lose']:#当委托价格大于最新价格时，向下移动
                                cancel_order = self._trader._OKServices.cancel_future_order(symbol, order['order_id'])
                                if cancel_order:  # 撤销订单成功
                                    pk_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['PK'],
                                                                                  match_price=0,
                                                                                  price=self._trader._user_cost['sell_cost']-self._trader._params['lose'],
                                                                                  amount=user_pos['sell_available'])
                                    if pk_order:
                                        orders = pk_order
                                        self._log.log_info('设置做空移动止损(挂单)1：%s' % pk_order)
                else:#表示没有委托订单

                    pk_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['PK'],
                                                                          match_price=0,
                                                                          price=self._trader._user_cost['sell_cost'] -
                                                                                self._trader._params['lose'],
                                                                          amount=user_pos['sell_available'])#
                    if pk_order:
                        orders = pk_order
                        self._log.log_info('可平仓量：%s'%user_pos['sell_available'])
                        self._log.log_info('设置做空移动止损(挂单)2：%s' % pk_order)

        return orders

    def send_pc_order(self,symbol,order_type,order_price,match_price=0,cancel_ys=False):
        orders={}
        user_pos = self._trader.get_user_position(symbol)
        pc_qty = 0
        if user_pos['status']:
            wt_orders = self._trader.get_wt_orders(symbol)
            if order_type in wt_orders['type_list'] and cancel_ys:  # 有委托订单，并且执行撤销
                for order in wt_orders['orders']:
                    if order['type'] == order_type:  # 表示平多未成交，摊销未成交订单
                        self._log.log_error(order)
                        cancel_order = self._trader._OKServices.cancel_future_order(symbol, order['order_id'])
                        if cancel_order:  # 撤销订单成功 #执行移动止损，将止损挂单价格向上移动
                            self._log.log_info('订单撤销成功:%s'%cancel_order)

            if order_type==OK_ORDER_TYPE['PD']:
                pc_qty = user_pos['buy_available']

            elif order_type==OK_ORDER_TYPE['PK']:
                pc_qty = user_pos['sell_available']

            if pc_qty>0:
                pc_order = self._trader._OKServices.send_future_order(symbol=symbol,type=order_type,match_price=match_price,
                                                                      price=order_price,amount=pc_qty)
                if pc_order:
                    orders = pc_order
                    self._log.log_info('平仓订单已下单%s：%s' %(match_price, pc_order))

        return orders
    #-----------------------------------------------------------------------------------------------------#
    def get_kc_signal(self):
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
        # 当价格向上突破前六个交易单元的收盘价时，执行挂单做多

        if np.amax(self._trader._buffer[-7:-1]) - np.amin(self._trader._buffer[-7:-1]) <self._trader._params['space']:#市场震荡空间很小，不下单
            self._log.log_debug('震荡区间太小，不执行下单操作')
        else:##市场震荡空间满足条件，才执行操作
            if self._trader._new_price > np.amax(self._trader._buffer[-7:-1])+self._trader._params['point']:
                self._log.log_debug('当前价格;%s,六个交易单元高价:%s,低价:%s,震荡区间:%s,条件区间:%s' % (self._trader._new_price,
                                                                                   np.amax(self._trader._buffer[-7:-1]),
                                                                                   np.amin(self._trader._buffer[-7:-1]),
                                                                                   np.amax(self._trader._buffer[
                                                                                           -7:-1]) - np.amin(
                                                                                       self._trader._buffer[-7:-1]),
                                                                                   self._trader._params['space']
                                                                                   ))
                signal=1
            # 当价格向下突破前六个交易单元的收盘价时，执行挂单做空
            if self._trader._new_price < np.amin(self._trader._buffer[-7:-1])-self._trader._params['point']:
                self._log.log_debug('当前价格;%s,六个交易单元高价:%s,低价:%s,震荡区间:%s,条件区间:%s' % (self._trader._new_price,
                                                                                   np.amax(self._trader._buffer[-7:-1]),
                                                                                   np.amin(self._trader._buffer[-7:-1]),
                                                                                   np.amax(self._trader._buffer[
                                                                                           -7:-1]) - np.amin(
                                                                                       self._trader._buffer[-7:-1]),
                                                                                   self._trader._params['space']
                                                                                   ))
                signal = -1


        return signal

    def trade_kc(self,symbol,period='1min',size = 60,contract_type='this_week'):
        orders = {}
        user_pos = self._trader.get_user_position(symbol)
        if user_pos['status']:
            signal = self.get_kc_signal()
            if signal ==1:#做多交易信号
                if user_pos['buy_amount'] == 0:  # 没有做多持仓
                    buy_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['KD'],
                                                                           match_price=1, price=0.005,
                                                                           amount=self._trader._params['amount'])
                    if buy_order:
                        orders = buy_order
                        self._log.log_info('做多订单已下单(市价)：%s' % buy_order)
            if signal ==-1:#做空交易信号
                if user_pos['sell_amount'] == 0 :  # 没有做空持仓
                    sell_order = self._trader._OKServices.send_future_order(symbol=symbol, type=OK_ORDER_TYPE['KK'],
                                                                            match_price=1, price=0.005,
                                                                            amount=self._trader._params['amount'])
                    if sell_order:
                        orders = sell_order
                        self._log.log_info('做空订单已下单(市价)：%s' % sell_order)

        return orders

    def get_pc_signal(self):
        signal = 0
        self._trader.get_calculates_values()

        self._log.log_debug('当前最新价格;%s,做多止损价格:%s,做空止损价格:%s' % (self._trader._new_price,
                                                               self._trader._stop_price['buy_price'],
                                                               self._trader._stop_price['sell_price']))
        if self._trader._new_price < self._trader._stop_price['buy_price'] and self._trader._user_cost['buy_cost']!=0:
            self._trader._buffer.append(self._trader._user_cost['buy_cost'])
            self._log.log_debug('最新高价：%s,Buffer长度:%s'%(self._trader._buffer[-1],len(self._trader._buffer)))
            self._log.log_debug('最近6个交易单元收盘价:%s' % (self._trader._buffer[-7:-1]))
            signal = 1 #发出做多平仓信号

        if self._trader._new_price > self._trader._stop_price['sell_price'] and self._trader._user_cost['sell_cost']!=0:
            self._trader._buffer.append(self._trader._user_cost['sell_cost'])
            self._log.log_debug('最新低价：%s,Buffer长度:%s' % (self._trader._buffer[-1], len(self._trader._buffer)))
            self._log.log_debug('最近6个交易单元收盘价:%s' % (self._trader._buffer[-7:-1]))
            signal = -1  # 发出做空平仓信号

        return signal

    def trade_pc(self,symbol,period='1min',size = 60,contract_type='this_wek'):
        signal = self.get_pc_signal()

        if signal==1:
            self._log.log_debug('平仓交易信号:%s' % signal)
            self.send_pc_order(symbol=symbol,order_type=OK_ORDER_TYPE['PD'],order_price=0,match_price=1,
                               cancel_ys=True)
        if signal ==-1:
            self._log.log_debug('平仓交易信号:%s' % signal)
            self.send_pc_order(symbol=symbol, order_type=OK_ORDER_TYPE['PK'], order_price=0, match_price=1,
                               cancel_ys=True)

if __name__ == '__main__':
    ts = Trade_Strategy()
    ts.set_log_level()
    log = Logger('main',logging.ERROR)
    zlog = logging.getLogger('ok.strategy.zzsd')
    tlog = logging.getLogger('ok.trade')
    tlog.setLevel(logging.ERROR)
    zlog.setLevel(logging.DEBUG)
    while True:
        try:
            ts.trade_kc('eth_usdt')
            ts.trade_pc('eth_usdt')
        except Exception as e:
            log.log_warning('发生系统异常;%s'%e)
