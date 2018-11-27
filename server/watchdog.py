#!/usr/bin/python3
# coding: utf-8

import logging
import sys
import time
import os

from apscheduler.schedulers.background import BackgroundScheduler

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from common import flog
from common.demo_base import Daemon
from configs import config
from configs.jobs.job_watch_branch import WatchBranchJob
from configs.jobs.job_sync_jenkins import SyncJenkinsJob


class WatchedDaemon(Daemon):
    """后台服务
    1. 触发定时任务
    2. 定时更新缓存
    """
    sched = BackgroundScheduler()

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', args=None):
        super(WatchedDaemon, self).__init__(pidfile, stdin, stdout, stderr, args)
        self.watch_branch_job = WatchBranchJob()
        self.sync_jenkins_job = SyncJenkinsJob()

    # def job_sync_project_branches(self):
    #     """sync project branches every 10 mins"""
    #     try:
    #         project = 'platform/frameworks/base'
    #         easy_gerrit.fetch_project(project)
    #         logging.info(time.ctime() + ': update project %s branches finished!' % project)
    #     except HTTPError as e:
    #         logging.error(time.ctime() + str(e))

    def job_sync_base_branches(self):
        """
        sync base branches every 1 hour
        """
        self.sync_jenkins_job.run()

    def job_watch_branch(self):
        self.watch_branch_job.run()

    def run(self):
        # self.sched.add_job(self.job_sync_project_branches, 'interval', minutes=10)
        self.sched.add_job(self.job_sync_base_branches, 'interval', hours=6)
        if config.DEBUG:
            self.sched.add_job(self.job_watch_branch, 'interval', minutes=1)
        else:
            self.sched.add_job(self.job_watch_branch, 'cron', hour=00, minute=5)

        self.sched.start()

        # keep main thread alive
        while True:
            time.sleep(60 * 60)


if __name__ == '__main__':

    if config.DEBUG:
        logging.info('DEBUG MODE')
        demo = WatchedDaemon(config.PATH_WATCHDOG_SERVER_PID_FILE + '_debug', '/dev/null',
                             config.PATH_WATCHDOG_STDOUT_FILE + '_debug', config.PATH_WATCHDOG_STDERR_FILE + '_debug')
        demo.job_watch_branch()
    else:
        demo = WatchedDaemon(config.PATH_WATCHDOG_SERVER_PID_FILE, '/dev/null',
                             config.PATH_WATCHDOG_STDOUT_FILE, config.PATH_WATCHDOG_STDERR_FILE)
        if len(sys.argv) > 1:
            command = sys.argv[1]
            if command == 'start':
                demo.start()
            elif command == 'stop':
                demo.stop()
            elif command == 'restart':
                demo.restart()
            elif command == 'job_watch_branch':
                demo.job_watch_branch()
            elif command == 'job_sync_base_branches':
                demo.job_sync_base_branches()

