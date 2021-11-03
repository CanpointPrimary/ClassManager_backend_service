#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/9/16
# Author: gray

"""
路径函数 - 校本作业 相关
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Set, Callable

from fastapi import APIRouter, Body, Depends, File, Path, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from app import crud, schemas, utils
from app.api import deps
from app.api.class_manager import upload
from app.constants import DBConst, RespError
from app.exceptions import BizHTTPException
from app.models import (
    FileInfo, FileReference, Homework, HomeworkAnswer, HomeworkAnswerStatus,
    HomeworkAssign, HomeworkEvaluate, HomeworkAnswerCheck, Message, MessageContent
)
from app.schemas import Str


router = APIRouter()

ALLOW_IMAGE_MIMES = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
}
IMAGE_SIZE_LIMIT = 10 * 1024 * 1024

ALLOW_VIDEO_MIMES = {
    'video/mp4': '.mp4',
    'video/x-flv': '.flv',
    'video/x-msvideo': '.avi',
    'video/x-ms-wmv': '.wmv',
    'video/quicktime': '.mov',
}
VIDEO_SIZE_LIMIT = 10 * 1024 * 1024
VIDEO_DURATION_LIMIT = 60

ALLOW_AUDIO_MIMES = {
    'audio/mpeg': '.mp3',
    'audio/aac': '.aac',
}
AUDIO_SIZE_LIMIT = 10 * 1024 * 1024

ALLOW_DOC_MIMES = {
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',  # noqa
    'text/plain': '.txt',
}
DOC_SIZE_LIMIT = 10 * 1024 * 1024

SCORE_ENUM_SET = {'A', 'B', 'C', 'D', 'E'}


class GetHomeworkDependency(object):
    def __init__(self, *extra_fields):
        self.__extra_fields = extra_fields

    def __call__(
        self,
        db=Depends(deps.get_db),
        homework_id: int = Path(..., description='作业id'),
    ) -> Row:
        return crud.homework.info(db, homework_id, *self.__extra_fields)


def homework_enabled_func(get_homework_dep: GetHomeworkDependency) -> Callable:
    def homework_enabled_di(homework: Row = Depends(get_homework_dep)) -> Row:
        """校验作业是否存在，是否被删除"""
        if not homework:
            raise BizHTTPException(*RespError.INVALID_PARAMETER)
        if homework.is_delete:
            raise BizHTTPException(*RespError.HOMEWORK_DELETED)
        return homework
    return homework_enabled_di


get_homework: Callable = homework_enabled_func(GetHomeworkDependency())
get_homework_end_time: Callable = homework_enabled_func(
    GetHomeworkDependency(Homework.end_time)
)
get_homework_info: Callable = homework_enabled_func(
    GetHomeworkDependency(Homework.end_time, Homework.title, Homework.desc)
)


@router.get('/classes/school_homeworks', summary='查询当前班级的作业列表')
def get_class_homeworks(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
    subject_id: int = Query(None, description='学科id'),
    page: int = Query(1, gt=0, description='页码'),
    page_size: int = Query(15, gt=0, le=100, description='页数据量'),
) -> JSONResponse:
    """查询当前班级的作业列表"""
    res_list = crud.homework_answer_status.get_teacher_homework_list(
        db, None, token.class_id, subject_id, page, page_size
    )
    resp_data = deps.handle_paging_data(res_list, page, page_size)
    return schemas.Response(data=resp_data)


@router.get('/members/school_homeworks', summary='查询当前班级成员的作业列表')
def get_user_homeworks(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_class_member),
    page: int = Query(1, gt=0, description='页码'),
    page_size: int = Query(15, gt=0, le=100, description='页数据量'),
) -> JSONResponse:
    """查询当前班级成员的作业列表"""
    # 学生视角
    if token.member_role == DBConst.STUDENT:
        res_list = crud.homework_answer_status.get_student_homework_list(
            db, token.member_id, token.class_id, page, page_size
        )
        resp_data = deps.handle_paging_data(res_list, page, page_size)
    # 教师视角
    else:
        res_list = crud.homework_answer_status.get_teacher_homework_list(
            db, int(token.sub), token.class_id, None, page, page_size
        )
        resp_data = deps.handle_paging_data(res_list, page, page_size)
    return schemas.Response(data=resp_data)


@router.get('/classes/school_homeworks/assignments/groups',
            summary='查询校本作业发送对象')
def get_homework_assign_available_groups(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
    pub_time: datetime = Query(..., description='作业发布时间'),
) -> JSONResponse:
    """查询校本作业发送对象"""
    resp_data = crud.homework_assign.get_homework_assign_available_groups(
        db, int(token.sub), token.subject_id, pub_time.date()
    )
    return schemas.Response(data=resp_data)


def check_homework_attachments(
    db: Session, homework: schemas.SchoolHomeworkAttachment
) -> List[int]:
    """校验作业引用附件是否存在，若不存在抛出异常"""
    attachment_existed_count = crud.file_info.count_homework_attachments(
        db, homework.images, homework.videos, homework.audios, homework.docs
    )
    attachment_count = (len(homework.images) + len(homework.videos)
                        + len(homework.audios) + len(homework.docs))
    if attachment_existed_count != attachment_count:
        raise BizHTTPException(*RespError.FILE_NOT_FOUND)
    attachment_ids = []
    attachment_ids.extend(homework.images)
    attachment_ids.extend(homework.videos)
    attachment_ids.extend(homework.audios)
    attachment_ids.extend(homework.docs)
    return attachment_ids


@router.post('/users/school_homeworks/assignments', summary='新建校本作业')
def assign_homework(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
    homework: schemas.SchoolHomeworkAssign = Body(..., description='作业信息'),
) -> JSONResponse:
    """新建校本作业"""
    # 校验 作业附件已上传
    attachment_ids = check_homework_attachments(db, homework)
    # 校验 每个班的作业发布范围只能指定一次
    class_scope_set = {group.class_id for group in homework.scope}  # 作业发布班级的集合
    if len(class_scope_set) != len(homework.scope):
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 校验 每个老师每天在每个班只能发布一次作业
    assigned_homework = crud.homework_assign.get_homework4the_day_assigned(
        db, int(token.sub), class_scope_set, homework.pub_time.date()
    )
    if assigned_homework:
        raise BizHTTPException(*RespError.HOMEWORK_ASSIGNED, data=assigned_homework)
    # 校验 发布人必须是要发布作业班级的对应科目的老师
    class_charge_list = crud.class_member.get_teacher_class_charge_list(
        db, int(token.sub), token.subject_id, class_scope_set
    )
    class_charge_set = {row.class_id for row in class_charge_list}  # 执教班级的集合
    if not class_scope_set.issubset(class_charge_set):
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 校验作业发布范围: 小组发布的作业小组存在，全班发布的作业该班级要有学生
    class_assign_list: List[int] = []                          # 全班发布的班级id列表
    group_assign_list: List[schemas.HomeworkAssignScope] = []  # 小组发布的小组发布列表
    _ = [
        group_assign_list.append(group) if group.groups
        else class_assign_list.append(group.class_id)
        for group in homework.scope
    ]
    valid_count: int = crud.homework_assign.validate_assign_scope(
        db, class_assign_list, group_assign_list
    )
    group_count = sum([len(scope.groups) for scope in group_assign_list])
    if valid_count != len(class_assign_list) + group_count:
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 数据入库
    # 新建作业数据
    new_homework = Homework(publisher_id=int(token.sub), subject_id=token.subject_id,
                            pub_time=homework.pub_time, end_time=homework.end_time,
                            title=homework.title, desc=homework.desc)
    try:
        new_homework = crud.homework.create(db, obj_in=new_homework,
                                            auto_commit=False)
        # 新建作业发送范围
        class_charge_map = {row.class_id: row.id for row in class_charge_list}
        create_homework_assign(db, new_homework.id, homework.scope)
        # 新建作业发布消息
        create_homework_assign_msg(db, new_homework.id, class_charge_map,
                                   class_assign_list, group_assign_list)
        # 新建作业附件引用
        new_file_refs = [
            FileReference(file_id=file_id, referenced_id=new_homework.id,
                          ref_type=DBConst.REF_BY_HOMEWORK)
            for file_id in attachment_ids
        ]
        db.add_all(new_file_refs)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return schemas.Response()


def create_homework_assign(
    db: Session,
    homework_id: int,
    homework_scope: List[schemas.HomeworkAssignScope],
) -> None:
    """生成作业发布信息并入库"""
    assign_list: List[HomeworkAssign] = []
    for scope in homework_scope:
        assign_list.extend(
            [
                HomeworkAssign(homework_id=homework_id,
                               class_id=scope.class_id, group_id=group_id)
                for group_id in scope.groups
            ]
        ) if scope.groups else assign_list.append(
            HomeworkAssign(homework_id=homework_id,
                           class_id=scope.class_id, group_id=0)
        )
    db.add_all(assign_list)


def create_homework_assign_msg(
    db: Session,
    homework_id: int,
    class_charge_map: Dict[int, int],
    class_assign_list: List[int],
    group_assign_list: List[schemas.HomeworkAssignScope],
) -> None:
    """新建作业发布消息"""
    new_message_content = MessageContent(related_id=homework_id,
                                         content='发布了新的作业')
    new_message_content = crud.message_content.create(db, auto_commit=False,
                                                      obj_in=new_message_content)
    student_assigned_list = crud.homework_assign.get_homework_assign_students(
        class_assign_list, group_assign_list
    )
    homework_assign_msg_list = [
        Message(sender_member_id=class_charge_map[row.class_id],
                category=DBConst.SCHOOL_HOMEWORK_HINT,
                receiver_class_id=row.class_id,
                receiver=row.name, content_id=new_message_content.id)
        for row in student_assigned_list
    ]
    homework_answer_status_list = [
        HomeworkAnswerStatus(homework_id=homework_id, student_name=row.name,
                             student_class_id=row.class_id)
        for row in student_assigned_list
    ]
    db.add_all(homework_assign_msg_list)
    db.add_all(homework_answer_status_list)


@router.put('/users/school_homeworks/{homework_id}', summary='修改校本作业')
def update_homework(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
    homework_id: int = Path(..., description='作业id'),
    updated_homework: schemas.SchoolHomework = Body(..., description='作业信息'),
) -> JSONResponse:
    """修改校本作业"""
    user_id = int(token.sub)
    # 校验 作业存在且发布人是当前用户
    if not crud.homework.is_homework_exists(db, homework_id, user_id):
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 校验 作业附件已上传
    check_homework_attachments(db, updated_homework)
    # 校验修改后的作业发布时间，每个老师每天在每个班只能发布一次作业
    assigned_homework = crud.homework_assign.get_assigned_class_scopes(
        db, user_id, homework_id, updated_homework.pub_time.date()
    )
    if assigned_homework:
        raise BizHTTPException(*RespError.HOMEWORK_ASSIGNED, data=assigned_homework)
    try:
        crud.homework.update_homework(db, user_id, homework_id, updated_homework)
        crud.message.send_update_homework_msg(
            db, homework_id, user_id, homework_id
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return schemas.Response()


@router.delete('/users/school_homeworks/{homework_id}', summary='删除校本作业')
def delete_homework(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
    homework_id: int = Path(..., description='作业id'),
) -> JSONResponse:
    """删除校本作业"""
    try:
        # 软删除作业
        if not crud.homework.delete_homework(db, homework_id, int(token.sub)):
            return schemas.Response()
        # 发送作业删除信息
        new_message_content = MessageContent(related_id=homework_id,
                                             content='删除了作业')
        new_message_content = crud.message_content.create(db, auto_commit=False,
                                                          obj_in=new_message_content)
        crud.message.send_update_homework_msg(
            db, homework_id, int(token.sub), new_message_content.id
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return schemas.Response()


@router.get('/classes/school_homeworks/{homework_id}', summary='查询单个校本作业信息')
def get_homework_info(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_class_member),
    homework: Row = Depends(get_homework_info),
) -> JSONResponse:
    """查询单个校本作业信息"""
    # 教师有权限查看本班作业，学生有权限查看发布范围包含该生的作业
    if token.member_role == DBConst.STUDENT:
        valid_assigned = crud.homework.is_assigned4student(
            db, homework.id, token.class_id, token.name
        )
    else:
        valid_assigned = crud.homework.is_assigned4class(
            db, homework.id, token.class_id
        )
    if not valid_assigned:
        raise BizHTTPException(*RespError.AUTHORIZATION_DENIED)
    # 查询作业引用的文件
    ref_files = crud.file_ref.get_homework_referenced_file_ids(db, homework.id)
    images = [file.id for file in ref_files if file.category == DBConst.IMAGE]
    videos = [file.id for file in ref_files if file.category == DBConst.VIDEO]
    audios = [file.id for file in ref_files if file.category == DBConst.AUDIO]
    docs = [file.id for file in ref_files if file.category == DBConst.DOC]
    # 构造响应数据
    homework_data = {
        'homework_id': homework.id, 'end_time': homework.end_time,
        'title': homework.title, 'desc': homework.desc, 'images': images,
        'videos': videos, 'audios': audios, 'docs': docs,
    }
    return schemas.Response(data=homework_data)


@router.post('/classes/school_homeworks/{homework_id}/answers')
def commit_homework_answer(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_student),
    homework_id: int = Path(..., description='作业id'),
    answer: schemas.SchoolHomeworkAnswer = Body(..., description='作业作答信息'),
) -> JSONResponse:
    """提交作业作答"""
    # 校验该作业发布范围是否包含当前学生，不包含则无权限提交该作业
    homework = crud.homework_answer_status.get_stu_answer_status(
        db, homework_id, token.class_id, token.name
    )
    if not homework:
        raise BizHTTPException(*RespError.AUTHORIZATION_DENIED)
    # 作业过期不能提交作答
    if homework.pub_time < datetime.now():
        raise BizHTTPException(*RespError.EXPIRED_HOMEWORK)
    # 判断当前作业 作答状态 和 作业类型（作答/重做/订正）
    if homework.status == DBConst.CHECKED:  # 已批改的作业，最多只能订正两次
        corrected_times = crud.homework_answer.get_correction_times()
        if corrected_times and corrected_times >= 2:
            raise BizHTTPException(*RespError.CORRECTION_TIMES_OUT_OF_LIMIT)
        answer_status = DBConst.CORRECTED
        answer_category = DBConst.CORRECTION
    elif homework.status == DBConst.NEED2SUBMIT:  # 待提交的作业
        answer_status = DBConst.SUBMITTED
        answer_category = DBConst.ANSWER
    elif homework.status == DBConst.NEED2REWORK:  # 待重做的作业
        answer_status = DBConst.SUBMITTED
        answer_category = DBConst.REWORKING
    else:  # 状态为 待提交、待重做 或 已批改 的作业才能提交作答
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 检查提交待附件是否存在
    attachment_ids = check_homework_attachments(db, answer)
    try:
        # 更新作业状态
        crud.homework_answer_status.update_answer_status_by_id(
            db, homework.status_id, answer_status
        )
        # 作业作答信息入库
        new_answer = HomeworkAnswer(submitter_member_id=token.member_id,
                                    homework_id=homework_id,
                                    status_id=homework.status_id,
                                    category=answer_category,
                                    desc=answer.desc)
        # 新建作答附件引用
        new_file_refs = [
            FileReference(file_id=file_id, referenced_id=new_answer.id,
                          ref_type=DBConst.REF_BY_HOMEWORK_ANSWER)
            for file_id in attachment_ids
        ]
        db.add_all(new_file_refs)
        crud.homework_answer.create(db, obj_in=new_answer)
    except Exception:
        db.rollback()
        raise
    return schemas.Response()


@router.get('/classes/school_homeworks/{homework_id}/answers',
            description='查询作业作答信息')
def get_homework_answer(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_class_member),
    homework: Row = Depends(get_homework_end_time),
    page: int = Query(1, gt=0, description='页码'),
    page_size: int = Query(15, gt=0, le=100, description='页数据量'),
) -> JSONResponse:
    """查询作业作答信息"""
    homework_id = homework.id
    homework_expired = True if homework.end_time < datetime.now() else False

    if token.member_role == DBConst.STUDENT:
        answer_status = crud.homework_answer_status.get_stu_answer_status(
            db, homework_id, token.class_id, token.name
        )
        if not answer_status:
            return schemas.Response(data=None)
        # 如果作答状态为 待提交 / 待重做，判断作业是否已结束，若结束则判断作答状态为 未反馈
        if homework_expired and answer_status.status in DBConst.EXPIRED_STATUS:
            status = DBConst.NO_FEEDBACK
        else:
            status = answer_status.status
        # 查询作答信息
        answers_data = crud.homework_answer.get_stu_homework_answers(
            db, answer_status.status_id
        )
        status_id: int = answer_status.status_id
        answers_data = {
            'status': status,
            'student_name': token.name,
            'answers': [dict(row) for row in answers_data],
        }
    else:
        answers_data = crud.homework_answer.get_class_homework_answers(
            db, homework_id, token.class_id, page, page_size
        )
        status_id: List[int] = [row.status_id for row in answers_data]

    # 查询作答引用文件的文件id
    file_data_list = crud.homework_answer.get_homework_answer_file_ids(
        db, status_id
    )
    file_answer_id_map = {row.id: row for row in file_data_list}
    # 拼接作业作答的文件引用数据
    iter_list = [answers_data] if isinstance(answers_data, dict) else answers_data
    for stu_answers_data in iter_list:
        for answer in stu_answers_data.get('answers'):
            if files := file_answer_id_map.get(answer['answer_id']):
                answer['images'] = files.images
                answer['videos'] = files.videos
                answer['audios'] = files.audios
                answer['docs'] = files.images
            else:
                answer['images'] = []
                answer['videos'] = []
                answer['audios'] = []
                answer['docs'] = []
    return schemas.Response(data=answers_data)


@router.post('/classes/school_homeworks/{homework_id}/answers/{answer_id}'
             '/checks', description='提交作业批改')
def check_homework_answer(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
    homework_id: int = Path(..., description='作业id'),
    answer_id: int = Path(..., description='作答id'),
    image_mark: Str = Body(..., description='大图批改信息'),
    score: str = Body(None, description='作业评分，0表示已阅'),
) -> JSONResponse:
    """提交作业批改"""
    # 分数 必须是合法的枚举值
    if score and score not in SCORE_ENUM_SET:
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 校验作业发布人身份、作业作答状态
    answer = crud.homework_answer.get_answer_status(
        db, homework_id, int(token.sub), token.class_id, answer_id
    )
    if not answer:
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 只能批改已提交的和已订正的作业
    if answer.status not in {DBConst.SUBMITTED, DBConst.CORRECTED}:
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    image_mark = json.dumps(image_mark)
    try:
        # 入库作答批改信息
        new_answer_check = HomeworkAnswerCheck(reviewer_member_id=token.member_id,
                                               category=DBConst.IMAGE_MARK,
                                               content=image_mark)
        new_answer_check = crud.homework_answer_check.create(
            db, obj_in=new_answer_check, auto_commit=False
        )
        crud.homework_answer.update_answer_check(db, image_mark, new_answer_check.id)
        # 更新作业作答情况及评分
        crud.homework_answer_status.update_score_and_status_by_id(
            db, answer.status_id, score, DBConst.CHECKED
        )
        # 发送批改消息
        new_message_content = MessageContent(related_id=homework_id,
                                             content='你的作业已被批改')
        new_message_content = crud.message_content.create(db, auto_commit=False,
                                                          obj_in=new_message_content)
        new_msg = Message(sender_member_id=token.member_id,
                          category=DBConst.SCHOOL_HOMEWORK_HINT,
                          receiver_class_id=token.class_id,
                          receiver=answer.student_name,
                          content_id=new_message_content.id)
        crud.message.create(db, obj_in=new_msg)
    except Exception:
        db.rollback()
        raise
    return schemas.Response()


@router.post('/classes/school_homeworks/{homework_id}/answers/evaluates',
             summary='提交作业作答评价或打回作答')
def evaluate_homework_answer(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_teacher),
    homework_id: int = Path(..., description='作业id'),
    answers: Set[int] = Body(..., min_items=1, description='作答id列表'),
    comment: Str = Body(..., description='评论正文'),
    score: str = Body(None, description='作业评分，0表示已阅，无评分表示打回'),
) -> JSONResponse:
    """提交作业作答评价或打回作答"""
    if score and score not in SCORE_ENUM_SET:
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 校验 作业作答对应的作业发布人、作业发布范围、作答点评和批改情况
    exists_answers = crud.homework_answer.get_existed_answers(
        db, homework_id, int(token.sub), token.class_id, answers
    )
    if len(exists_answers) != len(answers):
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 校验作业作答状态
    corrected = 0   # 已订正作业
    submitted = []  # 已提交作业
    for answer in exists_answers:
        if answer.status == DBConst.SUBMITTED:
            submitted.append(answer.student_name)
        elif answer.status == DBConst.CORRECTED:
            corrected = 1
        # 只能点评 已提交 或 已订正 的作答
        else:
            raise BizHTTPException(*RespError.INVALID_PARAMETER)
    if not score:
        # 订正作业不能打回
        if corrected:
            raise BizHTTPException(*RespError.INVALID_PARAMETER)
        # 校验打回作业次数
        if submitted:
            reject_counts = crud.homework_answer.count_rejected()
            over_twice = [row.student_name
                          for row in reject_counts if row.rejected_times == 2]
            raise BizHTTPException(
                *RespError.REJECTION_TIMES_OUT_OF_LIMIT, data=over_twice
            ) if over_twice else ...
    try:
        # 入库点评信息
        new_evaluate = HomeworkEvaluate(reviewer_member_id=token.member_id,
                                        comment=comment, rejected=not score,
                                        score=score)
        new_evaluate = crud.homework_evaluate.create(db, obj_in=new_evaluate,
                                                     auto_commit=False)
        crud.homework_answer.update_evaluate(db, answers, new_evaluate.id)
        # 更新作业作答情况评分
        crud.homework_answer_status.update_score_by_answer_id(db, answers, score) \
            if score else ...
        # 发送评论消息
        new_message_content = MessageContent(related_id=homework_id, content=comment)
        new_message_content = crud.message_content.create(db, auto_commit=False,
                                                          obj_in=new_message_content)
        new_message_list = [
            Message(sender_member_id=token.member_id,
                    category=DBConst.SCHOOL_HOMEWORK_COMMENT,
                    receiver_class_id=token.class_id,
                    receiver=row.student_name, content_id=new_message_content.id)
            for row in exists_answers
        ]
        db.add_all(new_message_list)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return schemas.Response()


@router.post('/school_homeworks/attachments', summary='校本作业上传附件')
async def upload_homework_attachment(
    token: schemas.TokenPayload = Depends(deps.get_class_member),
    file: UploadFile = File(..., description='上传文件'),
) -> JSONResponse:
    """校本作业上传附件，返回文件名称"""
    # 根据请求头 Content-Type 判断上传文件类型
    if file.content_type in ALLOW_IMAGE_MIMES:
        att_type = 'images'
        size_limit = IMAGE_SIZE_LIMIT
        allow_mimes = ALLOW_IMAGE_MIMES
        db_file_type = DBConst.IMAGE
    elif file.content_type in ALLOW_VIDEO_MIMES:
        att_type = 'videos'
        size_limit = VIDEO_SIZE_LIMIT
        allow_mimes = ALLOW_VIDEO_MIMES
        db_file_type = DBConst.VIDEO
    elif file.content_type in ALLOW_AUDIO_MIMES:
        att_type = 'audios'
        size_limit = AUDIO_SIZE_LIMIT
        allow_mimes = ALLOW_AUDIO_MIMES
        db_file_type = DBConst.AUDIO
    elif file.content_type in ALLOW_DOC_MIMES:
        att_type = 'docs'
        size_limit = DOC_SIZE_LIMIT
        allow_mimes = ALLOW_DOC_MIMES
        db_file_type = DBConst.DOC
    else:
        raise BizHTTPException(*RespError.INVALID_UPLOADED_FILETYPE)
    # 上传文件保存到本地
    relative_file_dir, file_save_dir = upload.make_upload_dir(att_type)
    new_filename = await upload.save_upload_file(
        file, allow_mimes, token.sub, file_save_dir, size_limit
    )
    # 如果是视频，校验视频时长
    if att_type == 'videos':
        video_duration = utils.get_video_duration(
            os.path.join(file_save_dir, new_filename)
        )
        if video_duration > VIDEO_DURATION_LIMIT:
            raise BizHTTPException(*RespError.VIDEO_DURATION_OUT_OF_LIMIT)
    # 文件信息入库
    file_path = os.path.join(relative_file_dir, new_filename)
    new_file_info = FileInfo(
        uploader_id=int(token.sub), category=db_file_type, file_path=file_path
    )
    db = next(deps.get_db())
    new_file_info = crud.file_info.create(db, obj_in=new_file_info)
    return schemas.Response(data=new_file_info.id)
