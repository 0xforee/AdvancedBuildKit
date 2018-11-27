#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 foree <foree@foree-pc>
#
# Distributed under terms of the MIT license.
import json
import logging
import os
import re
import subprocess
import sys
from subprocess import CalledProcessError

from requests.exceptions import HTTPError

from common import flog
from common.pygerrit import GerritFactory
from common.pygerrit import MergeCommitError
from configs import config

BASE_URLS = {
        'xxxA': 'http://xxx.review.xxxx.com/',
        'xxxB': 'http://xxxx.rnd.xxxx.com/l/'
        }


def _get_remote_from_url(url):
    """根据url获取remote"""

    if url.startswith(BASE_URLS['xxx']):
        return 'xxx'
    elif url.startswith(BASE_URLS['xxxxx']):
        return 'xxxxx'
    else:
        raise ValueError('cannot parse this url for known remotes')


def _get_base_url(url):
    """
    获取base_url用于gerrit的认证
    :param url: 任意的合法的gerrit的url
    :return: 由schema + host组成的url
    """
    url = url.strip()
    remote = _get_remote_from_url(url)
    return BASE_URLS[remote]


def get_remote_from_branch(project, branch):
    """
    获取指定project库下，对应分支branch的remote名称
    remote名称用于加载对应gerrit的base_url
    :param project: project的名称
    :param branch: 需要识别的分支名称，可为任何分支
    :return: 如果存在，返回remote(xxx,xxxxx,xxxxxapp)，如果不存在提示错误
    """

    branches = load_project_branches(project)
    for remote in branches.keys():
        for remote_branch in branches[remote]:
            if branch == remote_branch:
                return remote

    # maybe not update in time! clean cache and try again!!
    clean_cache(project)
    remote = get_remote_from_branch(project, branch)
    if remote:
        return remote

    # not found, raise error
    raise ValueError('no such branch, please check your branch name')


def make_url_from_no(remote, no):
    """
    通过remote的change number，拼接url
    :param remote: 需要认证的地址
    :param no: number，review的标识
    :return: 拼接的地址
    """
    return BASE_URLS[remote] + str(no)


def _parse_review_no(url):
    """
    解析url中的change number, 如果不存在会报错
    :param url: 合法的changes url，包含number
    :return: 解析得到的number
    """
    url = url.strip()
    for item in url.split('/'):
        if item.isdigit():
            return item
    raise ValueError('Not valid changes url !!!')


def get_commit_revision(url):
    gerrit = GerritFactory.get_gerrit(_get_base_url(url))
    return gerrit.fetch_commit_revisions(_parse_review_no(url))


def get_commit_message(url):
    gerrit = GerritFactory.get_gerrit(_get_base_url(url))
    return gerrit.fetch_commit_message(_parse_review_no(url))


def fetch_review_info(url):
    """
    获取review的信息，包括project和branch
    :param url: 要解析的changes url，包含number
    :return: dict，包含review的信息
    """
    gerrit = GerritFactory.get_gerrit(_get_base_url(url))
    return gerrit.fetch_review_info(_parse_review_no(url))


def _encode_project_cache_name(project_name):
    if project_name:
        project_cache_path = config.PATH_CACHE_DIR + project_name.replace('/', '%2F')
        logging.debug('project cache = ' + project_cache_path)
        return project_cache_path

    raise ValueError("project name not empty!!")


def load_project_branches(project):
    """
    获取指定project的多个gerrit分支集
    :param project:
    :return: dict, project库下对应的多个分支
    """

    # if not exists, fetch first
    # 缓存名称时project的名称加密
    if not os.path.exists(_encode_project_cache_name(project)):
        fetch_project(project)

    try:
        with open(_encode_project_cache_name(project)) as f:
            return json.load(f)
    except TypeError:
        raise


def clean_cache(project):
    """
    清除指定的project的缓存，用于强制刷新
    :param project: project的名称
    """
    if not os.path.exists(_encode_project_cache_name(project)):
        return
    else:
        os.remove(_encode_project_cache_name(project))
        print('cleaning cache ...')


def fetch_project(project):

    logging.debug('fetch project')
    remote_branches = {}

    for remote, url in BASE_URLS.items():
        gerrit = GerritFactory.get_gerrit(url)
        branches = gerrit.fetch_project_branches(project)
        if branches:
            remote_branches[remote] = branches

    # if fetch success, update local cache
    if remote_branches:
        with open(_encode_project_cache_name(project), 'w') as f:
            json.dump(remote_branches, f)


def create_branch(project, initial_revision, new_branch_name):
    """创建分支"""
    if not new_branch_name.startswith('xxxxx/' + config.get_user_profile()['username'] + '/'):
        print('branch name must starts with xxxxx/' + config.get_user_profile()['username'] + '/')
        exit()

    remote = get_remote_from_branch(project, initial_revision)

    gerrit = GerritFactory.get_gerrit(BASE_URLS[remote])
    result = gerrit.create_branch(project, initial_revision, new_branch_name)
    print(result)


def query(project, branch):
    """
    对pygerrit的简单封装，查询指定project，指定branch，merged的提交记录
    :param project: manifests中的project字段
    :param branch: 分支名称
    :param pages: 需要查询的页码，默认为0
    :return: dict, 查询到的结果
    """
    url = BASE_URLS[get_remote_from_branch(project, branch)]
    gerrit = GerritFactory.get_gerrit(url)
    return gerrit.query(project=project, branch=branch)


def recognize_project():
    """
    识别当前目录是什么project，只有在命令行跑的时候才需要用到
    :return:识别出project的名称，类似于 platform/frameworks/base 否者提示手工指定
    """
    try:
        result = subprocess.check_output('git remote -v', shell=True)
        result = result.decode('utf-8').split('\n')[0]

        # 输出结果必须包含username，否则不合法
        if result.rfind(config.get_user_profile()['username']) != -1:
            p = re.compile(r' |\n|\d+')
            result = p.split(result)
            project_name = result[2].strip('/')
            logging.debug('current_project = ' + project_name)
            return project_name
    except CalledProcessError as e:
        pass

    raise ValueError('Not valid workspace !!!')


def get_commit_messages(review_list):
    """根据review list获取提交信息
    """

    commit_info = ''
    i = 1
    for review_url in review_list:
        try:
            result_info = get_commit_message(review_url)
        except ValueError as e:
            logging.warning('invalid url %s, skip parse' % review_url.strip())
            continue
        except HTTPError as e:
            logging.warning(e)
            continue
        except MergeCommitError as e:
            logging.warning(e)
            continue
        else:
            commit_info += '问题' + str(i) + '：\n'
            commit_info += review_url + '\n'
            commit_info += result_info + '\n\n'
            i += 1

    return commit_info


def generate_review_list():
    """
    从用户输入中获取多个review链接
    :return: review链接的列表
    """
    review_list = []
    # TODO:格式化输入的连接，因为要拼接字符串
    print('Please input reviews: ')
    for review_url in sys.stdin:
        if review_url.startswith('http') and review_url not in review_list:
            review_list.append(review_url)
        else:
            print("Invalid url, must startswith 'http://' ")
            sys.exit(1)

    return review_list


def chose_branch(project, branch_keyword='', retry=0, filter_personal=False):
    """
    从cache中加载initial revision交由用户选择,如果keyword不为空，使用keyword进行模糊匹配
    :param project: project name, not project path
    :param branch_keyword: 匹配分支的关键字
    :param retry: 网络失败，请求的重试次数
    :param filter_personal: 过滤个人分支，一般用于创建分支
    :return: 用户选择的base branch
    """
    branches = load_project_branches(project)

    i = 0
    chose_list = []
    for remote, branch_list in branches.items():
        print(remote + " :")
        for branch in branch_list:
            if filter_personal:
                if branch.startswith('xxxxx/'):
                    continue
            if re.search(branch_keyword, branch, re.I):
                print("\t\t%d. %s" % (i, branch))
                chose_list.append(branch)
                i += 1

    # if not match any branch, exit
    if chose_list:
        u_input = input("Select [0]:")
        if len(u_input.strip()) == 0:
            user_input = 0
        else:
            user_input = int(u_input)

        if -1 < user_input < i:
            return chose_list[user_input]
        else:
            print("input not invalid, retry")
            chose_branch(project, branch_keyword, retry, filter_personal)
    else:
        print('Not found branch matched %s' % branch_keyword)
        if retry < 1:
            print()
            print('trying forced update project ...')
            clean_cache(project)
            chose_branch(project, branch_keyword, retry+1, filter_personal)


if __name__ == '__main__':
    pass

