#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @author: jiehua233@gmail.com
#

import sys
import rsa
import time
import base64
import urllib
import logging
import urlparse
import gevent
import gevent.monkey
import requests
import redis
import ujson as json
import config
from Crypto.Cipher import DES


reload(sys)
sys.setdefaultencoding("utf8")
gevent.monkey.patch_all()
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


""" 全局配置常量 """
CRYPT_IV = '\x01\x09\x08\x02\x00\x07\x00\x05'
BUS_API = [
    # MOBILE" to slowly...
    "http://g3.gzyyjt.net:7007/unicom/",
    # TELECOM"
    "http://info-3g.gzyyjt.net:8008/unicom/",
    # UNICOM
    "http://info.gzyyjt.net:9009/unicom/",
]


""" 加解密 """
ciphers = {}


class DESCipher():
    """ DES加解密 """

    def __init__(self, key):
        self.bs = DES.block_size
        self.iv = CRYPT_IV
        self.key = key

    def encrypt(self, params):
        raw_data = self._pad(urllib.urlencode(params))
        cipher = DES.new(self.key, DES.MODE_CBC, self.iv)
        enc_data = base64.b64encode(cipher.encrypt(raw_data))
        return enc_data

    def decrypt(self, enc_str):
        enc_data = base64.b64decode(enc_str)
        cipher = DES.new(self.key, DES.MODE_CBC, self.iv)
        dec_data = cipher.decrypt(enc_data)
        try:
            return json.loads(self._unpad(dec_data))
        except ValueError:
            # deskey 过期, 重新初始化
            init_descipher()
            raise ValueError

    def _pad(self, s):
        pad_len = self.bs - len(s) % self.bs
        return s + pad_len * chr(pad_len)

    def _unpad(self, s):
        return s[:-ord(s[-1])]


def init_descipher():
    logging.info("Init DESCipher...")
    pubkey, prikey = rsa.newkeys(1024)
    p = bytearray.fromhex('00'+hex(pubkey.n)[2:-1]+'010001')
    p = base64.b64encode(p)
    for url in BUS_API:
        r = requests.post(urlparse.urljoin(url, "data"), data=p)
        key = rsa.decrypt(base64.b64decode(r.text), prikey)
        logging.info("Get deskey: %s from: %s", key, url)
        ciphers[urlparse.urljoin(url, "Bus")] = DESCipher(key)


def getbus():
    params = {
        "username": "android",
        "password": "123456",
        "IMSI": "460000290762763",
        "devNumber": "0000000029F6B0C400000000454D8D02VIXPZQKPIK",
        "version": "2.5.8",
        "devType": 0,
        "queryType": 1,
        "type": "line",
        "routeName": u"大学城2线".encode("gbk"),
        "oper": "detail",
    }
    jobs, start = [], time.time()
    for url in BUS_API:
        url = urlparse.urljoin(url, "Bus")
        enc_data = ciphers[url].encrypt(params)
        jobs.append(gevent.spawn(requests.post, url, data=enc_data))

    # 同时请求了三个接口，只要有一个返回就可以
    result = gevent.joinall(jobs, count=1)
    if len(result) >= 1:
        r = result[0].value
    else:
        logging.error("Get bus info no result: %s", result)
        return None

    logging.info("Get bus info from %s in %ss", r.url, time.time() - start)
    if r.status_code == requests.codes.ok:
        bus_data = ciphers[r.url].decrypt(r.text)
        return bus_data
    else:
        logging.error("get bus pos err: %s, msg: %s", r.status_code, r.text)
        return None


def main():
    init_descipher()
    rpool = redis.ConnectionPool(**config.REDIS)
    while True:
        rds = redis.StrictRedis(connection_pool=rpool)
        # 重试3次
        for _ in range(3):
            bus_data = getbus()
            if bus_data:
                rds.set(config.REDISKEY, json.dumps(bus_data))
                break

        time.sleep(config.FREQUENCY)


if __name__ == "__main__":
    main()
