#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/9/18
# Author: gray

"""
ORM模型类 - 文件 相关
"""

from sqlalchemy.schema import Column
from sqlalchemy.sql import false
from sqlalchemy.types import BigInteger, Boolean, String

from app.models.base import Base


class FileInfo(Base):
    """
    文件信息
    数据表: uploaded - 描述文件相关的信息
    """
    __tablename__ = 'file_info'  # noqa

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id，主键')
    uploader_id = Column(BigInteger, nullable=False, comment='上传者用户id')
    category = Column(String(2), nullable=False, comment='文件类型: '
                                                         '1-图像 '
                                                         '2-视频 '
                                                         '3-音频 '
                                                         '4-文档')
    file_path = Column(String, nullable=False, comment='文件路径')
    compressed = Column(
        Boolean, nullable=False, server_default=false(), comment='是否压缩完成'
    )

    __idx_list__ = ('uploader_id', )


class FileReference(Base):
    """
    文件引用
    数据表: file_reference - 描述文件被引用的关联关系
    """
    __tablename__ = 'file_reference'  # noqa

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id，主键')
    file_id = Column(BigInteger, nullable=False, comment='文件id')
    ref_type = Column(String(2), nullable=False, comment='引用类型: '
                                                         '1-用户反馈 '
                                                         '2-作业 '
                                                         '3-作业作答')
    referenced_id = Column(BigInteger, nullable=False, comment='引用对象id')

    __idx_list__ = ('referenced_id', )
