#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/8/27
# Author: gray

"""
路径函数 - 用户反馈相关
"""

import os
from typing import List

from fastapi import APIRouter, Body, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.api.class_manager import upload
from app.constants import DBConst
from app.exceptions import BizHTTPException
from app.constants.resp_error import RespError
from app.models import Feedback, FileInfo, FileReference
from app.schemas import Str10, StrLeast10


router = APIRouter()

ALLOW_IMAGE_MIMES = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
}
PIC_SIZE_LIMIT = 10 * 1024 * 1024


@router.post('/exception_reports', summary='提交功能异常反馈')
def feedback_exception(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
    file_list: List[int] = Body(..., min_items=1, max_items=5, description='上传图片'),
    exc_desc: Str10 = Body(..., description='问题描述'),
    category: str = Body(..., description='问题类型'),
) -> JSONResponse:
    """
    提交功能异常反馈
    """
    # 校验文件数量、文件是否存在、问题类型
    if category == DBConst.PRODUCT_SUGGESTION:
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 校验文件是否存在
    existed_file_count = crud.file_info.count_existed_files(
        db, file_list, DBConst.IMAGE
    )
    if existed_file_count != len(file_list):
        raise BizHTTPException(*RespError.FILE_NOT_FOUND)
    # 反馈信息入库
    feedback = Feedback(
        user_id=int(token.sub), category=category, desc=exc_desc,
    )
    feedback = crud.feedback.create(db, obj_in=feedback)
    # 提交图片引用信息入库
    image_ref_list = [
        FileReference(file_id=file_id, referenced_id=feedback.id,
                      ref_type=DBConst.REF_BY_USER_FEEDBACK)
        for file_id in file_list
    ]
    db.add_all(image_ref_list) if image_ref_list else ...
    return schemas.Response()


@router.post('/images', summary='上传用户反馈图片')
async def upload_feedback_images(
    token: schemas.TokenPayload = Depends(deps.get_activated),
    file: UploadFile = File(..., description='上传图片'),
) -> JSONResponse:
    """
    上传用户反馈图片
    """
    # 生成文件路径
    relative_file_dir, file_save_dir = upload.make_upload_dir('images')
    # 保存文件到本地
    new_filename = await upload.save_upload_file(
        file, ALLOW_IMAGE_MIMES, token.sub, file_save_dir, PIC_SIZE_LIMIT
    )
    # 文件信息入库
    file_path = os.path.join(relative_file_dir, new_filename)
    new_file_info = FileInfo(
        uploader_id=int(token.sub), category=DBConst.IMAGE, file_path=file_path
    )
    db = next(deps.get_db())
    new_file_info = crud.file_info.create(db, obj_in=new_file_info)
    return schemas.Response(data=new_file_info.id)


@router.post('/product_suggestions', summary='提交产品建议')
def feedback_suggestion(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
    suggestion: StrLeast10 = Body(..., embed=True, description='产品建议'),
) -> JSONResponse:
    """
    提交产品建议
    """
    feedback = Feedback(
        user_id=int(token.sub),
        category=DBConst.PRODUCT_SUGGESTION,
        desc=suggestion,
    )
    crud.feedback.create(db, obj_in=feedback)
    return schemas.Response()
