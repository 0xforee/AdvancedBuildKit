#!/usr/bin/python3
# coding: utf-8


class CommitItem:
    """
    提交信息所对应的结构体
    TODO: 使用__hash__, __eq__来过滤去重
    """
    def __init__(self, id, message, review_url):
        self.id = id
        self.message = message
        self.review_url = review_url

    def get_message(self):
        return self.message

    def get_review_url(self):
        return self.review_url

    def get_id(self):
        return self.id

    def __str__(self):
        return "id = " + self.id + ', message = ' + self.message + ', review_url = ' + self.review_url
