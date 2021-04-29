import requests

from config import Config


# wechat SDK auth.code2Session
def WXSDK_jscode2session(code):
    wechat_url = 'https://api.weixin.qq.com/sns/jscode2session'
    wechat_data = {
        'appid': Config.AppId,
        'secret': Config.AppSecret,
        'js_code': code,
        'grant_type': 'authorization_code',
    }
    response = requests.get(wechat_url, params=wechat_data)
    if response.status_code == requests.codes.ok:
        return response.json()
