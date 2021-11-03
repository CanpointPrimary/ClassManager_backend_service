#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/9/13
# Author: gray

"""
ORM模型类 - 消息相关
"""

from sqlalchemy.schema import Column
from sqlalchemy.sql import text
from sqlalchemy.types import BigInteger, Boolean, String

from app.models.base import Base


class Message(Base):
    """
    消息
    数据表: message - 消息
    """
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id，主键')
    sender_member_id = Column(
        BigInteger, nullable=False, comment='消息发送人的成员id，0 表示系统发送'
    )
    category = Column(String(2), nullable=False, comment='类型: '
                                                         '1-校本作业提示 '
                                                         '2-校本作业评论')
    receiver_class_id = Column(BigInteger, nullable=False, comment='消息接收人班级id')
    receiver = Column(String, nullable=False, comment='消息接收人姓名')
    content_id = Column(BigInteger, nullable=False, comment='消息内容id')
    is_delete = Column(
        Boolean, server_default=text('False'), nullable=False, comment='是否删除'
    )

    __no_update_time__ = True
    __idx_list__ = ('sender_member_id', 'receiver_class_id', 'receiver')


class MessageContent(Base):
    """
    消息内容
    数据表: message_content - 描述消息的具体内容
    """
    __tablename__ = 'message_content'  # noqa

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id，主键')
    related_id = Column(BigInteger, comment='关联对象id')
    content = Column(String, comment='消息正文')

    __no__update_time__ = True
    __idx_list__ = ('related_id', )
