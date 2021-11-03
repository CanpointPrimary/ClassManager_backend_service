#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/8/9
# Author: gray

"""
公共工具模块
"""

import os
import sys
from typing import IO

import aiofiles
import cv2
from loguru import logger

from app.core.config import settings


def init_logger():
    """
    初始化日志系统
    日志路径为 项目根目录下的log目录
    日志等级为 .env 文件中 LOG_LEVEL 配置项
    日志分为两种，一为 runtime_YYYY-MM-DD.log 文件名的运行时日志，
        另一种为 error_YYYY-MM-DD.log 文件名的错误日志
    日志每天 00:00 进行绕街并压缩为zip格式
    日志系统异步（包括多进程和协程）安全，可以将 enqueue=True 删除以提高性能，但会丧失异步安全特性
    """
    log_dir = os.path.join(settings.BASE_DIR, 'log')
    logger.remove()
    if settings.LOG_LEVEL in ('TRACE', 'DEBUG'):
        logger.add(sink=sys.stderr, level=settings.LOG_LEVEL)
    logger.add(
        sink=os.path.join(log_dir, 'runtime_{time:YYYY-MM-DD}.log'),
        level=settings.LOG_LEVEL,
        rotation='00:00',
        enqueue=True,
        compression='zip',
    )
    logger.add(
        sink=os.path.join(log_dir, 'error_{time:YYYY-MM-DD}.log'),
        level='ERROR',
        rotation='00:00',
        enqueue=True,
        compression='zip',
    )


async def save_file_chunked(
    io_in: IO,
    new_file_path: str,
    chunk_size: int = 1024 ** 3,
    size_limit: int = 1024 ** 3
) -> int:
    """
    分片读取保存文件，如果指定了文件大小限制，当文件大小超出限制时则不会保存文件
    返回写入文件大小
    """
    writen_size = 0
    async with aiofiles.open(new_file_path, 'wb') as file_out:
        while content := await io_in.read(chunk_size):
            writen_size += len(content)
            if size_limit and writen_size > size_limit:
                writen_size = 0
                break
            await file_out.write(content)
    if not writen_size:
        os.remove(new_file_path)
    return writen_size


def get_video_duration(video_path: str) -> int:
    """
    获取视频时长
    """
    video = cv2.VideoCapture(video_path)
    if video.isOpened():
        frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = video.get(cv2.CAP_PROP_FPS)
        duration = int(frame_count / fps)
        video.release()
        return duration
    return 0
