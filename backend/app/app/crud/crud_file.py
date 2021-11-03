#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date: 2021/10/27
# @Author: gray

"""
CRUD模块 - 文件相关
"""

from typing import Iterable, List, Union

from sqlalchemy.orm import Session
from sqlalchemy.sql import and_, func
from sqlalchemy.sql.selectable import ScalarSelect

from app.constants import DBConst
from app.crud.base import CRUDBase
from app.models import FileInfo, FileReference


class CRUDFileInfo(CRUDBase[FileInfo, FileInfo, FileInfo]):
    """文件信息相关CRUD
    模型类: FileInfo  数据表: file_info
    """
    @staticmethod
    def count_existed_files(
        db: Session, file_id: Union[int, Iterable[int]], file_type: str
    ) -> int:
        """查询存在的文件信息的数量"""
        if isinstance(file_id, Iterable):
            cond = and_(FileInfo.id.in_(file_id), FileInfo.category == file_type)
        else:
            cond = and_(FileInfo.id == file_id, FileInfo.category == file_type)
        return db.query(func.count(FileInfo.id)).filter(cond).scalar()

    @staticmethod
    def get_subquery_by_file_type(
        db: Session, id_list: List[int], file_type: str
    ) -> ScalarSelect:
        return (
            db.query(func.count(FileInfo.id))
            .filter(
                FileInfo.id.in_(id_list),
                FileInfo.category == file_type,
            )
            .scalar_subquery()
        )

    def count_homework_attachments(
        self, db: Session, image_ids: List[int],
        video_ids: List[int], audio_ids: List[int], doc_ids: List[int]
    ) -> int:
        """查询存在的作业附件的数量"""
        images_scalar_subquery = self.get_subquery_by_file_type(db, image_ids,
                                                                DBConst.IMAGE)
        videos_scalar_subquery = self.get_subquery_by_file_type(db, video_ids,
                                                                DBConst.VIDEO)
        audios_scalar_subquery = self.get_subquery_by_file_type(db, audio_ids,
                                                                DBConst.AUDIO)
        docs_scalar_subquery = self.get_subquery_by_file_type(db, doc_ids,
                                                              DBConst.DOC)
        return (
            db.query(images_scalar_subquery + videos_scalar_subquery
                     + audios_scalar_subquery + docs_scalar_subquery)
            .scalar()
        )


class CRUDFileReference(CRUDBase[FileReference, FileReference, FileReference]):
    """文件引用相关CRUD
    模型类: FileReference  数据表: file_reference
    """
    @staticmethod
    def get_homework_referenced_file_ids(db: Session, homework_id: int):
        return (
            db.query(FileInfo.id, FileInfo.category)
            .join(FileInfo, FileInfo.id == FileReference.file_id)
            .filter(FileReference.ref_type == DBConst.REF_BY_HOMEWORK,
                    FileReference.referenced_id == homework_id)
            .all()
        )


file_info = CRUDFileInfo(FileInfo)
file_ref = CRUDFileReference(FileReference)
