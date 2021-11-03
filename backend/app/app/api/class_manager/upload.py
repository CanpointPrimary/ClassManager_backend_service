#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/9/22
# Author: gray

"""
公共部分 - 上传文件相关
"""

import os
import time
import uuid
from datetime import datetime
from hashlib import md5
from typing import Dict, Union, Tuple

import magic
from fastapi import UploadFile

from app import utils
from app.constants import RespError
from app.core.config import settings
from app.exceptions import BizHTTPException


def make_upload_dir(file_type: str) -> Tuple[str, str]:
    """
    生成上传文件目录，返回 相对项目根目录的相对路径 和 绝对路径
    生成的路径依此规则: upload/{文件类型}/年/月/日

    Args:
        file_type : 上传文件文件类型
    """
    today = datetime.today()
    relative_file_dir = os.path.join(
        'upload', file_type, str(today.year), str(today.month), str(today.day)
    )
    file_save_dir = os.path.join(settings.BASE_DIR, relative_file_dir)
    os.makedirs(file_save_dir, exist_ok=True)
    return relative_file_dir, file_save_dir


async def save_upload_file(
    file: UploadFile,
    allow_mimes: Dict[str, str],
    id_mark: Union[str, int],
    file_save_dir: str,
    size_limit: int,
) -> str:
    """
    保存上传文件，返回重命名的文件名
    """
    # 校验文件后缀名
    file_suffix = allow_mimes.get(file.content_type)
    if file_suffix not in allow_mimes.values():
        raise BizHTTPException(*RespError.INVALID_UPLOADED_FILETYPE)
    # 生成重命名文件
    mark = uuid.uuid4().hex + str(time.time()) + str(id_mark)
    new_filename = md5(mark.encode('utf8')).hexdigest() + file_suffix
    new_file_path = os.path.join(file_save_dir, new_filename)
    # 分片读取并保存文件
    res = await utils.save_file_chunked(file, new_file_path, size_limit=size_limit)  # noqa
    if not res:
        raise BizHTTPException(*RespError.FILESIZE_OUT_OF_LIMIT)
    # 校验文件头，判断文件类型
    file_mime = magic.from_file(new_file_path, mime=True)
    if file_mime != file.content_type:
        os.remove(new_file_path)
        raise BizHTTPException(*RespError.UNRECOGNIZED_UPLOADED_FILETYPE)
    return new_filename
