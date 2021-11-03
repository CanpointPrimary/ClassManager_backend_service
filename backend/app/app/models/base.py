#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date: 2021/7/7
# @Author: gray

"""
ORM模型类 - 基类
"""

from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.schema import Index, Column
from sqlalchemy.sql import text
from sqlalchemy.types import TIMESTAMP


@as_declarative()
class Base:
    id: Any
    __name__: str
    __no_create_time__: bool
    __no_update_time__: bool

    # 自动生成表名
    @declared_attr
    def __tablename__(cls) -> str:  # noqa
        return cls.__name__.lower()

    # 利用反射自动为字段生成索引
    @declared_attr
    def __table_args__(cls):  # noqa
        table_args = []
        if hasattr(cls, '__arg_list__'):
            for arg in cls.__arg_list__:
                table_args.append(arg)
        if hasattr(cls, '__idx_list__'):
            for field_name in cls.__idx_list__:
                field = getattr(cls, field_name)
                index_name = f'{cls.__tablename__}_{field_name}_idx'
                table_args.append(Index(index_name, field))
        return tuple(table_args) if table_args else None

    # 自动生成 创建时间 字段
    @declared_attr
    def create_time(cls):  # noqa
        if hasattr(cls, '__no_create_time__') and cls.__no_create_time__ is True:
            return None
        return Column(
            TIMESTAMP,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP'),
            comment='创建时间'
        )

    # 自动生成 最后修改时间 字段
    @declared_attr
    def update_time(cls):  # noqa
        if hasattr(cls, '__no_update_time__') and cls.__no_update_time__ is True:
            return None
        return Column(
            TIMESTAMP,
            server_default=text('CURRENT_TIMESTAMP'),
            server_onupdate=text('CURRENT_TIMESTAMP'),
            onupdate=text('CURRENT_TIMESTAMP'),
            comment='最后修改时间',
        )

    def __repr__(self):
        secrets = getattr(self, '__secrets__', ())
        verbose = []
        for attr, value in self.__dict__.items():
            if attr.startswith('_') or attr in secrets:
                continue
            verbose.append(f'{attr}={value}')
        verbose = ', '.join(verbose)
        return f'<{self.__class__.__name__}: {verbose}>'
