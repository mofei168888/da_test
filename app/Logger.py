#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

class Logger:

    def __init__(self,name,level=logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(self.formatter)

        self.logger.addHandler(ch)

    def set_log_file(self,level,file_name):
        self.fh = logging.FileHandler(file_name)
        self.fh.setLevel(level)
        self.fh.setFormatter(self.formatter)

        self.logger.addHandler(self.fh)

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
    log.set_log_level(logging.ERROR)
    #file_name = "D:\config\log\{}".format('test.log')
    #log.set_log_file(logging.INFO,file_name)
    log.log_debug('debug info')
    log.log_info('info')
    log.log_warning('warning info')
    log.log_error('error info')