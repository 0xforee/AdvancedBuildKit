import requests
import json


class DingTalkRobot(object):

    def __init__(self, web_hook):
        self.web_hook = web_hook

    def send_msg(self, content, at_mobiles=None, is_at_all=False):
        if content:
            data = {'msgtype': 'text'}
            at = {}
            data['text'] = {'content': content}
        else:
            raise ValueError('msg cannot empty!!')

        if at_mobiles and isinstance(at_mobiles, list):
            at['atMobiles'] = at_mobiles

        if is_at_all:
            at['isAtAll'] = is_at_all

        if at:
            data['at'] = at

        self.post(data)

    def send_link(self, title, content, message_url, pic_url=None):
        if title and content and message_url:
            data = {'msgtype': 'link'}
            link = {}
        else:
            raise ValueError('title or content or message_url cannot empty!!!')

        link['title'] = title
        link['text'] = content
        link['messageUrl'] = message_url

        if pic_url:
            link['picUrl'] = pic_url

        data['link'] = link

        self.post(data)

    def send_markdown(self):
        pass

    def send_action_card(self):
        pass

    def send_feed_card(self):
        pass

    def post(self, data):
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        r = requests.post(self.web_hook, headers=headers, data=json.dumps(data))
        r.raise_for_status()

        print('result_code = ' + str(r.status_code) + ', result = ' + r.text)

