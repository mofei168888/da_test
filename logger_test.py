#!/usr/bin/env python



import time
try:
    from app.Logger import *
except Exception as e:
    from Logger import *



if __name__ == '__main__':
     log= logging.getLogger('test')

     log.debug('debug info')
     log.info('info')
     log.warning('warning info')
     time.sleep(5)
     log.error('error info')

