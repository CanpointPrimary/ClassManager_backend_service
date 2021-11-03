#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# Date: 2021/7/29
# Author: gray

"""
CRUD模块 - 页面相关 非复杂业务CRUD
"""

from typing import List

from app.constants import DBConst
from app.crud.base import CRUDBase
from app.models import HomepageMenu, EntrancePage

from sqlalchemy.engine.row import Row
from sqlalchemy.orm import Session


class CRUDHomepageMenu(CRUDBase[HomepageMenu, HomepageMenu, HomepageMenu]):
    """
    首页菜单相关CRUD
    模型类: HomepageMenu
    数据表: homepage_menu
    """
    @staticmethod
    def get_activated(db: Session, limit: int = 8) -> List[Row]:
        """
        查询当前已启用的首页菜单
        """
        return (
            db.query(HomepageMenu.id, HomepageMenu.target,
                     HomepageMenu.title, HomepageMenu.icon)
            .filter(HomepageMenu.status == DBConst.PIC_ACTIVATED)
            .order_by(HomepageMenu.id.desc())
            .limit(limit)
            .all()
        )


class CRUDEntrancePage(CRUDBase[EntrancePage, EntrancePage, EntrancePage]):
    """
    启动页图片相关CRUD
    模型类: EntrancePage
    数据表: entrance_page
    """
    @staticmethod
    def get_startup_activated(db: Session) -> Row:
        """
        查询当前已启用的启动页图片
        """
        return (
            db.query(EntrancePage.src, EntrancePage.desc, EntrancePage.target)
            .filter(
                EntrancePage.type == DBConst.STARTUP,
                EntrancePage.status == DBConst.PIC_ACTIVATED,
            )
            .order_by(EntrancePage.id.desc())
            .first()
        )

    @staticmethod
    def get_guidance_activated(db: Session, limit: int = 10) -> List[Row]:
        """
        查询已启用的引导页图片
        """
        return (
            db.query(EntrancePage.id, EntrancePage.src, EntrancePage.desc)
            .filter(
                EntrancePage.type == DBConst.GUIDANCE,
                EntrancePage.status == DBConst.PIC_ACTIVATED,
            )
            .order_by(EntrancePage.id.desc())
            .limit(limit)
            .all()
        )


homepage_menu = CRUDHomepageMenu(HomepageMenu)
entrance_page = CRUDEntrancePage(EntrancePage)
