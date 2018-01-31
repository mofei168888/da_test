#!/usr/bin/env python



try:
    from app.Logger import *
except Exception as e:
    from Logger import *



if __name__ == '__main__':
     logger = Logger('eth_usdt')
     log= logger.get_loger()

     log.debug('debug info')
     log.info('info')
     log.warning('warning info')
     log.error('error info')