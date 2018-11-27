#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 foree <foree@foree-pc>
#
# Distributed under terms of the MIT license.

"""
配置logging的基本配置
"""
import logging
import sys
import os
from common.common import get_root_path


FILE_LEVEL = logging.DEBUG
STREAM_LEVEL = logging.WARN

LOG_DIR = os.path.join(get_root_path(), 'log')
PATH_LOG = os.path.join(get_root_path(), 'log/advanced_build_kit.log')

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

if not os.path.exists(PATH_LOG):
    f = open(PATH_LOG, 'w')
    f.write('')
    f.close()

# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create formatter
message_fmt = "%(asctime)s %(process)d/%(filename)s %(levelname)s/%(funcName)s(%(lineno)d): %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt=message_fmt, datefmt=datefmt)

# create file handler
fh = logging.FileHandler(PATH_LOG)
fh.setLevel(FILE_LEVEL)
fh.setFormatter(formatter)
logger.addHandler(fh)

# create stdout handler
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(STREAM_LEVEL)
sh.setFormatter(formatter)
logger.addHandler(sh)
