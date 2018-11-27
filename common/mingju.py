#!/usr/bin/python3

import requests
from bs4 import BeautifulSoup
import random
import re

'''
古诗名句随机获取
'''

def generate_base_url():
    page_random = random.randint(1, 115)
    url = 'http://so.gushiwen.org/mingju/Default.aspx?p=%s&c=&t=' % page_random

    return url

r = requests.get(generate_base_url())
r.raise_for_status()

while r.status_code != 200:
    r = requests.get(generate_base_url())

soup = BeautifulSoup(r.text, 'html.parser')

results = soup('a', href=re.compile(r'/mingju/juv_\d+'))

index_random = random.randint(0, len(results)-1)


print(results[index_random].string)
