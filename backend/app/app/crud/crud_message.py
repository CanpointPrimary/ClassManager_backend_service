#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date: 2021/10/15
# @Author: gray

"""
CRUD模块 - 消息相关
"""

from sqlalchemy.orm import aliased, Session
from sqlalchemy.sql import and_, false, insert, text

from app.crud.base import CRUDBase
from app.constants import DBConst
from app.models import ClassMember, Group, Homework, HomeworkAssign, Message, \
    MessageContent


class CRUDMessage(CRUDBase[Message, Message, Message]):
    """消息相关CRUD
    模型类: Message  数据表: message
    """
    @staticmethod
    def send_update_homework_msg(
        db: Session, homework_id: int, user_id: int, content_id: int
    ) -> None:
        """根据 作业id、发布人用户id，向该作业发布的所有学生发送消息"""
        teacher = aliased(ClassMember)
        group_union_query = (
            db.query(
                teacher.id,
                text(f"'{DBConst.SCHOOL_HOMEWORK_HINT}'"),
                ClassMember.class_id,
                ClassMember.name,
                text(f'{content_id}')
            )
            .distinct(ClassMember.name, ClassMember.class_id)
            .join(teacher, teacher.class_id == ClassMember.class_id)
            .join(Group, and_(Group.class_id == ClassMember.id,
                              Group.name == ClassMember.name))
            .join(HomeworkAssign, and_(HomeworkAssign.class_id == Group.class_id,
                                       HomeworkAssign.group_id == Group.id))
            .join(Homework, Homework.id == HomeworkAssign.homework_id)
            .filter(
                Homework.id == homework_id,
                Homework.publisher_id == user_id,
                Homework.is_delete == false(),
                teacher.user_id == user_id,
            )
        )
        class_union_query = (
            db.query(
                teacher.id,
                text(f"'{DBConst.SCHOOL_HOMEWORK_HINT}'"),
                ClassMember.class_id,
                ClassMember.name,
                text(f'{content_id}')
            )
            .distinct(ClassMember.name, ClassMember.class_id)
            .join(teacher, teacher.class_id == ClassMember.class_id)
            .join(HomeworkAssign, HomeworkAssign.class_id == ClassMember.class_id)
            .join(Homework, Homework.id == HomeworkAssign.homework_id)
            .filter(
                Homework.id == homework_id,
                Homework.publisher_id == user_id,
                Homework.is_delete == false(),
                HomeworkAssign.group_id == DBConst.ASSIGNED4WHOLE_CLASS,
                ClassMember.member_role == DBConst.STUDENT,
                teacher.user_id == user_id,
            )
        )
        query = group_union_query.union_all(class_union_query)

        insert_sql_obj = insert(Message.__table__).from_select(
            [
                Message.sender_member_id,
                Message.category,
                Message.receiver_class_id,
                Message.receiver,
                Message.content_id,
            ],
            query
        )
        return db.execute(insert_sql_obj)


class CRUDMessageContent(CRUDBase[MessageContent, MessageContent, MessageContent]):
    """消息内容相关CRUD
    模型类: MessageContent  数据表: message_content
    """
    ...


message = CRUDMessage(Message)
message_content = CRUDMessageContent(MessageContent)
