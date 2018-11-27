#!/usr/bin/python3
# coding: utf-8

from abc import ABCMeta, abstractmethod


class IFilter(metaclass=ABCMeta):
    @abstractmethod
    def filter(self, item):
        """
        是否过滤item
        :param item: 任意object
        :return: 满足过滤条件，返回True，否则返回False
        """
        pass
