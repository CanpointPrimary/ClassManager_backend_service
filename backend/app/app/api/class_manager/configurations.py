#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/8/16
# Author: gray

"""
路径函数 - 配置相关
"""

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.constants import DBConst
from app.core.celery_app import celery_app


router = APIRouter()


@router.get('/subjects', summary='查询学科配置')
def get_subjects(
    db: Session = Depends(deps.get_db),
    _: schemas.TokenPayload = Depends(deps.get_token),
) -> Any:
    """
    查询学科配置
    """
    return crud.subject.all(db)


@router.get('/family_relations', summary='查询亲属关系配置')
def get_family_relations(
    db: Session = Depends(deps.get_db),
    _: schemas.TokenPayload = Depends(deps.get_token),
) -> Any:
    """
    查询亲属关系配置
    """
    return crud.sys_config.get_config_by_type(db, type_=DBConst.FAMILY_RELATION)


@router.put('/schools', summary='更新学校信息')
def update_school_info(
    _: schemas.TokenPayload = Depends(deps.get_activated)
) -> JSONResponse:
    """
    更新学校信息
    """
    celery_app.send_task('update_school_data', queue='main-queue')
    return schemas.Response()
