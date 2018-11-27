#!/usr/bin/python3
# coding: utf-8
import sqlite3
from configs import config
from common import flog
import logging


class AbkitDb:
    def __init__(self):
        self.table_name = 'watched_history'
        self.init_db()

    def init_db(self):
        """ init abkit.db and watched_history table"""
        co = sqlite3.connect(config.PATH_ABKIT_DATABASE)

        create_watched_history_table_str = '''create table %s
            ( id integer primary key autoincrement not null,
              watched_id integer not null,
              project_id text not null,
              review_id integer not null,
              review_url text,
              update_time text not null)''' % self.table_name

        # if table watched_history not exits, create it
        cursor = co.cursor()
        cursor.execute("select * from sqlite_master where type='table' and name='%s'" % self.table_name)
        result = cursor.fetchone()
        if not result:
            cursor.execute(create_watched_history_table_str)

        # close cursor
        cursor.close()

        # maybe commit
        co.commit()

        # close db
        co.close()

    def check_inited(self, watched_id, project_id):
        co = sqlite3.connect(config.PATH_ABKIT_DATABASE)
        cursor = co.cursor()

        select_str = "select review_id from %s where watched_id=%s and project_id='%s' " \
                     "order by update_time desc limit 1" \
                     % (self.table_name, watched_id, project_id)
        cursor.execute(select_str)
        db_fetch_result = cursor.fetchone()

        cursor.close()
        co.close()

        if db_fetch_result:
            return True

        return False

    def get_latest_review_id(self, watched_id, project_id):
        """
        从数据库从查找task_id, project_id所对应的最新review_id
        :param watched_id: 监视任务id
        :param project_id: 代码库id
        :return: 返回最新review_id，否则None
        """
        co = sqlite3.connect(config.PATH_ABKIT_DATABASE)
        cursor = co.cursor()

        cursor.execute('select review_id from %s where watched_id=%s and project_id="%s" '
                       'order by update_time desc limit 1'
                       % (self.table_name, watched_id, project_id))
        db_fetch_result = cursor.fetchone()

        cursor.close()
        co.close()

        if db_fetch_result:
            return db_fetch_result[0]

        return None

    def update_watched_history(self, watched_id, project_id, review_id, review_url, update_time):
        """
        更新监视任务数据库
        :param watched_id: 监视任务id
        :param project_id: project name 转换为的id
        :param review_id: 提交记录id
        :param review_url: 提交记录链接
        :param update_time: 更新时间
        :return:
        """
        co = sqlite3.connect(config.PATH_ABKIT_DATABASE)
        cursor = co.cursor()

        insert_str = "insert into %s (review_id, watched_id, review_url, update_time, project_id) " \
                     "values(%s, %s, '%s', '%s', '%s')" % \
                     (self.table_name, review_id, watched_id, review_url, update_time, project_id)

        logging.info(insert_str)

        cursor.execute(insert_str)

        cursor.close()
        co.commit()
        co.close()