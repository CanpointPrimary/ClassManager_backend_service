#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/8/4
# Author: gray

"""
CRUD模块 - 学科相关 非复杂业务CRUD
"""

from typing import List

from sqlalchemy.engine import Row
from sqlalchemy.orm import Session
from sqlalchemy.sql import false, text

from app.crud.base import CRUDBase
from app.models import Subject


class CRUDSubject(CRUDBase[Subject, Subject, Subject]):
    """
    学科相关CRUD
    模型类: Subject
    数据表: subject
    """
    @staticmethod
    def all(db: Session) -> List[Row]:
        """
        获取所有学科数据
        """
        return (
            db.query(Subject.id.label('code'), Subject.name)
            .filter(Subject.is_delete == false())
            .all()
        )

    @staticmethod
    def subject_exists(db: Session, subject_id: int) -> int:
        """
        查询 subject_id 对应学科是否存在
        """
        return (
            db.query(text('1'))
            .filter(
                Subject.id == subject_id,
                Subject.is_delete == false()
            )
        )


subject = CRUDSubject(Subject)
