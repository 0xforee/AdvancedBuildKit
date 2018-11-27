#! /usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 foree <foree@foree-pc>
#
# Distributed under terms of the MIT license.

import datetime
import logging
import time

from redminelib import Redmine

from common import flog
from configs import config

"""
提交测试单
"""

REDMINE_FAVICON = 'http://xxx.redmine.com/favicon.ico'

HOST_URL = 'http://redmine.xxxxx.com'


def get_redmine(url, key):
    return Redmine(url, key=key)


def get_issue(key, issue_id):
    """
    根据issue_id获取issue对象
    :param issue_id:
    :return:
    """

    return get_redmine(HOST_URL, key=key).issue.get(issue_id)


def update_table(key, issue_id, description):
    redmine = get_redmine(HOST_URL, key=key)
    issue = redmine.issue.get(issue_id)

    issue.description = description
    issue.save()


def generate_table(key, description):
    redmine = get_redmine(HOST_URL, key=key)

    # get today
    year = time.localtime().tm_year
    month = time.localtime().tm_mon
    day = time.localtime().tm_mday
    today_date = datetime.date(year, month, day)

    if config.DEBUG:
        issue = redmine.issue.get(698851)
    else:
        issue = redmine.issue.new()

    # 放置信息
    issue.project_id = '693'  # 项目：通知中心
    issue.subject = '（%s.%s）bugfix提测单' % (month, day)
    issue.category_id = 429  # 类别：通知中心
    issue.priority_id = 5  # 优先级：高
    issue.tracker_id = 23  # 追踪ID：手机端测试申请单
    issue.description = description  # 描述：
    issue.assigned_to_id = 2981  # 指派给：用户id(liming1), lijun=3070, 2981=liangrui
    issue.watcher_user_ids = []  # 跟踪者：
    issue.custom_fields = [
        {'name': '测试类别', 'value': '基本功能验证', 'id': 27},
        {'name': '应用版本', 'value': ['支持Tag特性，可输入内容后按回车新建Tag'], 'multiple': True, 'id': 31},
        {'name': '适用机型', 'value': ['All'], 'multiple': True, 'id': 23},
        {'name': '产品负责人', 'value': '211', 'id': 24},
        {'name': '发布类型', 'value': '固件发布', 'id': 25},
        {'name': '自测', 'value': '1', 'id': 28},
        {'name': '测试重点', 'value': '按验证建议即可', 'id': 30},
        {'name': '发布风险', 'value': '中', 'id': 29},
        {'name': '专题', 'value': '功能', 'id': 50},
        {'name': '严重程度', 'value': '严重', 'id': 2}
    ]

    #issue.start_date = today_date
    #issue.due_date = today_date

    # 触发发送
    if config.DEBUG:
        # debug模式 不触发redmine的修改提交
        print_string = 'issue create skip: ' + issue.url
        print(print_string)
        logging.info(print_string)
    else:
        issue.save()
        print_string = 'issue has created: ' + issue.url
        print(print_string)
        logging.info(print_string)

    return issue.id


if __name__ == '__main__':
    pass
