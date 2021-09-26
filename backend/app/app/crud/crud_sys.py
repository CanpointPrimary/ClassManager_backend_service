#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date: 2021/7/19
# @Author: gray

"""
CRUD模块 - 系统配置相关 非复杂业务CRUD
"""

from typing import List

from sqlalchemy.engine import Row
from sqlalchemy.orm import aliased, Session
from sqlalchemy.sql import func

from app.crud.base import CRUDBase
from app.constants import DBConst
from app.models import Region, SysConfig


class CRUDRegion(CRUDBase[Region, Region, Region]):
    """
    全国地区配置相关CRUD
    模型类: Region
    数据表: region
    """
    @staticmethod
    def get_area_tree(db: Session) -> List[Row]:
        """
        获取 区县级行政区 编码、名称、父级行政区编码
        """
        parent = aliased(Region)
        return (
            db.query(Region.code, Region.name, parent.name.label('parent_name'))
            .join(parent, Region.parent_code == parent.code)
            .filter(Region.level == DBConst.AREA)
            .all()
        )


class CRUDSysConfig(CRUDBase[SysConfig, SysConfig, SysConfig]):
    """
    系统配置相关CRUD
    CRUD类: SysConfig
    数据表: sys_config
    """
    @staticmethod
    def get_config_by_type(db: Session, type_: str) -> List[Row]:
        """
        根据配置类型查得该类型的所有配置项的 key-value
        """
        return (
            db.query(SysConfig.key, SysConfig.value)
            .filter(SysConfig.type_ == type_)
            .all()
        )

    def family_relation_exists(self, db: Session, family_relation: str) -> int:
        """
        查询对应 亲属关系 配置是否存在
        """
        return (
            db.query(func.count(self.model.id))
            .filter(
                    SysConfig.type_ == DBConst.FAMILY_RELATION,
                    SysConfig.key == family_relation,
            )
            .scalar()
        )


region = CRUDRegion(Region)
sys_config = CRUDSysConfig(SysConfig)
