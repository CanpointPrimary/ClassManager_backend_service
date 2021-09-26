import json
import os
import traceback
from typing import Any

import requests
from pydantic import ValidationError
from raven import Client
from celery.signals import beat_init
from celery.utils.log import get_task_logger
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import \
    TencentCloudSDKException
# 导入对应产品模块的client models。
from tencentcloud.sms.v20210111 import sms_client, models
# 导入可选配置类
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile

from app import schemas
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.internal import APIGateway
from app.db.redis import redis
from app.db.session import SessionLocal


client_sentry = Client(settings.SENTRY_DSN)

logger = get_task_logger(__name__)
if os.path.exists('celerybeat-schedule'):
    os.remove('celerybeat-schedule')


@celery_app.task(name='send_sms_captcha')
def send_sms_captcha(
    request_id: str, telephone: str, captcha: int, expire: int
) -> None:
    """
    发送手机短信验证码

    Parameters:
        request_id : rid
        telephone : 手机号
        captcha : 验证码
        expire : 过期时间，单位：分钟
    """
    try:
        # 必要步骤：
        # 实例化一个认证对象，入参需要传入腾讯云账户密钥对secretId，secretKey。
        # 这里采用的是从环境变量读取的方式，需要在环境变量中先设置这两个值。
        # 你也可以直接在代码中写死密钥对，但是小心不要将代码复制、上传或者分享给他人，
        # 以免泄露密钥对危及你的财产安全。
        # CAM密匙查询: https://console.cloud.tencent.com/cam/capi
        cred = credential.Credential(settings.TENCENT_CLOUD_SECRET_ID,
                                     settings.TENCENT_CLOUD_SECRET_KEY)
        # cred = credential.Credential(
        #     os.environ.get(""),
        #     os.environ.get("")
        # )
        # 实例化一个http选项，可选的，没有特殊需求可以跳过。
        httpProfile = HttpProfile()
        # 如果需要指定proxy访问接口，可以按照如下方式初始化hp
        # httpProfile = HttpProfile(proxy="http://用户名:密码@代理IP:代理端口")
        httpProfile.reqMethod = "POST"  # post请求(默认为post请求)
        httpProfile.reqTimeout = 30  # 请求超时时间，单位为秒(默认60秒)
        httpProfile.endpoint = "sms.tencentcloudapi.com"  # 指定接入地域域名(默认就近接入)
        # 非必要步骤:
        # 实例化一个客户端配置对象，可以指定超时时间等配置
        clientProfile = ClientProfile()
        clientProfile.signMethod = "TC3-HMAC-SHA256"  # 指定签名算法
        clientProfile.language = "en-US"
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品(以sms为例)的client对象
        # 第二个参数是地域信息，可以直接填写字符串ap-guangzhou，或者引用预设的常量
        client = sms_client.SmsClient(cred, "ap-guangzhou", clientProfile)
        # 实例化一个请求对象，根据调用的接口和实际情况，可以进一步设置请求参数
        # 你可以直接查询SDK源码确定SendSmsRequest有哪些属性可以设置
        # 属性可能是基本类型，也可能引用了另一个数据结构
        # 推荐使用IDE进行开发，可以方便的跳转查阅各个接口和数据结构的文档说明
        req = models.SendSmsRequest()
        # 基本类型的设置:
        # SDK采用的是指针风格指定参数，即使对于基本类型你也需要用指针来对参数赋值。
        # SDK提供对基本类型的指针引用封装函数
        # 帮助链接：
        # 短信控制台: https://console.cloud.tencent.com/smsv2
        # sms helper: https://cloud.tencent.com/document/product/382/3773
        # 短信应用ID: 短信SdkAppId在 [短信控制台] 添加应用后生成的实际SdkAppId，示例如1400006666
        req.SmsSdkAppId = settings.TENCENT_CLOUD_SMS_SDK_APPID
        # 短信签名内容: 使用 UTF-8 编码，必须填写已审核通过的签名，签名信息可登录 [短信控制台] 查看
        req.SignName = settings.TENCENT_CLOUD_SMS_SIGN
        # 短信码号扩展号: 默认未开通，如需开通请联系 [sms helper]
        req.ExtendCode = ""
        # 用户的 session 内容: 可以携带用户侧 ID 等上下文信息，server 会原样返回
        req.SessionContext = "xxx"
        # 国际/港澳台短信 senderid: 国内短信填空，默认未开通，如需开通请联系 [sms helper]
        req.SenderId = ""
        # 下发手机号码，采用 E.164 标准，+[国家或地区码][手机号]
        # 示例如：+8613711112222， 其中前面有一个+号 ，86为国家码，13711112222为手机号，最多不要超过200个手机号
        req.PhoneNumberSet = [f'+86{telephone}']
        # 模板 ID: 必须填写已审核通过的模板 ID。模板ID可登录 [短信控制台] 查看
        req.TemplateId = settings.TENCENT_CLOUD_SMS_TEMPLATE_ID
        # 模板参数: 若无模板参数，则设置为空
        req.TemplateParamSet = [str(captcha), str(expire)]
        # 通过client对象调用DescribeInstances方法发起请求。注意请求方法名与请求对象是对应的。
        # 返回的resp是一个DescribeInstancesResponse类的实例，与请求对象对应。
        resp = client.SendSms(req)
        # 输出json格式的字符串回包
        resp_text = resp.to_json_string(indent=2)
        if 'send success' not in resp_text:
            logger.error(f'rid={request_id} send sms captcha failed,'
                         f'message={resp_text}')
    except TencentCloudSDKException:
        logger.error(f'rid={request_id} send sms captcha failed,'
                     f'unexpected exception:\n{traceback.format_exc()}')


@celery_app.task(name='update_school_data')
def update_school_data() -> Any:
    db = SessionLocal()
    APIGateway.sync_school_data(db)


@celery_app.task(name='get_wx_mini_program_access_token')
def get_wx_mini_program_access_token() -> Any:
    """
    请求微信小程序平台 access_token
    """
    error = None
    params = {
        'grant_type': 'client_credential',
        'appid': settings.MINI_PROGRAM_APP_ID,
        'secret': settings.MINI_PROGRAM_APP_SECRET,
    }
    resp = requests.get(settings.WX_ACCESS_TOKEN_URL, params=params)
    try:
        resp_msg = schemas.WXAccessTokenMsg(**json.loads(resp.text))
    except (ValidationError, json.JSONDecodeError):
        error = resp_msg = 1
    if error or not resp_msg.access_token or not resp_msg.expires_in:
        logger.error(
            f'get WX mini program access token failed,'
            f'status code={resp.status_code} message={resp.text}'
        )
        return
    if resp_msg.expires_in != settings.WX_ACCESS_TOKEN_EXPIRES:
        logger.warning(f'WX mini program access token expires may changed,'
                       f'expires_in={resp_msg.expires_in}')
    redis.set('wx_access_token', resp_msg.access_token)
    return resp_msg.access_token


@celery_app.on_after_configure.connect
def set_timing_task(sender, **_) -> None:
    """
    设置celery定时任务
    """
    period = settings.WX_ACCESS_TOKEN_EXPIRES
    period -= settings.WX_ACCESS_TOKEN_UPDATE_OFFSET
    sender.add_periodic_task(period,
                             get_wx_mini_program_access_token.s(),
                             name='update_wx_mini_program_access_token',
                             queue='main-queue')


@beat_init.connect
def when_beat_init(*_, **__) -> Any:
    """
    设置beat启动时worker执行到任务
    """
    celery_app.send_task('get_wx_mini_program_access_token', queue='main-queue')
