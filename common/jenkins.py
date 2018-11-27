#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 foree <foree@foree-pc>
#
# Distributed under terms of the MIT license.

"""
构建编译任务
"""
import json
import logging
import os
import re
from pprint import pprint

from jenkinsapi.jenkins import Jenkins

from common import flog
from configs import config

CACHE_FILE = config.PATH_BASE_BRANCHES_CACHE

JENKINS_ALL_JOBS_API = 'http://jenkins.rnd.xxxxx.com/api/json'
JENKINS_HOST = 'http://jenkins.rnd.xxxxx.com'

# default config
DEFAULT_VERSION = '7.0.0.1'
DEFAULT_VARIANT = 'user'
DEFAULT_SUFFIX_NAME = 'dev_bugfix_freestyle_by_abkit'
DEFAULT_TYPE = ''


class JenkinsJob:
    """
    jenkins 一个job需要的数据结构体
    name: job名称
    url: job对应的链接

    """
    def __init__(self, name, url):
        self.name = name
        self.branch = []
        self.type = []
        self.variant = []
        self.url = url

    def set_branch(self, branch):
        self.branch = branch

    def set_type(self, build_type):
        self.type = build_type

    def set_variant(self, variant):
        self.variant = variant

    def is_base_branch_matched(self, branch_name):
        if self.branch:
            for branch in self.branch:
                if re.search(branch_name, branch, re.I):
                    return True

        return False

    @classmethod
    def from_json(cls, json_obj):
        job = JenkinsJob(json_obj['name'], json_obj['url'])
        job.set_variant(json_obj['variant'])
        job.set_type(json_obj['type'])
        job.set_branch(json_obj['branch'])
        return job


class JenkinsParams:
    """
    启动一个job需要的参数
    """
    def __init__(self, name, url, branch, project_info):
        self.name = name
        self.build_url = url + '/build'
        self.branch = branch
        self.project_info = project_info
        self._block = False
        self._variant = DEFAULT_VARIANT
        self._suffix_name = DEFAULT_SUFFIX_NAME
        self._type = DEFAULT_TYPE
        self._version = DEFAULT_VERSION

    @property
    def suffix_name(self):
        return self._suffix_name

    @suffix_name.setter
    def suffix_name(self, suffix_name):
        self._suffix_name = suffix_name

    @property
    def variant(self):
        return self._variant

    @variant.setter
    def variant(self, variant):
        self._variant = variant

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, build_type):
        self._type = build_type

    @property
    def block(self):
        return self._block

    @block.setter
    def block(self, block):
        self._block = block

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, version):
        self._version = version

    def to_dict(self):
        target_dict = {}
        target_dict['name'] = self.name
        target_dict['branch'] = self.branch
        target_dict['project_info'] = self.project_info

        if self._type:
            target_dict['type'] = self._type

        if self._variant:
            target_dict['variant'] = self._variant

        if self._version:
            target_dict['version'] = self._version

        if self._suffix_name:
            target_dict['suffix_name'] = self._suffix_name

        return target_dict


class JenkinsCacheHelper(object):
    """
    Jenkins缓存的帮助类
    """
    def __init__(self):
        self.jobs_cache = self.load_jenkins_cache()

    @staticmethod
    def should_cache(job_name):
        """
        指定cache的规则，过滤不符合要求的job
        :param job_name:从jenkins获取的name标识，指定唯一job
        :return:如果符合缓存规则，返回true；否则返回false
        """
        # url中包含ALL-FREESTYLE 且 不包含FVCS的
        # TODO: 且 color:"disabled"
        return job_name.find('ALL-FREESTYLE') != -1 and job_name.find('FVCS') == -1

    def fetch_all_base_branch(self):
        """
        获取base_branch以及对应的url到缓存json文件
        """
        jenkins = get_jenkins()
        cache = []
        for job_name in jenkins.get_jobs_list():
            if self.should_cache(job_name):
                print("Fetch job: " + job_name)
                # 获取job的单个属性
                job = jenkins.get_job(job_name)

                jenkins_job = JenkinsJob(job.name, job.baseurl)

                # get branches

                actions = job._data['actions']
                for action in actions:
                    if 'parameterDefinitions' in action.keys():
                        descriptions = action['parameterDefinitions']
                        for description in descriptions:
                            if description['name'] == 'branch':
                                logging.debug(job.name + ", branches = ".join(description['choices']))
                                jenkins_job.set_branch(description['choices'])
                            if description['name'] == 'variant':
                                logging.debug(job.name + ", variant = ".join(description['choices']))
                                jenkins_job.set_variant(description['choices'])
                            if description['name'] == 'type':
                                logging.debug(job.name + ", type = ".join(description['choices']))
                                jenkins_job.set_type(description['choices'])
                cache.append(jenkins_job.__dict__)

        # update cache
        self.update_cache(cache)

    def get_jobs(self, base_branch):
        """
        从给定的base_branch查找对应的jobs
        :param base_branch:
        :return:
        """
        results = []
        for job_cache in self.jobs_cache:
            if not base_branch:
                results.append(job_cache)
                continue
            if job_cache.is_base_branch_matched(base_branch):
                results.append(job_cache)

        return results

    def get_url(self, job_name):
        """
        获取job对应的url
        :param job_name:
        :return:
        """
        for job_cache in self.jobs_cache:
            if job_cache.name == job_name:
                return job_cache.url

        raise ValueError('Not Found job_name %s, check if exits firstly' % job_name)

    def load_jenkins_cache(self, re_try=0):
        """
        加载缓存，缓存文件的结构，参见fetch_all_base_branch
        :return: JenkinsJob，list
        """
        if not os.path.exists(CACHE_FILE):
            self.fetch_all_base_branch()

        if re_try > 5:
            raise TimeoutError('load jenkins cache retry 5 time!!!')

        try:
            with open(CACHE_FILE) as f:
                jenkins_cache = json.load(f)
                if not jenkins_cache:
                    self.load_jenkins_cache(re_try + 1)
        except TypeError:
            raise

        job_cache = []
        for cache in jenkins_cache:
            job_cache.append(JenkinsJob.from_json(cache))
        return job_cache

    def update_cache(self, cache):
        # update cache
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)

    def load_cached_branches(self):
        """
        加载缓存文件中所有的分支信息
        :return:返回list类型的Params
        """
        params_list = []
        for job_cache in self.jobs_cache:
            for branch in job_cache.branch:
                params = JenkinsParams(job_cache.name, job_cache.url, branch, '')
                params_list.append(params)

        return params_list


def start_task(jenkins_params: JenkinsParams):

    # 打印json配置参数
    print_string = "\n 编译的参数:\n" + json.dumps(jenkins_params.__dict__)
    logging.info(print_string)
    pprint(print_string)

    if config.DEBUG:
        print('debug mode, skip start task!!')
    else:
        block = jenkins_params.block
        jenkins = get_jenkins()
        queue_item = jenkins[jenkins_params.name].invoke(block=block, build_params=jenkins_params.to_dict())

        if block:
            return queue_item

        if queue_item.is_running():
            print(queue_item.get_build_number())
        else:
            print('task is queuing....')


def get_jenkins():
    return Jenkins(JENKINS_HOST, username=config.get_user_profile()['username'], password=config.get_user_profile()['password'], timeout=60)


def get_build_target_location_from_freestyle(console):
    """
    从输出中解析固件地址
    :param console: 终端输入内容
    :return: 解析出的固件地址
    """
    console = console.encode('ISO-8859-1').decode('utf-8', errors='ignore')
    for line in console.splitlines():
        if re.search('storage_dir', line):
            print(line)
            return line

    logging.info('cannot resolve location from console!')
    return ""


if __name__ == '__main__':
    pass

