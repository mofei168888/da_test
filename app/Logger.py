#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

class Logger:

    def __init__(self,name,level=logging.INFO):
        logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(name)

    def set_log_level(self,level):
        self.logger.setLevel(level)

    def log_debug(self,msg):
        self.logger.debug(msg)

    def log_info(self,msg):
        self.logger.info(msg)

    def log_warning(self,msg):
        self.logger.warning(msg)

    def log_error(self,msg):
        self.logger.error(msg)

if __name__ == '__main__':
    log = Logger('Example')
    log.set_log_level(logging.DEBUG)
    log.log_debug('debug info')
    log.log_info('info')
    log.log_warning('warning info')
    log.log_error('error info')