import requests
import random
from hashlib import md5
import logging

class Client:
    def __init__(self, appid: str, appkey: str, endpoint: str = 'http://api.fanyi.baidu.com'):
        self.appid = appid
        self.appkey = appkey
        self.endpoint = endpoint
        self.path = '/api/trans/vip/translate'
        self.url = self.endpoint + self.path

    def translate(self, text: str, from_lang: str = 'auto', to_lang: str = 'jp') -> str:
        salt = random.randint(32768, 65536)
        sign = md5((self.appid + text + str(salt) + self.appkey).encode('utf-8')).hexdigest()
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'appid': self.appid,
            'q': text,
            'from': from_lang,
            'to': to_lang,
            'salt': salt,
            'sign': sign
        }
        try:
            r = requests.post(self.url, params=payload, headers=headers, timeout=5)
            result = r.json()
            if 'trans_result' in result:
                return '\n'.join([item['dst'] for item in result['trans_result']])
            else:
                return text
        except Exception as e:
            return text
