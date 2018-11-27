#!/usr/bin/python3
# coding: utf-8


class ProjectInfo:
    """
    project_name + 所对应的branch
    """
    def __init__(self, dict_config):
        self.project = ""
        self.branch = ""
        self.parse_config(dict_config)

    def parse_config(self, dict_config):
        if not isinstance(dict_config, dict):
            raise TypeError("config must be dict object")
        self.project = dict_config['project']
        self.branch = dict_config['branch']

    def get_project(self):
        return self.project

    def get_branch(self):
        return self.branch

