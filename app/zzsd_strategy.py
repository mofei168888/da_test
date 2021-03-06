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

        user_pos = self.get_user_position()
        if user_pos['status']:
            self._user_pos = user_pos

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
            pl = pd.concat([kline['data']['high'][1:], kline['data']['low'][1:]], axis=0)
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
        if self._depth_price['buy'] - self._kline_data['high'] > self._params['point'] and self._user_pos['buy_amount']==0:#价格向上突破箱体，并且没有持仓
             signal = 1
        elif self._kline_data['low'] - self._depth_price['sell'] > self._params['point'] and self._user_pos['sell_amount']==0:#价格向下突破箱体，并且没有持仓
             signal = -1

        return signal

    def trade_kc(self,period,nums):
        orders = {}
        signal = self.get_kc_signal(period,nums)
        if signal == 1:  # 做多交易信号
            orders = self.send_kc_order(order_type=OK_ORDER_TYPE['KD'], order_price=0.0000, match_price=1,cancel_ys=True)
        if signal == -1:  # 做空交易信号
            orders = self.send_kc_order(order_type=OK_ORDER_TYPE['KK'], order_price=0.0000, match_price=1,cancel_ys=True)

        return orders

    def get_pc_signal(self,period,nums):
        signal =0
        self.get_updated_price(period, nums)

        #if abs(self._kline_data['mean']) < 2 and self._kline_data['std'] < 5 and self._kline_data['kurt'] < 2:
        if self._user_pos['buy_cost'] - self._depth_price['buy'] > self._params['lose'] and self._user_pos['buy_amount']!=0:
           signal = 1 #发出做多平仓信号

        if self._depth_price['sell'] - self._user_pos['sell_cost'] >self._params['lose'] and self._user_pos['sell_amount']!=0:
           signal = -1  # 发出做空平仓信号

        return signal

    def set_profit_win(self,period,nums):
        orders = {}
        if self._user_pos['buy_available']>0:
            orders = self.send_pc_order(order_type=OK_ORDER_TYPE['PD'],
                                        order_price=self._user_pos['buy_cost']+self._params['profit'],
                                        match_price=0, cancel_ys=False)
        if self._user_pos['sell_available']>0:
            orders = self.send_pc_order(order_type=OK_ORDER_TYPE['PK'],
                                        order_price=self._user_pos['sell_cost']-self._params['profit'],
                                        match_price=0, cancel_ys=False)
        return orders

    def trade_pc(self,period,nums):
        orders = {}
        signal = self.get_pc_signal(period,nums)
        if signal == 1:
            orders = self.send_pc_order(order_type=OK_ORDER_TYPE['PD'], order_price=0, match_price=1,cancel_ys=True)
            if orders:
                self._log.log_info('做多开仓价格:%s,平仓价格:%s,百分比;%s' % (self._user_pos['buy_cost'], self._depth_price['buy'],
                                                                 (self._depth_price['buy'] - self._user_pos[
                                                                     'buy_cost']) / self._user_pos[
                                                                     'buy_cost'] * 100 * 20))
        if signal == -1:
            orders = self.send_pc_order(order_type=OK_ORDER_TYPE['PK'], order_price=0, match_price=1,cancel_ys=True)
            if orders:
                self._log.log_info('做空开仓价格:%s,平仓价格:%s,百分比:%s' % (self._user_pos['sell_cost'], self._depth_price['sell'],
                                                                 (self._user_pos['sell_cost'] - self._depth_price[
                                                                     'sell']) / self._user_pos['sell_cost'] * 100 * 20))
        return orders

def main():
    zs = zzsd_strategy('params.json')
    logfile = datetime.datetime.now().strftime('%Y%m%d%H%M')
    zs.set_log_file(logging.INFO, logfile + '.log')
    zs.set_LogLevel(logging.ERROR)
    period = zs._params['period']
    nums = zs._params['p_nums']
    waitingFlag = False
    # --------------------------星期五下午2点后，暂停执行，到交割之后，重新执行--------#
    while True:
        dt = datetime.datetime.now()
        friday = dt.strftime('%w')
        time = dt.strftime('%H%M')
        if int(friday) == 5 and int(time) < 1700 and int(time) > 1400:  # 表示星期五,下午2点,暂停5点开始执行
            waitingFlag =True
        else:
            waitingFlag = False
        #-----------------------------------------------------------------------------#
        while waitingFlag==False: #
            try:
                zs.trade_kc(period, nums)
                zs.set_profit_win(period, nums)  # 增加止赢
                zs.trade_pc(period, nums)
            except Exception as e:
                zs._log.log_error('发生异常:%s' % e)

if __name__== '__main__':
    main()




