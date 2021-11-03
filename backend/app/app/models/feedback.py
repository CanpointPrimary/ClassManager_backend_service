#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date: 2021/7/12
# @Author: gray

"""
ORM模型类 - 用户反馈
"""

from sqlalchemy.schema import Column
from sqlalchemy.types import BigInteger, String, Text

from app.models.base import Base


class Feedback(Base):
    """
    用户反馈
    数据表: feedback - 用户反馈的信息
    """
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键')
    user_id = Column(BigInteger, nullable=False, comment='用户id')
    category = Column(String(2), nullable=False, comment='反馈类型: '
                                                         '1-产品建议 '
                                                         '其他-功能异常')
    desc = Column(Text, nullable=False, comment='反馈内容描述')

    __idx_list__ = ('user_id', )
    __no_update_time__ = True
