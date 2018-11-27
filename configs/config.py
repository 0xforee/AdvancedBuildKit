#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 foree <foree@foree-pc>
#
# Distributed under terms of the MIT license.

"""
配置信息
"""
import base64
import getpass
import os
import json

from common.common import get_root_path

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'

# debug mode
DEBUG = False

# for user profile
PATH_USER_PROFILE = os.path.join(get_root_path(), 'configs/.user_profile')

# for watched branches
PATH_WATCHED_BRANCHES = os.path.join(get_root_path(), "configs/watched_branch.json")

# for remote branches
PATH_CACHE_DIR = os.path.join(get_root_path(), 'cache/')

# for jenkins base branches
PATH_BASE_BRANCHES_CACHE = os.path.join(get_root_path(), 'cache/base_branches.json')

# for commit info file prefix
PATH_COMMIT_INFO_PREFIX = os.path.join(get_root_path(), 'output/commit_info_')

# for all database path
PATH_ABKIT_DATABASE = os.path.join(get_root_path(), 'output/abkit.db')

# for watched server stdout
PATH_WATCHDOG_STDOUT_FILE = os.path.join(get_root_path(), 'log/watchdog.log')

# for watched server stderr
PATH_WATCHDOG_STDERR_FILE = os.path.join(get_root_path(), 'log/watchdog_err.log')

# for watched server pid file
PATH_WATCHDOG_SERVER_PID_FILE = '/tmp/watchdog.pid'

# for dingtalk robot test webhook
TEST_WEBHOOK = 'https://oapi.dingtalk.com/robot/send?access_token=86a596930c375d0ea06db53a40855a7109630b1757216b1fa324e308ec850485'

# sign app config
SIGN_APPS_CONFIG = os.path.join(get_root_path(), "configs/sign_app_configs.json")


def load_profile():
    """
    加载配置文件
    :return: dict
    """
    try:
        if os.path.exists(PATH_USER_PROFILE):
            with open(PATH_USER_PROFILE) as f:
                profile = json.load(f)
                return profile
        else:
            raise TypeError('user profile is invalid, please delete config/.user_profile and reinit')
    except:
        print('load profile failed, clean and try init')
        os.remove(PATH_USER_PROFILE)
        _init()
        return load_profile()


def get_redmine_key():
    """
    redmine的key
    :return:
    """
    try:
        key = load_profile()['redmine_key']
        if len(key) > 0:
            return key
        else:
            raise ValueError('user profile is invalid, please delete config/.user_profile and reinit')
    except KeyError as e:
        print('not found redmine_key in user_profile, did you init this item?? ')
        raise e
    except TypeError as e:
        print('not found redmine_key in user_profile, did you init this item?? ')
        raise e


def get_odc_key():
    """
    odc gerrit的key
    :return:
    """
    try:
        key = load_profile()['odcgerrit']
        if len(key) > 0:
            return key
        else:
            raise ValueError('user profile is invalid, please delete config/.user_profile and reinit')
    except KeyError as e:
        print('not found odcgerrit in user_profile, did you init this item?? ')
        raise e
    except TypeError as e:
        print('not found odcgerrit in user_profile, did you init this item?? ')
        raise e


def get_user_profile():
    """ 解析用户名和密码
    """
    try:
        # init user config
        profile = load_profile()['user_profile']

        if len(profile) > 0:
            user_list = base64.b64decode(profile).decode('utf-8').split(':')
            data = {"username": user_list[0], "password": user_list[1]}
            return data
        else:
            raise ValueError('user profile is invalid, please delete config/.user_profile and reinit')
    except KeyError as e:
        print('not found username in user_profile, did you init this item?? ')
        raise e
    except TypeError as e:
        print('not found username in user_profile, did you init this item?? ')
        raise e


def _init():
    # init dirs
    config_dirs = ['configs', 'cache', 'output', 'log']
    for config_dir in config_dirs:
        dir_path = os.path.join(get_root_path(), config_dir)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

    # init user profile
    if not os.path.exists(PATH_USER_PROFILE):
        with open(PATH_USER_PROFILE, 'w') as f:
            user_profile = {}

            # 1. 输入用户名密码
            print('请输入用户名和密码来初始化（用户名不带@后缀)')
            username = input('username:')
            if len(username.strip()) > 0:
                password = getpass.getpass('password:')
                if len(password.strip()) > 0:
                    profile = username + ':' + password
                    profile = base64.b64encode(profile.encode('utf-8'))
                    user_profile['user_profile'] = profile.decode('utf-8')

            # 2. 输入redmine_key
            print('请输入redmine_key，如果不需要redmine提单功能，请回车跳过')
            redmine_key = input('redmine_key:')
            if len(redmine_key.strip()) > 0:
                user_profile['redmine_key'] = redmine_key

            json.dump(user_profile, f)


_init()


if __name__ == '__main__':
    get_user_profile()

