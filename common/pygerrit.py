#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 foree <foree@foree-pc>
#
# Distributed under terms of the MIT license.
import json
import logging

import requests
from requests.auth import HTTPBasicAuth

from common import flog
from configs import config

GERRIT_MAGIC_JSON_PREFIX = ")]}\'\n"

GERRIT_API_CHANGES = '/changes/'
GERRIT_API_PROJECTS = '/projects/'


class Error(Exception):
    """Base class for exception in this module"""
    pass


class MergeCommitError(Error):
    """ if commit is a merge code, throw it"""


class Revisions:
    def __init__(self, url, refs):
        self.url = url
        self.refs = refs

    def set_url(self, url):
        self.url = url

    def set_refs(self, refs):
        self.refs = refs


class Gerrit(object):

    def __init__(self, url):
        self.base_url = url.rstrip('/') + '/a'
        self.s = requests.Session()
        self.s.auth = HTTPBasicAuth(config.get_user_profile()['username'], config.get_user_profile()['password'])
        self.s.headers = {'User-Agent': config.USER_AGENT}

    def fetch_review_info(self, review_no):
        """根据review链接获取相关信息
            """
        url = self.base_url + GERRIT_API_CHANGES + str(review_no)
        params = {'o': ['CURRENT_REVISION', 'CURRENT_COMMIT']}

        r = self.s.get(url, params=params)
        r.raise_for_status()
        result = self._parser_response(r)
        current_revision = result['current_revision']
        commit = result['revisions'][current_revision]['commit']

        if len(commit['parents']) > 1:
            raise MergeCommitError('%s is merge commit, abandon it!' % url.replace('a/changes', '#/c'))
        return result

    def fetch_commit_revisions(self, review_no):
        """
        根据review链接获取commit revisions
        :param review_no:
        :return: Revisions
        """
        url = self.base_url + GERRIT_API_CHANGES + str(review_no)
        params = {'o': ['CURRENT_REVISION', 'CURRENT_COMMIT']}

        r = self.s.get(url, params=params)
        logging.debug(url)
        r.raise_for_status()
        result = self._parser_response(r)
        current_revision = result['current_revision']
        fetch_info = result['revisions'][current_revision]['fetch']['ssh']
        return Revisions(fetch_info['url'], fetch_info['ref'])

    def fetch_commit_message(self, review_no):
        """根据review number获取commit message"""
        url = self.base_url + GERRIT_API_CHANGES + str(review_no)
        params = {'o': ['CURRENT_REVISION', 'CURRENT_COMMIT']}

        r = self.s.get(url, params=params)
        logging.debug(url)
        r.raise_for_status()
        result = self._parser_response(r)
        current_revision = result['current_revision']
        commit = result['revisions'][current_revision]['commit']

        if len(commit['parents']) > 1:
            raise MergeCommitError('%s is merge commit, abandon it!' % url.replace('a/changes', '#/c'))

        return commit['message']

    def fetch_project_branches(self, project):
        if not project:
            raise ValueError('project cannot empty!!!')

        params = self.generate_param()
        project = project.replace('/', '%2F')
        url = self.base_url + '/projects/' + project + '/branches'
        logging.debug(url)
        r = self.s.get(url, params=params)
        try:
            branches = self._parser_response(r)
        except Exception as e:
            logging.exception("Must Handle this exception")
            return None

        logging.info('status_code: ' + str(r.status_code) + ', branch number: ' + str(len(branches)))
        branch_list = []
        # parse branch
        for branch in branches:
            ref = branch['ref']
            if ref.startswith('refs/heads'):
                remote_branch = ref[11:]
                branch_list.append(remote_branch)

        return branch_list

    def create_branch(self, project, initial_revision, new_branch_name):
        """创建分支"""

        headers = {'Accept': 'application/json',
                   'Accept-Encoding': 'gzip'}
        project = project.replace('/', '%2F')
        new_branch_name = new_branch_name.replace('/', '%2F')
        url = self.base_url + GERRIT_API_PROJECTS + project + '/branches/' + new_branch_name
        data = {'revision': initial_revision}
        r = self.s.put(url, headers=headers, json=data)
        logging.info(self._parser_response(r))
        return self._parser_response(r)

    def query(self, status="merged", project=None, branch=None, page=0):
        query_url = self.base_url + GERRIT_API_CHANGES

        query_url += '?q=status:' + status
        if project:
            query_url += '+project:' + project

        if branch:
            query_url += '+branch:' + branch

        query_url += '&n=25&O=0&S=' + str(page * 25)

        r = self.s.get(query_url)
        r.raise_for_status()
        logging.debug('query url = ' + r.url)
        return self._parser_response(r)

    def _parser_response(self, response):
        """Strip off Gerrit's magic prefix and decode a response.
        """
        content = response.text.strip()
        response.raise_for_status()
        if content.startswith(GERRIT_MAGIC_JSON_PREFIX):
            content = content[len(GERRIT_MAGIC_JSON_PREFIX):]

        try:
            return json.loads(content)
        except TypeError:
            logging.error('Invalid json content: %s' % content)
            raise
        except ValueError:
            logging.error('Invalid json content: %s' % content)
            raise

    def generate_param(self):
        return {'n': '5000', 's': '0'}


class ODCGerrit(Gerrit):
    def __init__(self, url):
        super(ODCGerrit, self).__init__(url)
        #self.s.auth = HTTPBasicAuth(config.get_user_profile()['username'], config.get_odc_key())

    def generate_param(self):
        return {'n': '5000', 'S': '0'}


class GerritFactory:
    @staticmethod
    def get_gerrit(url):
        return ODCGerrit(url)
        # if url.startswith('http://odc'):
        #     return ODCGerrit(url)
        # else:
        #     return Gerrit(url)
