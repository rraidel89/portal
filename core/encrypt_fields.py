# -*- coding: utf-8 -*-

import types
import base64

from Crypto import Random
from Crypto.Cipher import AES

from django.db import models
from django.conf import settings

class EncryptedField(models.Field):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        self.prefix = kwargs.pop('prefix', '_')
        super(EncryptedField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return 'TextField'

    def to_python(self, value):
        if value is None or not isinstance(value, types.StringTypes):
            return value

        if self.is_encrypted(value):
            value = value[len(self.prefix):]    # cut prefix
            value = base64.b64decode(value)

            iv, encrypted = value[:AES.block_size], value[AES.block_size:]  # extract iv

            crypto = AES.new(settings.FIELD_ENCRYPTION_KEY[:32], AES.MODE_CBC, iv)
            raw_decrypted = crypto.decrypt(encrypted)
            value = raw_decrypted.rstrip("\0").decode('unicode_escape')

        return value

    def get_db_prep_value(self, value, connection, prepared=False):
        if not prepared:
            iv = Random.new().read(AES.block_size)
            crypto = AES.new(settings.FIELD_ENCRYPTION_KEY[:32], AES.MODE_CBC, iv)

            if isinstance(value, types.StringTypes):
                value = value.encode('unicode_escape')
                value = value.encode('ascii')
            else:
                value = str(value)

            tag_value = (value + (AES.block_size - len(value) % AES.block_size) * "\0")
            value = self.prefix + base64.b64encode(iv + crypto.encrypt(tag_value))

        return value

    def is_encrypted(self, value):
        """checks if a string is encrypted against a static predefined prefix"""
        if self.prefix and value.startswith(self.prefix):
            return True
        else:
            return False