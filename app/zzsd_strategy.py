#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime

try:
    from app.trade_base import *
except Exception as e:
    from trade_base import *

class zzsd_strategy(Trade_Base):

    def __init__(self,params_file):
        super(zzsd_strategy,self).__init__(params_file)

        #------------------------------------------#
        self._user_pos = {}
        self._depth_price = {}
        self._kline_data = {}
        #-----------------------------------------#
        self._user_cost = {}

        user_pos = self.get_user_position()
        if user_pos['status']:
            self._user_pos = user_pos
            self._log.log_info(self._user_pos)
            if self._user_pos['buy_amount'] > 0:
                self._user_cost['buy_cost'] = self._user_pos['buy_cost']
            else:
                self._user_cost['buy_cost'] = 0.0000

            if self._user_pos['sell_amount'] > 0:
                self._user_cost['sell_cost'] = self._user_pos['sell_cost']
            else:
                self._user_cost['sell_cost'] = 1000000.0000  # 给一个很大的值
            self._log.log_info('用户持仓成本:%s' % self._user_cost)

    def get_price_box(self, period, nums):
        '''
        #获取箱体最高价格和最低价格
        :param period: 表示时间周期，如:1min,5min
        :param nums: 获取多少个时间周期的数据
        :return: 返回箱体最高价格和最低价格
        '''
        price_box = {}
        kline = self.get_kline(period, nums)
        if kline['status']:
            pl = pd.concat([kline['data']['open'][1:], kline['data']['close'][1:]], axis=0)
            price_box['high'] = float("%.04f" % pl.max())
            price_box['low'] = float("%.04f" % pl.min())

        price_box['kline'] = kline['data']  # 将获取的K线数据直接保存起来，不用再去获取一遍

        return price_box

    def get_updated_price(self,period,nums):
        self._depth_price = {}
        self._kline_data = {}
        self._user_pos = {}

        #-----获取交易深度数据------#
        depth_price = self.get_price_depth()
        if depth_price['status']:
            self._depth_price = depth_price
            self._log.log_debug('交易深度:%s'%self._depth_price)

        #------获取K线数据-------#
        price_box = self.get_price_box(period, nums)
        if price_box:
            dif_data = self.get_change_rate(price_box['kline'])
            price_box['kline'] = dif_data
            price_box['mean'] = dif_data['dif'].mean()  # 获取K线涨跌幅平均值
            price_box['std'] = dif_data['dif'].std() # 获取K线涨跌幅标准差
            price_box['skew'] = dif_data['dif'].skew() # 获取K线涨跌幅偏度
            price_box['kurt'] = dif_data['dif'].kurt() # 获取K线涨跌幅峰度
            self._kline_data = price_box
            self._log.log_debug('箱体高点:%s,箱体低点:%s' % (self._kline_data['high'], self._kline_data['low']))
            self._log.log_debug("K线平均值:%s,标准差:%s,偏度:%s,峰度:%s" % (self._kline_data['mean'], self._kline_data['std'], self._kline_data['skew'], self._kline_data['kurt']))
        #----获取用户持仓数据--------#
        user_pos = self.get_user_position()
        if user_pos['status']:
            self._user_pos = user_pos
            if self._user_pos['buy_amount'] > 0:  # 拥有做多持仓，然后再更新成本信息
                buy_price = []
                buy_price.append(self._depth_price['buy'])
                buy_price.append(self._user_cost['buy_cost'])
                if len(buy_price) == 2:
                    self._user_cost['buy_cost'] = np.amax(buy_price)  # 更新成本价格
            if self._user_pos['sell_amount'] > 0:  # 拥有做空持仓，然后再更新成本信息
                sell_price = []
                sell_price.append(self._depth_price['sell'])
                sell_price.append(self._user_cost['sell_cost'])
                if len(sell_price) == 2:
                    self._user_cost['sell_cost'] = np.amin(sell_price)  # 更新成本价格
                    self._log.log_debug(self._user_cost)

    #--------------------------交易模型--------------------------------#
    def get_kc_signal(self,period,nums):
        '''
        根据箱体突破法，将深度买一价格，卖一价格与箱体价格进行对比，识别做多信号和做空信号
        简单的箱体突法，无法识别当前行情状态，增值如下分析方法：
        1. 加入前几个时间周期涨跌幅度的统计分析  激烈震荡下的箱体突破，容易产生假突破。使用统计分析将其过滤掉
        :param period: 时间周期,如:1min,5min
        :param nums: 多少个时间周期数
        :return: 1,表示做多信号，-1表示做空交易信号，0不操作
        '''
        #-------------获取数据------------------#
        signal=0
        self.get_updated_price(period,nums)
        #------------执行计算------------------#
        if self._kline_data and self._depth_price and self._user_pos:#获取箱体价格,交易深度价格,用户持仓数据
            if abs(self._kline_data['mean'])< 1.5 and self._kline_data['std'] <8 and self._kline_data['kurt'] <2:   #表示行情稳定，稳定下的突破才是有效的突破
                if self._depth_price['buy'] - self._kline_data['high'] > self._params['point'] and self._user_pos['buy_amount']==0:#价格向上突破箱体，并且没有持仓
                    signal = 1
                elif self._kline_data['low'] - self._depth_price['sell'] > self._params['point'] and self._user_pos['sell_amount']==0:#价格向下突破箱体，并且没有持仓
                    signal = -1

        return signal

    def trade_kc(self,period,nums):
        orders = {}
        signal = self.get_kc_signal(period,nums)
        if signal == 1:  # 做多交易信号
            orders = self.send_kc_order(order_type=OK_ORDER_TYPE['KD'], order_price=0.0000, match_price=1,cancel_ys=False)
        if signal == -1:  # 做空交易信号
            orders = self.send_kc_order(order_type=OK_ORDER_TYPE['KK'], order_price=0.0000, match_price=1,cancel_ys=False)

        return orders

    def get_pc_signal(self,period,nums):
        signal =0
        self.get_updated_price(period, nums)
        if self._user_cost['buy_cost'] - self._depth_price['buy'] > self._params['lose'] and self._user_pos['buy_amount']!=0:
            self._log.log_info('做多开仓价格:%s,平仓价格:%s,百分比;%s' % (self._user_pos['buy_cost'], self._depth_price['buy'],
                                                                (self._user_pos['buy_cost']-self._depth_price['buy'])/self._user_pos['buy_cost'] *100*20))
            signal = 1 #发出做多平仓信号

        if self._depth_price['sell'] - self._user_cost['sell_cost'] >self._params['lose'] and self._user_pos['sell_amount']!=0:
            self._log.log_info('做空开仓价格:%s,平仓价格:%s,百分比:%s'%(self._user_pos['sell_cost'],self._depth_price['sell'],
                                                              (self._user_pos['sell_cost']-self._depth_price['sell'])/self._user_pos['sell_cost'] *100*20))
            signal = -1  # 发出做空平仓信号

        return signal

    def trade_pc(self,period,nums):
        orders = {}
        signal = self.get_pc_signal(period,nums)
        if signal == 1:
            orders = self.send_pc_order(order_type=OK_ORDER_TYPE['PD'], order_price=0, match_price=1,cancel_ys=True)
        if signal == -1:
            orders = self.send_pc_order(order_type=OK_ORDER_TYPE['PK'], order_price=0, match_price=1,cancel_ys=True)

        return orders

if __name__== '__main__':
    zs = zzsd_strategy('params.json')
    zs.set_log_file(logging.INFO,'20180205.log')
    zs.set_LogLevel(logging.INFO)
    while True:
        try:
            zs.trade_kc('5min',6)
            zs.trade_pc('5min',6)
        except Exception as e:
            print('发生异常错误:%s'%e)


