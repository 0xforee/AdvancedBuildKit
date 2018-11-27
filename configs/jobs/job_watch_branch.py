#!/usr/bin/python3
# coding: utf-8

import json
import logging

from common import flog
from configs import config
from configs.jobs.Job import Job

PATH_WATCHED_BRANCHES = config.PATH_WATCHED_BRANCHES


class WatchBranchJob:
    def run(self):
        """基于base branch监控project对应的branch是否有更新，如果有更新启动任务，并生成提交信息
                    watch branch at 23:55 every day
                """
        logging.info('watch branch start')
        with open(PATH_WATCHED_BRANCHES) as f:
            configs = json.load(f)['defconfig']

        for watch_config in configs:
            # init job
            # TODO: job使用多线程
            job = Job(watch_config)
            job.run()


if __name__ == '__main__':
    if config.DEBUG:
        watch_job = WatchBranchJob()
        watch_job.run()
