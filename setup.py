#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 foree <foree@foree-pc>
#
# Distributed under terms of the MIT license.

"""
初始化一些操作
"""

import os
import shutil
import subprocess

from common.common import get_root_path
from common.jenkins import JenkinsCacheHelper

MAGIC_PREFIX = '# This is auto generate by autoBuild, Do Not Delete it'
MAGIC_SUFFIX = '# end by autoBuild'


def init_bash_path():
    """将当前路径加入base PATH中
    """

    print('init bash path...')

    # backup current bashrc
    bashrc = os.path.join(os.getenv("HOME"), '.bashrc')

    # if .bashrc exists, backup
    if os.path.exists(bashrc):
        shutil.copyfile(bashrc, os.path.join(get_root_path(), 'configs/.bashrc.bk'))
    else:
        print(bashrc + ' not exits. exit!! ')
        exit(0)

    with open(bashrc) as f:
        # if already write to PATH
        line = f.readline()
        while line:
            if line.strip() == MAGIC_PREFIX:
                print('current path already write to PATH! skip!')
                print('')
                return
            line = f.readline()

    # write to PATH
    with open(bashrc, 'a+') as f:
        f.write(MAGIC_PREFIX + '\n')
        path_string = 'export PATH=${PATH}:%s' % (os.path.join(get_root_path(), 'scripts'))
        f.write(path_string + '\n')
        f.write(MAGIC_SUFFIX)


def init_script_cache():
    """脚本内容初始化
    1. 开启守护线程（默认不开启)
    2. 更新缓存
    """
    # 更新缓存
    print('init update base branches cache...')
    jenkins = JenkinsCacheHelper()
    jenkins.fetch_all_base_branch()
    print('base branches update done')
    print('')

    # start watchdog
    # cmd = os.path.join(get_root_path(), 'server/watchdog.py') + ' start'
    # subprocess.call(cmd, shell=True)


if __name__ == '__main__':
    init_bash_path()
    init_script_cache()
