#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from app.OK_Services import *
except Exception as e:
    from OK_Services import *



if __name__ == '__main__':

    ok_trade = Ok_Services()

    result = ok_trade.get_future_order(symbol='eth_usdt',order_id=-1,status=2,current_page=1,page_length=50)
    print(result)