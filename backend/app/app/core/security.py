"""
安全相关 工具模块
"""

import base64
import json
from datetime import datetime, timedelta
from typing import Any, Union

from Crypto.Cipher import AES
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

ALGORITHM = 'HS256'
BLOCK_SIZE = 16  # Bytes


def create_access_token(
    subject: Union[str, Any],
    flag: str,
    sub_sign: str,
    expires_delta: timedelta = None
) -> str:
    """
    生成 JWT Token

    Token payload
    -------------
    {
        'iss': 签发人,
        'aud': 受众群,
        'exp': 过期时间,
        'sub': 主体，此处即用户id,
        'flag': 加密后的 open_id
        'sub_sign': 加密后的 session_key
    }
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {
        'iss': 'PrimarySchoolDigitalTeachingCenter',
        'aud': 'ClassManager',
        'exp': expire,
        'sub': str(subject),
        'flag': flag,
        'sub_sign': sub_sign,
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=ALGORITHM
    )
    return encoded_jwt


class AESBase(object):
    @staticmethod
    def pad(s, block_size=BLOCK_SIZE):
        return s + (block_size - len(s) % block_size) \
               * chr(block_size - len(s) % block_size)

    @staticmethod
    def unpad(s):
        return s[:-ord(s[len(s) - 1:])]


class AESCrypto(AESBase):
    """
    AES加解密 CBC模式
    key 应为 16、24 或 32 位长度的字符串，分别对应 AES128、AES192 和 AES256
    iv 应为16位长度的字符串
    """
    @classmethod
    def encrypt(cls, raw: str, key: str, iv: str) -> str:
        raw = cls.pad(raw)
        # 字符串补位
        cipher = AES.new(key.encode('utf8'), AES.MODE_CBC, iv.encode('utf8'))
        encrypted_bytes = cipher.encrypt(raw.encode('utf8'))
        # 加密后得到的是bytes类型的数据，使用Base64进行编码,返回byte字符串
        encoded = base64.b64encode(encrypted_bytes)
        # 对byte字符串按utf-8进行解码
        encrypted = encoded.decode('utf8')
        return encrypted

    @classmethod
    def decrypt(cls, encrypted: str, key: str, iv: str) -> str:
        encrypted = encrypted.encode('utf8')
        encoded_bytes = base64.decodebytes(encrypted)
        # 将加密数据转换位bytes类型数据
        cipher = AES.new(key.encode('utf8'), AES.MODE_CBC, iv.encode('utf8'))
        decrypted = cipher.decrypt(encoded_bytes)
        # 去补位
        decrypted = cls.unpad(decrypted)
        decrypted = decrypted.decode('utf8')
        return decrypted


class WXBizDataCrypt(AESBase):
    """
    微信小程序开放数据解密

    Examples
    --------
    appId = 'appId'
    sessionKey = 'sessionKey'
    encryptedData = 'encryptedData'
    iv = 'iv'

    pc = WXBizDataCrypt(appId, sessionKey)

    print(pc.decrypt(encryptedData, iv))
    """
    def __init__(self, app_id, session_key):
        self.appId = app_id
        self.session_key = session_key

    def decrypt(self, encrypted_data, iv):
        session_key = base64.b64decode(self.session_key)
        encrypted_data = base64.b64decode(encrypted_data)
        iv = base64.b64decode(iv)

        cipher = AES.new(session_key, AES.MODE_CBC, iv)

        decrypted = json.loads(self.unpad(cipher.decrypt(encrypted_data)))

        if decrypted['watermark']['appid'] != self.appId:
            raise Exception('Invalid Buffer')

        return decrypted
