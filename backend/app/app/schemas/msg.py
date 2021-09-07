"""
结构体模型类 - 外部接口报文 相关
"""

from pydantic import BaseModel


class BaseMsg(BaseModel):
    errcode: str = None
    errmsg: str = None


class Code2SessionMsg(BaseMsg):
    session_key: str = None
    openid: str = None


class WXAccessTokenMsg(BaseMsg):
    access_token: str = None
    expires_in: int = None


class WXUrlLinkMsg(BaseMsg):
    url_link: str = None
