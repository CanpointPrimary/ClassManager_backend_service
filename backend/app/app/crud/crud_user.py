#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date: 2021/7/13
# @Author: gray

"""
CRUD模块 - 用户相关 非复杂业务CRUD
"""

from sqlalchemy.engine.row import Row
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import User


class CRUDUser(CRUDBase[User, User, User]):
    """
    用户相关，非复杂业务CRUD
    模型类: User
    数据表: user
    """
    @staticmethod
    def is_openid_exists(db: Session, openid: str) -> Row:
        """
        判断 openid 对应的用户是否存在，存在则返回 id
        """
        return (
            db.query(User.id)
            .filter(User.openid == openid)
            .first()
        )

    @staticmethod
    def get_basic_info(db: Session, user_id: int) -> Row:
        """
        获取用户基本信息
        """
        return (
            db.query(User.current_member_id, User.is_delete)
            .filter(User.id == user_id)
            .first()
        )

    @staticmethod
    def update_current_member(db: Session, user_id: int, member_id: int) -> int:
        """
        更新用户当前所在班级
        """
        res = (
            db.query(User)
            .filter(User.id == user_id)
            .update({User.current_member_id: member_id})
        )
        db.commit()
        return res


user = CRUDUser(User)
