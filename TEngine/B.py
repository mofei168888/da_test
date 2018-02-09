#!/usr/bin/env python
# -*- coding: utf-8 -*-


class B:
    def initialize(self):
        self.account.balance = 1000
        self.account.order_amount = 1
        print('用户余额：%s, 下单金额:%s'%(self.account.balance,self.account.order_amount))

    def handle_data(self):
        price = self.data.get_data()[0]
        self.order.buy('01',self.account.order_amount,price)
        self.order.sell('01',self.account.order_amount,price)