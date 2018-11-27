#!/usr/bin/python3
# coding: utf-8


from configs.jobs.ifilter import IFilter
from configs.jobs.commit_items import CommitItem
import re


class DoNotSubmitFilter(IFilter):
    def __init__(self):
        self.magic_suffix = 'DoNotSubmit'

    def filter(self, item):
        if isinstance(item, CommitItem):
            message = item.get_message()
            if re.search(self.magic_suffix, message, re.I):
                return True
        return False

