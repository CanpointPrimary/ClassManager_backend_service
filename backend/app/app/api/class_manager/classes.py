#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/7/29
# Author: gray

"""
路径函数 - 班级相关
"""

import base64
import json
from typing import Any

import requests
from fastapi import APIRouter, Depends, Body, Path, Query
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError
from redis import Redis
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.constants import DBConst, RespError
from app.core.config import settings
from app.exceptions import BizHTTPException
from app.models import Apply4Class, Class, ClassMember


router = APIRouter()

TELEPHONE_REGEX = r'^1[358]\d{9}$|^147\d{8}$|^179\d{8}$'


def validate_sms_captcha(
    captcha: int = Body(..., description='验证码'),
    redis: Redis = Depends(deps.get_redis),
    telephone: str = Body(..., regex=TELEPHONE_REGEX, description='电话号码'),
) -> int:
    """
    校验短信验证码
    """
    key_name = f'sms_captcha_{telephone}'
    correct_captcha = redis.get(key_name)
    if not correct_captcha or str(captcha) != correct_captcha:
        raise BizHTTPException(*RespError.INCORRECT_CAPTCHA)
    redis.delete(key_name)
    return captcha


def get_class_by_code(
    db: Session = Depends(deps.get_db),
    class_code: int = Body(..., embed=True, description='班级码'),
) -> Row:
    """
    校验班级码是否有效，查询数据该班级码对应的班级是否存在
    """
    class_ = crud.class_.class_exists(db, class_id=class_code)
    if not class_:
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    return class_


def get_subject(
    db: Session = Depends(deps.get_db),
    subject_id: int = Body(..., embed=True, description='任教科目'),
):
    """
    校验学科是否存在
    """
    if not crud.subject.subject_exists(db, subject_id):
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    return subject_id


def get_family_relation(
    db: Session = Depends(deps.get_db),
    family_relation: str = Body(..., embed=True, description='亲属关系'),
) -> str:
    """
    校验亲属关系是否存在
    """
    if not crud.sys_config.family_relation_exists(db, family_relation):
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    return family_relation


@router.post('/teachers/join_request', summary='提交教师端入班申请')
def teacher_apply_into_class(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
    name: str = Body(..., description='姓名'),
    subject_id: int = Depends(get_subject),
    telephone: str = Body(..., regex=TELEPHONE_REGEX, description='电话号码'),
    class_: Row = Depends(get_class_by_code),
    _: int = Depends(validate_sms_captcha),
) -> JSONResponse:
    """
    提交教师端入班申请
    """
    user_id = int(token.sub)
    # 检查是否已在班
    is_exists = crud.class_member.is_teacher_in_class(db, user_id)
    if is_exists:
        raise BizHTTPException(
            RespError.DUPLICATE_TEACHER.status_code,
            RespError.DUPLICATE_TEACHER.statement,
            RespError.DUPLICATE_TEACHER.message.format(is_exists.name)
        )
    # 未在班的班主任直接入班
    if telephone == class_.contact:
        headteacher = ClassMember(
            class_id=class_.id,
            user_id=user_id,
            name=name,
            member_role=DBConst.HEADTEACHER,
            subject_id=subject_id,
            telephone=telephone,
        )
        headteacher = crud.class_member.create(db, obj_in=headteacher)
        if not token.user.current_member_id:
            crud.user.update_current_member(db, user_id, headteacher.id)
        return schemas.Response()
    # 检查老师是否已提交申请
    if crud.apply4class.teacher_apply_exists(db, user_id, class_.id):
        raise BizHTTPException(*RespError.DUPLICATE_APPLY)
    # 检查该科目是否已有任课老师
    teacher_exists = crud.class_member.subject_teacher_exists(
        db, class_id=class_.id, subject_id=subject_id
    )
    if teacher_exists:
        raise BizHTTPException(
            RespError.TEACHER_EXISTS.status_code,
            RespError.TEACHER_EXISTS.statement,
            RespError.TEACHER_EXISTS.message.format(teacher_exists.name)
        )
    # 如果该班级不需要审核，直接入班
    if not class_.need_audit:
        teacher = ClassMember(
            class_id=class_.id,
            user_id=user_id,
            name=name,
            member_role=DBConst.TEACHER,
            subject_id=subject_id,
            telephone=telephone,
        )
        teacher = crud.class_member.create(db, obj_in=teacher)
        if not token.user.current_member_id:
            crud.user.update_current_member(db, user_id, teacher.id)
        return schemas.Response()
    # 提交申请信息入库
    apply = Apply4Class(
        name=name,
        user_id=user_id,
        class_id=class_.id,
        subject_id=subject_id,
        telephone=telephone,
    )
    crud.apply4class.create(db, obj_in=apply)
    return schemas.Response()


@router.post('/students/join_request', summary='提交学生端入班申请')
def student_apply_into_class(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
    name: str = Body(..., description='姓名'),
    family_relation: str = Depends(get_family_relation),
    telephone: str = Body(..., regex=TELEPHONE_REGEX, description='电话号码'),
    class_: Class = Depends(get_class_by_code),
    _: int = Depends(validate_sms_captcha),
) -> JSONResponse:
    """
    提交学生端入班申请
    """
    user_id = int(token.sub)
    # 查询是否已在班
    if crud.class_member.is_student_in_class(db, user_id, name):
        raise BizHTTPException(*RespError.DUPLICATE_MEMBER)
    # 查询同一学生是否已提交申请
    apply_lst = crud.apply4class.student_apply_exists(db, user_id, class_.id)
    if [x for x in apply_lst if x.name == name]:
        raise BizHTTPException(*RespError.DUPLICATE_APPLY)
    # 查询在同一班级提交申请的数量
    if len(apply_lst) >= 5:
        raise BizHTTPException(*RespError.TOO_MANY_APPLY)
    # 如果该班级不需要审核，直接入班
    if not class_.need_audit:
        student = ClassMember(
            class_id=class_.id,
            user_id=user_id,
            name=name,
            member_role=DBConst.STUDENT,
            family_relation=family_relation,
            telephone=telephone,
        )
        student = crud.class_member.create(student)
        if not token.user.current_member_id:
            crud.user.update_current_member(db, user_id, student.id)
        return schemas.Response()
    # 提交入班申请
    apply = Apply4Class(
        name=name,
        user_id=user_id,
        class_id=class_.id,
        family_relation=family_relation,
        telephone=telephone,
    )
    crud.apply4class.create(db, obj_in=apply)
    return schemas.Response()


@router.post('/class_codes/query', summary='根据班主任的电话号码获取其班级的班级码')
def get_class_id_by_telephone(
    db: Session = Depends(deps.get_db),
    _: schemas.TokenPayload = Depends(deps.get_activated),
    telephone: str = Body(..., regex=TELEPHONE_REGEX,
                          embed=True, description='电话号码'),
) -> Any:
    """
    根据班主任的电话号码获取其班级的班级码
    """
    return crud.class_.get_class_id_by_telephone(db, telephone)


@router.get('/{class_code}/family_members/', summary='获取学生在该班的所有亲属信息')
def get_family_members(
    db: Session = Depends(deps.get_db),
    _: schemas.TokenPayload = Depends(deps.get_activated),
    class_code: int = Path(..., description='班级码'),
    name: str = Query(..., description='学生姓名'),
) -> Any:
    """
    根据班级码及学生姓名获取该学生在该班级的亲属的信息
    """
    return crud.class_member.get_family_members(db, class_code, name)


@router.get('/invitation/links', summary='生成邀请入班链接')
def get_invitation_links(
    request_id: str = Depends(deps.get_request_id),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
    redis: Redis = Depends(deps.get_redis),
    path: str = Query(None, description='跳转页面链接'),
) -> JSONResponse:
    """
    生成邀请入班链接
    """
    error = None
    cur_member_id = token.user.current_member_id
    # 请求微信小程序链接
    wx_access_token = redis.get('wx_access_token')
    json_data = {
        'path': path, 'query': f'id={cur_member_id}', 'is_expire': True,
        'expire_type': 1, 'expire_interval': 7
    }
    resp = requests.post(settings.WX_GET_URL_LINK_URL, json=json_data,
                         params={'access_token': wx_access_token})
    try:
        resp_msg = schemas.WXUrlLinkMsg(**json.loads(resp.text))
    except (ValidationError, json.JSONDecodeError):
        error = resp_msg = 1
    if error or not resp_msg.url_link:
        logger.error(f'rid={request_id} get wx url link failed,'
                     f'status code={resp.status_code} message={resp.text}')
        raise BizHTTPException(*RespError.GEN_WX_URL_LINK_FAILED)
    return schemas.Response(data=resp_msg.url_link)


@router.get('/invitation/wxacode', summary='生成邀请入班的小程序码')
def get_invitation_wxacode(
    token: schemas.TokenPayload = Depends(deps.get_teacher),
    redis: Redis = Depends(deps.get_redis),
    page: str = Query(None, description='跳转页面连接'),
) -> JSONResponse:
    """
    生成邀请入班的小程序码
    """
    cur_member_id = token.user.current_member_id
    # 请求微信小程序码
    wx_access_token = redis.get('wx_access_token')
    json_data = {'scene': f'id={cur_member_id}', 'page': page}
    resp = requests.post(settings.WXACODE_GET_UNLIMITED_URL, json=json_data,
                         params={'access_token': wx_access_token}, stream=True)
    # 通过响应头判断响应结果
    content_type = resp.headers.get('Content-Type')
    if not content_type or 'image' not in content_type:
        logger.error(f'Generate wxacode failed,content_type={content_type},'
                     f'message={resp.text}')
        raise BizHTTPException(*RespError.GEN_WXACODE_FAILED)
    return schemas.Response(data=base64.b64encode(resp.content).decode())


@router.get('/invitor/{member_id}/invitation',
            summary='根据邀请人id查询邀请入班信息')
def get_invitation_info(
    db: Session = Depends(deps.get_db),
    _: schemas.TokenPayload = Depends(deps.get_activated),
    member_id: str = Path(..., description='邀请人id'),
) -> JSONResponse:
    """
    根据邀请人id查询邀请入班信息
    """
    # 邀请人所在班的 班级码、用户在班角色、班级所属学校、邀请人名称
    cur_member = crud.class_member.get_current_class_member(db, member_id)
    if not cur_member:
        raise BizHTTPException(*RespError.INVALID_INVITATION)
    if cur_member.member_role not in (DBConst.HEADTEACHER, DBConst.TEACHER):
        raise BizHTTPException(*RespError.AUTHORIZATION_DENIED)
    invitation_data = {
        'class_code': cur_member.class_id,
        'invitor_name': cur_member.name,
        'school_name': cur_member.school_name,
        'grade': cur_member.grade,
        'class': cur_member['class'],
    }
    return schemas.Response(data=invitation_data)
