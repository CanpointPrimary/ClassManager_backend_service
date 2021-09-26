#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# Date: 2021/7/28
# Author: gray

"""
路径函数 - 页面相关
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps


router = APIRouter()

ENTRANCE_PAGE_LIMIT = 10
HOMEPAGE_MENU_NUMBER_LIMIT = 8


@router.get('/startup_pages', summary='获取启动页图片', description='获取启动页图片')
def get_startup_page(db: Session = Depends(deps.get_db)) -> Row:
    """
    获取启用中的启动页图片路径
    """
    return crud.entrance_page.get_startup_activated(db)


@router.get('/guidance_pages', summary='获取引导页图片', description='获取引导页图片')
def get_guidance_pages(
    db: Session = Depends(deps.get_db),
    limit: int = Query(ENTRANCE_PAGE_LIMIT, description='数量'),
) -> List[Row]:
    """
    获取启用中的启动页图片，图片数量有限制
    """
    if not limit or limit <= 0 or limit > ENTRANCE_PAGE_LIMIT:
        limit = ENTRANCE_PAGE_LIMIT
    return crud.entrance_page.get_guidance_activated(db, limit=limit)


@router.get('/homepage_menus', summary='获取首页菜单', description='获取首页菜单')
def get_homepage_menus(
    db: Session = Depends(deps.get_db),
    _: schemas.TokenPayload = Depends(deps.get_token),
    limit: int = Query(HOMEPAGE_MENU_NUMBER_LIMIT, description='数量'),
) -> List[Row]:
    """
    获取首页菜单，有数量限制
    """
    if not limit or limit <= 0 or limit > HOMEPAGE_MENU_NUMBER_LIMIT:
        limit = HOMEPAGE_MENU_NUMBER_LIMIT
    return crud.homepage_menu.get_activated(db, limit)
