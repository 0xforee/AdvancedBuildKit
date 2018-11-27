#!/usr/bin/python3
# coding: utf-8

import datetime
import json
import logging
import time

from requests.exceptions import ConnectionError
from urllib3.exceptions import ReadTimeoutError, MaxRetryError

from common import flog
from common import jenkins, easy_gerrit
from configs import config
from common.db import AbkitDb
from configs.jobs.project_info import ProjectInfo
from configs.jobs.commit_items import CommitItem
from configs.jobs.commit_filter import DoNotSubmitFilter
from common.jenkins import JenkinsParams, JenkinsCacheHelper

from common.pygerrit import MergeCommitError
from requests.exceptions import HTTPError

PATH_WATCHED_BRANCHES = config.PATH_WATCHED_BRANCHES


class Task:
    """
    一个jenkinsTask任务所代表的资源集合，可以独立编译，item地址，
    """
    def __init__(self, dict_config):
        self.id = None
        self.base_branch = ""
        self.need_update = False
        self.jenkins_param = None
        self.firmware_path = None
        self.firmware_build_url = None
        self.watched_enabled = True
        self.project_info_list = []
        self.commit_list = []
        self.filter_list = []
        self.db = AbkitDb()
        self.init_filter()
        self.jenkins_cache_helper = JenkinsCacheHelper()

        # init from config
        self.parse_config(dict_config)

    def parse_config(self, dict_config):
        if not isinstance(dict_config, dict):
            raise TypeError("config must be dict object")
        # init from config

        if "watched_enabled" in dict_config.keys():
            self.watched_enabled = dict_config['watched_enabled']

        for watch_info in dict_config['watched_branches']:
            project_info = ProjectInfo(watch_info)
            self.project_info_list.append(project_info)

        # parse params
        self.parse_param(dict_config['params'])

    def parse_param(self, param_config):
        if not isinstance(param_config, dict):
            raise TypeError("config must be dict object")

        name = param_config['name']
        url = self.jenkins_cache_helper.get_url(name)
        base_branch = param_config['base_branch']
        suffix_name = param_config['suffix_name']
        param = JenkinsParams(name, url, base_branch, self._get_project_info())
        param.suffix_name = suffix_name

        self.jenkins_param = param

    def init_filter(self):
        """
        增加filter，用于过滤commitItem
        :return:
        """
        self.filter_list.append(DoNotSubmitFilter())

    def is_enabled(self):
        return self.watched_enabled

    def check_update(self, watch_id):
        """
        检查是否有更新，需要两个步骤
        1. gerrit查询list是否更新
        2. commit item 是否被过滤
        :return: 有更新true，无更新false
        """
        logging.debug("check update for id: " + watch_id)
        for project_info in self.project_info_list:
            result = self.check_project_update(watch_id, project_info.get_project(), project_info.get_branch())
            self.need_update = self.need_update or result

        return self.need_update

    @staticmethod
    def _generate_project_id(project):
        return project.replace('/', '%2F')

    def check_project_update(self, watched_id, project, branch):
        """
        检查某个task的某个project是否有新的提交
        :param watched_id: watch task的id
        :param project: 要执行检查的代码库名称，not id
        :param branch: 分支名称
        :return: 如果有更新，返回更新list，否则None
        """
        # parse result
        review_results = easy_gerrit.query(project, branch)
        logging.debug('result.len = %s' % str(len(review_results)))
        if review_results:
            # check if inited, if not, set latest number
            latest_number = review_results[0]['_number']
            project_id = self._generate_project_id(project) + '_' + self._generate_project_id(branch)

            # do init start {@
            # 以下这段代码涉及到了监视task初始化的策略，如果加入这段代码，初次运行，不产生任何更新
            # if not self.db.check_inited(watched_id, project_id):
            #     # TODO:add review url column
            #     review_url = ''
            #     update_time = time.strftime('%Y-%m-%d %H:%M:%S')
            #
            #     logging.info('watch id %s, project_id %s init at %s' % (watched_id, project_id, latest_number))
            #     self.db.update_watched_history(watched_id, project_id, latest_number, review_url, update_time)
            # do init end @}

            # get the latest review id from db
            db_review_id = self.db.get_latest_review_id(watched_id, project_id)

            # TODO: 加入查询列表循环
            for review in review_results:
                logging.info('review_id =' + str(review['_number']) + ', db_review_id = ' + str(db_review_id))
                if review['_number'] == db_review_id:
                    break
                else:
                    remote = easy_gerrit.get_remote_from_branch(project, branch)
                    commit_url = easy_gerrit.make_url_from_no(remote, review['_number'])

                    try:
                        commit_message = easy_gerrit.get_commit_message(commit_url)
                    except ValueError as e:
                        logging.warning('invalid url %s, skip parse' % commit_url.strip())
                        continue
                    except HTTPError as e:
                        logging.warning(e)
                        continue
                    except MergeCommitError as e:
                        logging.warning(e)
                        continue
                    else:
                        item = CommitItem(str(review['_number']), commit_message, commit_url)
                        self.commit_list.append(item)

            if self.commit_list:
                # update watched id
                # TODO:add review url column
                review_url = ''
                update_time = time.strftime('%Y-%m-%d %H:%M:%S')
                self.db.update_watched_history(watched_id, project_id, latest_number, review_url, update_time)

                logging.info('update finished at watched_id = %s, project_id = %s, latest_number = %s'
                             % (watched_id, project_id, latest_number))
                # 这里的update只是针对更新数据库的commit_id，接下来的sort函数会执行去重和过滤，取得最后的需要提测的commit信息
                self.commit_list = self.filter(self.commit_list)
                # TODO: 进行去重
                if len(self.commit_list) > 0:
                    return True

            else:
                logging.info('watched_id = %s, project = %s, No update merged commit found' % (watched_id, project))

        return False

    def _get_project_info(self):
        project_info_str = ""
        for p_info in self.project_info_list:
            if self.project_info_list.index(p_info) > 0:
                project_info_str += "|"

            project_info_str += "project=%s,branch=%s" % (p_info.get_project(), p_info.get_branch())

        return project_info_str

    def perform_jenkins_task(self):
        """
        触发一个jenkins编译
        :return: 编译得到firmware_path返回true，否则返回false
        """
        # start jenkins job
        logging.info('start jenkins task')

        # 3.启动编译任务
        # 是否后台阻塞等待编译完成，如果不阻塞，不会加固件地址到提测单
        # do not block in debug mode
        if config.DEBUG:
            block = False
        else:
            block = True

        try:
            self.jenkins_param.block = block
            queue_item = jenkins.start_task(self.jenkins_param)

            # 如果不阻塞，无法获取到链接和编译结果，直接跳过
            if block and queue_item:
                # 编译完成，获取build
                build = queue_item.get_build()

                # 更新编译链接
                self.firmware_build_url = build.baseurl

                result = build.is_good()
                if result:
                    # 编译成功，追加地址到提测单中
                    self.firmware_path = jenkins.get_build_target_location_from_freestyle(build.get_console())

                    # 格式化固件地址字符串
                    self.firmware_path = self.firmware_path.replace('storage_dir:', '固件地址：')

                    return True

        # TODO: 发生异常robot提示重新触发编译
        except ReadTimeoutError as e:
            logging.exception(e)
        except MaxRetryError as e:
            logging.exception(e)
        except ConnectionError as e:
            logging.exception(e)

        return False

    def filter(self, commit_list):
        """
        过滤不符合规则的merge提交
        :return:
        """
        filtered_list = []
        for filter_object in self.filter_list:
            for commit in commit_list:
                logging.debug('filter: ' + str(commit))
                if filter_object.filter(commit):
                    logging.warning(commit.get_review_url() + ' filte by: ' + filter_object.__class__.__name__)
                    continue
                else:
                    filtered_list.append(commit)
        return filtered_list

    def get_commit_list(self):
        return self.commit_list

    def get_firmware_path(self):
        return self.firmware_path
