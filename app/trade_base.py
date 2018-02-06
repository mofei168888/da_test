#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from app.OK_Services import *
    from app.Logger import *
except Exception as e:
    from OK_Services import *
    from Logger import *

import pandas as pd
import datetime
import time
import numpy as np

class Trade_Base:

    def __init__(self,params_file):
        self._log = Logger('ok.trade_base')
        self._log.set_log_level(logging.DEBUG)
        self._OKServices = Ok_Services()
        self._params = {}
        self._file_path=""
        self._platform = platform.system()
        # Windows will be : Windows
        # Linux will be : Linux
        file_name = ""
        if self._platform == 'Windows':
            self._file_path = "D:\config"
            file_name= self._file_path+"\{}".format(params_file)
        elif self._platform == 'Linux':
            self._file_path = "/home"
            file_name = self._file_path + "/{}".format(params_file)
            #file_name = "/home/{}".format(params_file)
        with open(file_name, 'r') as fr:
            self._params = json.load(fr)

        self._log.log_info(self._params)

    def set_log_file(self,level,file_name):
        path_name=""
        if self._platform == 'Windows':
            path_name= self._file_path+"\log\{}".format(file_name)
        elif self._platform == 'Linux':
            path_name = self._file_path + "/log/{}".format(file_name)

        self._log.log_debug(path_name)
        self._log.set_log_file(level,path_name)

    def set_LogLevel(self,type):
        self._log.set_log_level(type)

    def get_price_depth(self):
        '''
        #获取市场行情深度
        :param symbol:
        :return:
        '''
        result={}
        result['status']=False
        try:
            data = self._OKServices.get_future_depth(self._params['symbol'])
            result['sell'] = data['asks'][-1][0]
            result['buy']= data['bids'][0][0]
            result['status'] = True
            #print(result['asks'][-5:-1])
            #print(result['bids'][0:5])
        except Exception as e:
            self._log.log_error('network error:%s'%e)
            result['status'] = False
        return result

    def get_user_position(self,contract_type='this_week'):
        '''
        #获取仓位信息
        :param symbol:btc_usdt   ltc_usdt    eth_usdt    etc_usdt    bch_usdt
        :param contract_type:
        :return:
        '''
        result = {}
        result['status'] = False
        hold = self._OKServices.get_future_position(self._params['symbol'], contract_type)
        # print(hold)
        if hold:
            result['buy_amount'] = hold['holding'][0]['buy_amount']
            result['buy_available'] = hold['holding'][0]['buy_available']
            result['buy_cost'] = hold['holding'][0]['buy_price_cost']
            result['sell_amount'] = hold['holding'][0]['sell_amount']
            result['sell_available'] = hold['holding'][0]['sell_available']
            result['sell_cost'] = hold['holding'][0]['sell_price_cost']
            result['status'] = True
        else:
            result['status'] = False

        return result

    def get_ma_data(self, symbol, period='1min', size=60, contract_type='this_week'):

        data = {}
        data['status'] = False
        ma = {}
        sum_5 = 0.0000
        sum_10 = 0.0000
        sum_15 = 0.0000
        sum_30 = 0.0000
        sum_60 = 0.0000
        try:
            result = self._OKServices.get_future_kline(symbol, period, size, contract_type)
            if result:
                for i in range(0, size):
                    if i < 5:
                        sum_5 = sum_5 + result[-1 - i][4]
                    if i < 10:
                        sum_10 = sum_10 + result[-1 - i][4]
                    if i < 15:
                        sum_15 = sum_15 + result[-1 - i][4]
                    if i < 30:
                        sum_30 = sum_30 + result[-1 - i][4]
                    if i < 60:
                        sum_60 = sum_60 + result[-1 - i][4]

                ma['price'] = round(result[-1][4], 4)
                ma['ma5'] = round(sum_5 / 5, 4)
                ma['ma10'] = round(sum_10 / 10, 4)
                ma['ma15'] = round(sum_15 / 15, 4)
                ma['ma30'] = round(sum_30 / 30, 4)
                ma['ma60'] = round(sum_60 / 60, 4)
                data['status'] = True
                data['data'] = ma
        except Exception as e:
            data['status'] = False

        return data

    def get_wt_orders(self):
        return_data={}
        wt_type = []
        wt_orders = self._OKServices.get_future_order(symbol=self._params['symbol'], order_id=-1)
        if wt_orders:
            for order in wt_orders['orders']:
                wt_type.append(order['type'])

            return_data['orders']=wt_orders['orders']
        return_data['type_list']=wt_type

        return return_data  # 返回用户委托订单类型

    def get_kline(self,period,nums):
        result={}
        result['status']=False
        result['data'] = None
        data=[]
        try:
            data = self._OKServices.get_future_kline(self._params['symbol'], period, nums)
        except Exception as e:
            self._log.log_error('网络异常错误:%s'%e)
        if data:
            df = pd.DataFrame(data,columns=['time', 'open', 'high', 'low', 'close', 'vol', 'btc_amount'])
            result['status'] = True
            result['data'] = df.sort_values(by='time', ascending=False).set_index(['time']).reset_index()
        else:
            result['status'] = False
            result['data'] =None

        return result

    def get_ticker(self):
        pass

    def send_pc_order(self,order_type,order_price,match_price=0,cancel_ys=False):
        orders={}
        user_pos = self.get_user_position()
        pc_qty = 0
        if user_pos['status']:
            wt_orders = self.get_wt_orders()
            if order_type in wt_orders['type_list'] and cancel_ys:  # 有委托订单，并且执行撤销
                for order in wt_orders['orders']:
                    if order['type'] == order_type:  # 表示平多未成交，摊销未成交订单
                        self._log.log_debug(order)
                        cancel_order = self._OKServices.cancel_future_order(self._params['symbol'], order['order_id'])
                        if cancel_order:  # 撤销订单成功 #执行移动止损，将止损挂单价格向上移动
                            self._log.log_debug('订单撤销成功:%s'%cancel_order)

            if order_type==OK_ORDER_TYPE['PD']:
                pc_qty = user_pos['buy_available']

            elif order_type==OK_ORDER_TYPE['PK']:
                pc_qty = user_pos['sell_available']

            if pc_qty>0:
                pc_order = self._OKServices.send_future_order(symbol=self._params['symbol'],type=order_type,match_price=match_price,
                                                                      price=order_price,amount=pc_qty)
                if pc_order:
                    orders = pc_order
                    self._log.log_debug('平仓订单已下单%s：%s' %(match_price, pc_order))
                    time.sleep(60)

        return orders

    def send_kc_order(self,order_type,order_price,match_price=0,cancel_ys=False):
        orders = {}
        wt_orders = self.get_wt_orders()
        if order_type in wt_orders['type_list'] and cancel_ys:  # 有委托订单，并且执行撤销
            for order in wt_orders['orders']:
                if order['type'] == order_type:  # 表示开仓订单未成交，摊销未成交订单
                   self._log.log_debug(order)
                   cancel_order = self._OKServices.cancel_future_order(self._params['symbol'], order['order_id'])
                   if cancel_order:  # 撤销订单成功
                       self._log.log_debug('订单撤销成功:%s' % cancel_order)
                       time.sleep(30)
        kc_order = self._OKServices.send_future_order(symbol=self._params['symbol'], type=order_type,
                                                                      match_price=match_price,
                                                                      price=order_price,
                                                                      amount=self._params['amount'])
        if kc_order:
            orders = kc_order
            self._log.log_debug('开仓订单已下单%s：%s' % (match_price, kc_order))


        return orders

    def cancel_orders(self,order_type):
        orders=[]
        wt_orders = self.get_wt_orders()
        if order_type in wt_orders['type_list']:  # 有委托订单，并且执行撤销
            for order in wt_orders['orders']:
                if order['type'] == order_type:  # 表示平多未成交，摊销未成交订单
                    self._log.log_debug(order)
                    cancel_order = self._OKServices.cancel_future_order(self._params['symbol'], order['order_id'])
                    if cancel_order:  # 撤销订单成功 #执行移动止损，将止损挂单价格向上移动
                        orders.append(cancel_order)
                        self._log.log_info('订单撤销成功:%s' % cancel_order)

        return orders

    def get_time(self,un_time):
        un_time = un_time/1000
        return datetime.datetime.fromtimestamp(un_time)

    def make_un_time(self,dtime):

        return time.mktime(dtime.timetuple())*1000

    def get_change_rate(self,df):
        new_df = pd.DataFrame(df['close']-df['open'],columns=['dif'])
        dif_df = pd.concat([df,new_df],axis=1)

        return dif_df



if __name__ == '__main__':
    tb = Trade_Base('ma_trade.json')
    tb.set_log_file(logging.WARNING,'20180201.log')






