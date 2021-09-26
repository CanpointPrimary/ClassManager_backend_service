#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/8/5
# Author: gray

"""
路径函数 - 用户相关
"""

import secrets

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.constants import DBConst, RespError
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.security import AESCrypto, WXBizDataCrypt
from app.exceptions import BizHTTPException


router = APIRouter()

TELEPHONE_REGEX = r'^1[358]\d{9}$|^147\d{8}$|^179\d{8}$'


@router.get('/info', summary='查询用户基本信息')
def get_user_basic_info(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
) -> JSONResponse:
    """
    查询用户在 当前所在班级的 信息
    """
    user_id = int(token.sub)
    cur_member_id = token.member_id
    cur_member = crud.class_member.get_current_member(db, user_id, cur_member_id)
    return schemas.Response(data=cur_member)


@router.post('/telephone/sms_captcha/request', summary='请求手机短信验证码')
def send_sms_captcha(
    request_id: int = Depends(deps.get_request_id),
    _: schemas.TokenPayload = Depends(deps.get_activated),
    redis: Redis = Depends(deps.get_redis),
    telephone: str = Body(
        ..., regex=TELEPHONE_REGEX, embed=True, description='电话号码'
    ),
) -> JSONResponse:
    """
    通过短信发送手机号验证码
    """
    # 从Redis获取该手机号对应的 send_flag，
    # 若 send_flag 已存在则判定为发送过于频繁，此时不予发送短信
    send_flag = redis.get(f'send_flag_{telephone}')
    if send_flag:
        raise BizHTTPException(*RespError.USER_REQUESTS_TOO_FREQUENTLY)
    # 生成随机验证码
    captcha = secrets.randbelow(999999)
    # 向celery推送短信发送任务
    celery_app.send_task(
        'send_sms_captcha',
        args=[
            request_id,
            telephone,
            captcha,
            settings.SMS_CAPTCHA_EXPIRE_SECONDS // 60,
        ],
        queue='main-queue',
    )
    # 存储 send_flag 和 验证码 到Redis
    redis.setex(f'send_flag_{telephone}', settings.SEND_SMS_INTERVAL_SECONDS, 1)
    redis.setex(
        f'sms_captcha_{telephone}', settings.SMS_CAPTCHA_EXPIRE_SECONDS, captcha
    )
    return schemas.Response()


@router.get('/telephone', summary='获取用户手机号')
def get_user_telephone(
    token: schemas.TokenPayload = Depends(deps.get_activated),
    encrypt_data: str = Query(..., description='加密数据'),
    iv: str = Query(..., description='加密向量'),
) -> JSONResponse:
    """
    获取用户手机号
    """
    session_key = AESCrypto.decrypt(token.sub_sign,
                                    settings.AES_KEY, settings.AES_IV)
    pc = WXBizDataCrypt(settings.MINI_PROGRAM_APP_ID, session_key)
    decrypted = pc.decrypt(encrypt_data, iv)
    return schemas.Response(data=decrypted)


@router.put('/classes/{member_id}', summary='用户切换所在班级')
def switch_class(
    token: schemas.TokenPayload = Depends(deps.get_activated),
    db: Session = Depends(deps.get_db),
    member_id: int = Path(..., description='目标班级的成员id'),
) -> JSONResponse:
    """
    用户切换所在班级
    """
    if member_id == token.member_id:
        return schemas.Response()
    user_id = int(token.sub)
    if not crud.class_member.member_exists(db, member_id, user_id):
        raise BizHTTPException(*RespError.CLASS_MEMBER_NOT_FOUND)
    crud.user.update_current_member(db, user_id, member_id)
    return schemas.Response()


@router.get('/classes', summary='查询用户已加入的班级列表')
def get_already_in_class_list(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
    page: int = Query(..., gt=0, description='页码'),
    page_size: int = Query(..., gt=0, le=100, description='页数据量'),
) -> JSONResponse:
    """
    查询用户已加入的班级列表
    """
    user_id = int(token.sub)
    result_list = crud.class_member.get_class_list(db, user_id, page, page_size)
    resp_data = deps.handle_paging_data(result_list, page, page_size)
    return schemas.Response(data=resp_data)


@router.get('/requested_classes', summary='查询用户待审核的班级列表')
def get_reviewing_classes(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
    page: int = Query(..., gt=0, description='页码'),
    page_size: int = Query(..., gt=0, le=100, description='页数据量'),
    rejected: bool = Query(False, description='是否包含未通过的班级申请'),
) -> JSONResponse:
    """
    查询用户待审核的班级列表
    """
    user_id = int(token.sub)
    result_list = crud.apply4class.get_reviewing_list(
        db, user_id, page, page_size, rejected
    )
    resp_data = deps.handle_paging_data(result_list, page, page_size)
    return schemas.Response(data=resp_data)


@router.get('/classes/class_members', summary='查询用户所在班的班级成员信息')
def get_class_members_list(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
) -> JSONResponse:
    """
    查询用户所在班的班级成员信息
    """
    if not token.member_id:
        return schemas.Response(data=None)
    cur_member = crud.class_member.get_class_id(db, token.member_id)
    if not cur_member:
        return schemas.Response(data=None)
    class_id = cur_member.class_id
    member_list = crud.class_member.get_class_members(db, class_id)
    teacher_list = [x for x in member_list if x.member_role != DBConst.STUDENT]
    student_list = [x for x in member_list if x.member_role == DBConst.STUDENT]
    teacher_list.sort(key=lambda x: x.member_role)
    data = {'teachers': teacher_list, 'students': student_list}
    return schemas.Response(data=data)
