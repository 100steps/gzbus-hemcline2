#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @author: jiehua233@gmail.com
#

""" 加解密 """

import base64
import urllib
import ujson as json

from Crypto.Cipher import DES


ciphers = {}


class DESCipher():
    """ DES加解密 """

    def __init__(self, iv, key):
        self.bs = DES.block_size
        self.iv = iv
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
        return json.loads(self._unpad(dec_data))

    def _pad(self, s):
        pad_len = self.bs - len(s) % self.bs
        return s + pad_len * chr(pad_len)

    def _unpad(self, s):
        return s[:-ord(s[-1])]
