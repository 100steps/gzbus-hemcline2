#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @author: jiehua233@gmail.com
#

import sys
import time
import urlparse
import requests
import redis
import ujson as json
import crypt
import config
from datetime import datetime

reload(sys)
sys.setdefaultencoding("utf8")


""" 全局配置常量 """
CRYPT_IV = '\x01\x09\x08\x02\x00\x07\x00\x05'
SITE_MOBILE = ("http://g3.gzyyjt.net:7007/unicom/", "MOKFV700")
SITE_TELECOM = ("http://info-3g.gzyyjt.net:8008/unicom/", "B4AHQK2G")
SITE_UNICOM = ("http://info.gzyyjt.net:9009/unicom/", "XTEIZDDM")

""" 加解密 """
cipher = crypt.DESCipher(CRYPT_IV, SITE_MOBILE[1])


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
    enc_data = cipher.encrypt(params)
    url = urlparse.urljoin(SITE_MOBILE[0], "Bus")
    r = requests.post(url, data=enc_data)
    return cipher.decrypt(r.text)


def main():
    rpool = redis.ConnectionPool(**config.REDIS)
    rds = redis.StrictRedis(connection_pool=rpool)
    while True:
        start = time.time()
        print datetime.now(), "query bus..."
        bus_data = getbus()
        print datetime.now(), "get result in %.2fs" % (time.time() - start)
        rds.set(config.REDISKEY, json.dumps(bus_data))
        time.sleep(config.FREQUENCY)


if __name__ == "__main__":
    main()
