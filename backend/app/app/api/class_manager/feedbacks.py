#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/8/27
# Author: gray

"""
路径函数 - 用户反馈相关
"""

import os
import shutil
import time
import uuid
from hashlib import md5
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import IO, List

from fastapi import APIRouter, Body, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.constants import DBConst
from app.core.config import settings
from app.exceptions import BizHTTPException
from app.constants.resp_error import RespError
from app.models import Feedback


router = APIRouter()

ALLOW_EXTENSIONS = ['.png', '.jpg', '.jpeg']
PIC_SIZE_LIMIT = 512 * 1024


@router.post('/exception_reports', summary='提交功能异常反馈')
def feedback_exception(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
    file_list: List[str] = Body(..., description='上传图片'),
    exc_desc: str = Body(..., description='问题描述'),
    category: str = Body(..., description='问题类型'),
) -> JSONResponse:
    """
    提交功能异常反馈
    """
    exc_desc = exc_desc.strip()
    if not file_list or len(exc_desc) < 10:
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    # 校验文件数量、文件是否存在、问题类型
    if category == DBConst.PRODUCT_SUGGESTION:
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    if len(file_list) > 5:
        raise BizHTTPException(*RespError.FILE_NUMBER_OUT_OF_LIMIT)
    in_existence = [
        1 for filename in file_list
        if not os.path.exists(
            os.path.join(settings.BASE_DIR, 'upload', 'pics', filename)
        )
    ]
    if in_existence:
        raise BizHTTPException(*RespError.UPLOADED_FILE_NOT_FOUND)
    feedback = Feedback(
        user_id=int(token.sub), category=category,
        images=','.join(file_list), desc=exc_desc,
    )
    crud.feedback.create(db, obj_in=feedback)
    return schemas.Response()


@router.post('/pics', summary='上传用户反馈图片')
def upload_feedback_pics(
    token: schemas.TokenPayload = Depends(deps.get_activated),
    file: UploadFile = File(..., description='上传图片'),
) -> JSONResponse:
    """
    上传用户反馈图片
    """
    filetype = Path(file.filename).suffix.lower()
    if filetype not in ALLOW_EXTENSIONS:
        raise BizHTTPException(*RespError.INVALID_UPLOADED_FILETYPE)
    new_filename = uuid.uuid4().hex + str(time.time()) + token.sub
    new_filename = md5(new_filename.encode('utf8')).hexdigest() + filetype
    temp: IO = NamedTemporaryFile()
    file_size = 0
    for chunk in file.file:
        file_size += len(chunk)
        if file_size > PIC_SIZE_LIMIT:  # 文件大小超过限制
            raise BizHTTPException(*RespError.FILESIZE_OUT_OF_LIMIT)
        temp.write(chunk)
    shutil.copy(
        temp.name,
        os.path.join(settings.BASE_DIR, 'upload', 'pics', new_filename),
    )
    temp.close()
    return schemas.Response(data=new_filename)


@router.post('/product_suggestions', summary='提交产品建议')
def feedback_suggestion(
    db: Session = Depends(deps.get_db),
    token: schemas.TokenPayload = Depends(deps.get_activated),
    suggestion: str = Body(..., embed=True, description='产品建议'),
) -> JSONResponse:
    """
    提交产品建议
    """
    suggestion = suggestion.strip()
    if len(suggestion) < 10:
        raise BizHTTPException(*RespError.INVALID_PARAMETER)
    feedback = Feedback(
        user_id=int(token.sub),
        category=DBConst.PRODUCT_SUGGESTION,
        desc=suggestion
    )
    crud.feedback.create(db, obj_in=feedback)
    return schemas.Response()
