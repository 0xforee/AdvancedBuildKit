#!/usr/bin/python3
# coding: utf-8

import datetime
import logging
import time

from common import flog
from common import redmine
from common.dtrobot import DingTalkRobot
from configs import config
from configs.jobs.task import Task

PATH_WATCHED_BRANCHES = config.PATH_WATCHED_BRANCHES


class Job:
    """
    代表一个WatchJob
    """
    def __init__(self, watch_config):
        self.tasks = []
        self.need_updated_tasks = []
        self.description = ""
        self.dingtalk_webhook = ""
        self.redmine_key = ""
        self.watched_enabled = True
        self.redmine_issue_id = None
        self.robot = None
        self.id = None
        self.parse_config(watch_config)

    def parse_config(self, watch_config):
        if not isinstance(watch_config, dict):
            raise TypeError('config must be dict object')
        # 从给定的配置文件中解析配置

        # id
        self.id = watch_config['id']

        # 全局监视开关
        self.watched_enabled = watch_config['watched_enabled']

        # 任务描述信息
        if 'description' in watch_config.keys():
            self.description = watch_config['description']
            logging.info(watch_config['description'])

        # load dingtalk webhook
        if config.DEBUG:
            self.dingtalk_webhook = config.TEST_WEBHOOK
        else:
            self.dingtalk_webhook = watch_config['dingtalk_webhook']

        self.robot = DingTalkRobot(self.dingtalk_webhook)

        # load redmine key, if not exits, load default
        self.redmine_key = watch_config['redmine_key']
        if not self.redmine_key:
            self.redmine_key = config.get_redmine_key()

        # 提取tasks
        for watch_tasks in watch_config['watched_tasks']:
            task = Task(watch_tasks)

            self.tasks.append(task)

    def is_enabled(self):
        return self.watched_enabled

    def run(self):
        """
        执行：检查更新，生成提测单操作
        :return:
        """

        # 全局开关
        if not self.is_enabled():
            return

        # 检查更新
        for task in self.tasks:
            # check if all task not enabled
            if not task.is_enabled():
                logging.info('wached_enabled not true, skip!')
                continue

            # check if all task not updated
            if not task.check_update(self.id):
                continue

            self.need_updated_tasks.append(task)

        if len(self.need_updated_tasks) > 0:
            # 打印监视任务描述信息
            logging.info(self.description)

            # 生成提测单
            self.generate_table()

            # 触发编译，如果编译成功，更新提测单
            for task in self.need_updated_tasks:
                if task.perform_jenkins_task():
                    # 更新提测单
                    self.generate_table()
                else:
                    # 编译结果异常
                    if task.firmware_build_url:
                        msg = "编译失败：" + task.firmware_build_url
                    else:
                        msg = "编译任务：" + task.base_branch + "可能已经触发，但未能跟踪到结果"

                    self.robot.send_msg(msg)
        else:
            # 没有更新
            msg = '每日构建分支没有新的提交，故今天没有提测单，请知悉^_^'
            self.robot.send_msg(msg)

    def gen_redmine_description(self):
        question_id = 1
        commit_info = ""
        for task in self.need_updated_tasks:
            for commit in task.get_commit_list():
                commit_info += '问题' + str(question_id) + '：\n'
                commit_info += commit.get_review_url() + '\n'
                commit_info += commit.get_message() + '\n\n'
                question_id += 1

            # if firmware path exits, add it
            if task.get_firmware_path():
                commit_info += task.get_firmware_path() + '\n\n'
                # add separtor
                commit_info += '---\n'

        return commit_info

    def generate_table(self):
        """
        执行生成提测单操作，如果已经生成过，那么更新
        :return:
        """
        if len(self.need_updated_tasks) > 0:
            message = self.gen_redmine_description()

            if not self.redmine_issue_id:
                # create table
                self.redmine_issue_id = redmine.generate_table(self.redmine_key, message)
                logging.info('create redmine bugs ' + message)

                # send msg by robot
                issue = redmine.get_issue(self.redmine_key, self.redmine_issue_id)

                self.robot.send_link(issue.subject, issue.description, issue.url, redmine.REDMINE_FAVICON)
                self.robot.send_msg(issue.subject + '\n' + issue.url + '\n', None, True)
                # get today
                year = time.localtime().tm_year
                month = time.localtime().tm_mon
                day = time.localtime().tm_mday
                today_date = datetime.date(year, month, day)

                logging.debug('issue: ' + issue.url + ' created at: ' + str(today_date))
            else:
                # update table
                redmine.update_table(self.redmine_key, self.redmine_issue_id, message)
