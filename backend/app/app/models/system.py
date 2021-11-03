#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date: 2021/7/8
# @Author: gray

"""
ORM模型类 - 系统配置相关
"""

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String

from app.models.base import Base


class Region(Base):
    """
    全国地区
    数据表: region - 描述全国行政区划信息
    """
    code = Column(Integer, primary_key=True, comment='行政区编号，主键')
    name = Column(String(20), nullable=False, comment='地区名称')
    parent_code = Column(Integer, comment='父级地区id')
    level = Column(
        Integer,
        nullable=False,
        comment='地区级别: '
                '1-省、自治区、直辖市 '
                '2-地级市、地区、自治州、盟 '
                '3-市辖区、县级市、县'
    )

    __no_create_time__ = True
    __no_update_time__ = True


class SysConfig(Base):
    """
    系统配置
    数据表: sys_config - 系统相关配置信息
    """
    __tablename__ = 'sys_config'  # noqa

    id = Column(Integer, primary_key=True, autoincrement=True, comment='id，主键')
    key = Column(String, nullable=False, comment='配置项KEY')
    value = Column(String, nullable=False, comment='配置项VALUE')
    desc = Column(String, comment='配置项说明')
    type_ = Column('type', Integer, nullable=False, comment='配置类型')

    __no_create_time__ = True
    __no_update_time__ = True
