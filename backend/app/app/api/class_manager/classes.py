#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/7/29
# Author: gray

"""
路径函数 - 班级相关
"""

import base64
import json
from typing import Any, List

import requests
from fastapi import APIRouter, Depends, Body, Path, Query
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError
from redis import Redis
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.constants import DBConst, RespError
from app.core.config import settings
from app.exceptions import BizHTTPException
from app.models import Apply4Class, ClassMember, Group, GroupMember


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
        raise BizHTTPException(*RespError.INVALID_CODE)
    return class_


def get_subject(
    db: Session = Depends(deps.get_db),
    subject_id: int = Body(..., embed=True, description='任教科目'),
) -> int:
    """
    校验学科是否存在
    """
    if not crud.subject.subject_exists(db, subject_id):
        raise BizHTTPException(*RespError.INVALID_SUBJECT)
    return subject_id


def get_family_relation(
    db: Session = Depends(deps.get_db),
    family_relation: str = Body(..., embed=True, description='亲属关系'),
) -> str:
    """
    校验亲属关系是否存在
    """
    if not crud.sys_config.family_relation_exists(db, family_relation):
        raise BizHTTPException(*RespError.INVALID_FAMILY_RELATION)
    return family_relation


def get_exists_apply(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
    apply_id: int = Path(..., description='已提交的入班申请id'),
) -> Row:
    """
    查询已提交的入班申请信息
    """
    user_id = int(token.sub)
    apply = crud.apply4class.get_apply_by_id(db, user_id, apply_id)
    if not apply:
        raise BizHTTPException(*RespError.INVALID_CLASS_APPLY)
    return apply


@router.post('/teachers/join_requests', summary='提交教师端入班申请')
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
    提交教师入班申请
    """
    return teacher_join_class(db, token, name, subject_id, telephone, class_)


@router.put('/teachers/join_requests/{apply_id}', summary='重新提交教师入班申请')
def teacher_reapply_into_class(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
    apply: Row = Depends(get_exists_apply),
) -> JSONResponse:
    """
    重新提交教师入班申请
    """
    name = apply.name
    telephone = apply.telephone
    subject_id = get_subject(db, apply.subject_id)
    class_ = get_class_by_code(db, apply.class_id)
    return teacher_join_class(db, token, name, subject_id, telephone, class_)


def teacher_join_class(
    db, token, name, subject_id, telephone, class_
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
        headteacher = ClassMember(class_id=class_.id, user_id=user_id,
                                  name=name, member_role=DBConst.HEADTEACHER,
                                  subject_id=subject_id, telephone=telephone)
        crud.class_member.create(db, obj_in=headteacher)
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
        teacher = ClassMember(class_id=class_.id, user_id=user_id, name=name,
                              member_role=DBConst.TEACHER,
                              subject_id=subject_id, telephone=telephone)
        crud.class_member.create(db, obj_in=teacher)
        return schemas.Response()
    # 提交申请信息入库
    apply = Apply4Class(name=name, user_id=user_id, class_id=class_.id,
                        subject_id=subject_id, telephone=telephone)
    crud.apply4class.create(db, obj_in=apply)
    return schemas.Response()


@router.post('/students/join_requests', summary='提交学生端入班申请')
def student_apply_into_class(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
    name: str = Body(..., description='姓名'),
    family_relation: str = Depends(get_family_relation),
    telephone: str = Body(..., regex=TELEPHONE_REGEX, description='电话号码'),
    class_: Row = Depends(get_class_by_code),
    _: int = Depends(validate_sms_captcha),
) -> JSONResponse:
    """
    提交学生入班申请
    """
    return student_into_class(db, token, name, family_relation, telephone, class_)


@router.put('/students/join_requests/{apply_id}', summary='重新提交学生入班申请')
def student_reapply_into_class(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
    apply: Row = Depends(get_exists_apply),
) -> JSONResponse:
    """
    重新提交学生入班申请
    """
    name = apply.name
    telephone = apply.telephone
    family_relation = get_family_relation(db, apply.family_relation)
    class_ = get_class_by_code(db, apply.class_id)
    return student_into_class(db, token, name, family_relation, telephone, class_)


def student_into_class(
    db, token, name, family_relation, telephone, class_
) -> JSONResponse:
    """
    提交学生入班申请
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
        student = ClassMember(class_id=class_.id, user_id=user_id, name=name,
                              member_role=DBConst.STUDENT, telephone=telephone,
                              family_relation=family_relation)
        crud.class_member.create(db, obj_in=student)
        return schemas.Response()
    # 提交入班申请
    apply = Apply4Class(name=name, user_id=user_id, class_id=class_.id,
                        family_relation=family_relation, telephone=telephone)
    crud.apply4class.create(db, obj_in=apply)
    return schemas.Response()


@router.post('/class_codes/query', summary='根据班主任的电话号码获取其班级的班级码')
def get_class_id_by_telephone(
    db: Session = Depends(deps.get_db),
    _: schemas.TokenPayload = Depends(deps.get_activated),
    telephone: str = Body(
        ..., regex=TELEPHONE_REGEX, embed=True, description='电话号码'
    ),
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
    cur_member_id = token.member_id
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
    page: str = Query(None, description='跳转页面链接'),
) -> JSONResponse:
    """
    生成邀请入班的小程序码
    """
    cur_member_id = token.member_id
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


@router.get('/invitor/{member_id}/invitation', summary='根据邀请人id查询邀请入班信息')
def get_invitation_info(
    db: Session = Depends(deps.get_db),
    _: schemas.TokenPayload = Depends(deps.get_activated),
    member_id: str = Path(..., description='邀请人id'),
) -> JSONResponse:
    """
    根据邀请人id查询邀请入班信息
    """
    # 邀请人所在班的 班级码、用户在班角色、班级所属学校、邀请人名称
    cur_member = crud.class_member.get_current_member(db, member_id)
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


@router.put('/', summary='修改入班是否需要审核')
def update_audit_need_for_class_joining(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_headteacher),
    need_audit: bool = Body(..., embed=True, description='入班是否需要审核'),
) -> JSONResponse:
    """
    修改入班是否需要审核
    """
    cur_member_id = token.member_id
    crud.class_.update_audit_need_for_joining(db, cur_member_id, need_audit)
    return schemas.Response()


@router.delete('/class_members/{member_id}', summary='删除班级成员')
def delete_class_member(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_class_member),
    member_id: int = Path(..., description='要删除的班级成员的成员id'),
) -> JSONResponse:
    """
    删除班级成员
    """
    if token.member_role == DBConst.HEADTEACHER and member_id == token.member_id:
        raise BizHTTPException(*RespError.HEADTEACHER_DELETE)
    if token.member_role != DBConst.HEADTEACHER and member_id != token.member_id:
        raise BizHTTPException(*RespError.AUTHORIZATION_DENIED)
    crud.class_member.delete_member(db, member_id)
    return schemas.Response()


@router.put('/class_members/{member_id}', summary='修改班级成员信息')
def update_member(
    class_member: schemas.ClassMember = Body(..., description='班级成员信息'),
    db: Session = Depends(deps.get_class_member),
    token: schemas.TokenPayload = Depends(deps.get_db),
    member_id: int = Path(..., description='要修改的班级成员的成员id'),
) -> JSONResponse:
    if not class_member.subject_id and not class_member.family_relation:
        raise BizHTTPException(*RespError.MISSING_PARAMETER)
    # 如果用户不是班主任也不是修改自己信息
    if token.member_role != DBConst.HEADTEACHER and member_id != token.member_id:
        raise BizHTTPException(*RespError.AUTHORIZATION_DENIED)
    target_member = crud.class_member.get_member_info(member_id)
    if not target_member or target_member.is_delete:
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    if (
        target_member.member_role == DBConst.STUDENT
        and not class_member.family_relation
    ):
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    if (
        target_member.member_role != DBConst.STUDENT
        and not class_member.subject_id
    ):
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    crud.class_member.update_member(db, member_id, class_member)
    return schemas.Response()


@router.get('/join_requests', summary='查询当前所在班级的入班审核记录')
def get_join_requests(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
) -> JSONResponse:
    """
    查询当前所在班级的入班审核记录
    """
    apply_record = crud.apply4class.get_apply_records(db, token.class_id)
    reviewing = [x for x in apply_record if x.result == DBConst.REVIEWING]
    reviewed = [x for x in apply_record if x.result != DBConst.REVIEWING]
    return schemas.Response(data={'reviewing': reviewing, 'reviewed': reviewed})


@router.put('/join_requests/{apply_id}', summary='审核入班申请')
def review_join_request(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
    apply_id: int = Path(..., description='入班申请id'),
    passed: bool = Body(..., description='是否通过'),
) -> JSONResponse:
    """
    审核入班申请
    """
    apply = crud.apply4class.is_apply_reviewing(db, apply_id, token.class_id)
    if not apply:
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 若申请结果不为 审核中 则返回 该申请已被审核
    if apply.result != DBConst.REVIEWING:
        raise BizHTTPException(*RespError.REVIEWED_APPLY)
    result = DBConst.PASS if passed else DBConst.REJECT
    crud.apply4class.update_apply_result(db, apply_id, token.member_id, result)
    return schemas.Response()


@router.get('/students/names', summary='查询班级所有学生姓名')
def get_class_stu_names(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
) -> JSONResponse:
    """
    查询班级所有学生姓名
    """
    stu_names = crud.class_member.get_stu_names(db, token.class_id)
    return schemas.Response(data=stu_names)


@router.get('/groups', summary='查询当前所在班级的班级小组信息')
def get_groups(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
) -> JSONResponse:
    """
    查询当前所在班级的班级小组信息
    """
    groups = crud.group.get_class_groups(db, token.class_id)
    return schemas.Response(data=groups)


@router.get('/groups/{group_id}/students', summary='查询小组所有学生姓名')
def get_group_members(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
    group_id: int = Path(..., description='小组id'),
) -> JSONResponse:
    """
    查询小组所有学生姓名
    """
    stu_names = crud.group_member.get_members_of_group(db, token.class_id, group_id)
    return schemas.Response(data=stu_names)


@router.post('/groups', summary='新建班级小组')
def add_class_group(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_headteacher),
    name: str = Body(..., min_length=1, max_length=10, description='小组名称'),
    stu_names: List[str] = Body(..., description='学生姓名列表'),
) -> JSONResponse:
    """
    新建班级小组
    """
    # 校验当前班级是否已存在同名小组，若已存在则返回 `班级小组已存在`
    if crud.group.group_exists(db, token.class_id, name):
        raise BizHTTPException(*RespError.GROUP_EXISTS)
    # 校验学生是否都已在班
    at_class_names = crud.class_member.get_stu_names(db, token.class_id, stu_names)
    if len(at_class_names) != len(stu_names):
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 新建小组入库
    group = Group(name=name, class_id=token.class_id)
    group = crud.group.create(db, obj_in=group)
    # 新建组员入库
    group_members = [
        GroupMember(group_id=group.id, name=stu_name)
        for stu_name in stu_names
    ]
    db.add_all(group_members)
    db.commit()
    return schemas.Response()


@router.put('/groups/{group_id}', summary='更新班级小组信息')
def update_group(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_headteacher),
    group_id: int = Path(..., description='小组id'),
    name: str = Body(..., min_length=1, max_length=10, description='小组名称'),
    stu_names: List[int] = Body(..., description='学生姓名列表'),
) -> JSONResponse:
    # 检查小组是否存在，若不存在则返回 `不存在的班级小组`
    if not crud.group.group_exists(db, class_id=token.class_id, group_id=group_id):
        raise BizHTTPException(*RespError.GROUP_NOT_FOUND)
    # 校验学生是否都已在班
    at_class_names = crud.class_member.get_stu_names(db, token.class_id, stu_names)
    if len(at_class_names) != len(stu_names):
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 更新小组名称k
    crud.group.update_group_name(group_id, name)
    # 更新小组成员
    # 删除
    names2del = crud.group_member.get_names2del(group_id, stu_names)
    names2del = [x.name for x in names2del]
    crud.group_member.delete_by_names(db, names2del) if names2del else ...
    # 修改 / 新建
    group_members = [
        {'group_id': group_id, 'name': stu_name}
        for stu_name in stu_names
    ]
    batch_upsert = insert(GroupMember).values(group_members)
    batch_upsert = batch_upsert.on_conflict_do_update(
        index_elements=[GroupMember.group_id, GroupMember.name],
        set_={'name': batch_upsert.excluded.name}
    )
    db.execute(batch_upsert)
    db.commit()
    return schemas.Response()


@router.delete('/groups/{group_id}', summary='删除小组')
def delete_group(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_headteacher),
    group_id: int = Path(..., description='小组id'),
) -> JSONResponse:
    """
    删除小组
    """
    if not crud.group.group_exists(db, class_id=token.class_id, group_id=group_id):
        raise BizHTTPException(*RespError.GROUP_NOT_FOUND)
    # 删除小组
    crud.group.delete_by_id(db, group_id)
    # 删除组员
    crud.group_member.delete_by_group_id(db, group_id)
    return schemas.Response()
