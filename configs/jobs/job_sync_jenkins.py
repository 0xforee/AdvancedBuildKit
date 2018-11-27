#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

# Copyright © 18-5-24 foree <foree@foree-pc>

# Distributed under terms of the MIT license.

# ===========================================
from common.jenkins import JenkinsCacheHelper
import logging
from common import flog
from requests.exceptions import HTTPError
import time


class SyncJenkinsJob:
    def run(self):
        try:
            jenkins_cache_helper = JenkinsCacheHelper()
            jenkins_cache_helper.fetch_all_base_branch()
            logging.info(time.ctime() + ': update base branches finished!')
        except HTTPError as e:
            logging.error(time.ctime() + str(e))


if __name__ == '__main__':
    pass
