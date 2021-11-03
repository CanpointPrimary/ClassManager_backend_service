#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date: 2021/7/8
# @Author: gray

"""
ORM模型类 - 作业相关
"""

from sqlalchemy import UniqueConstraint
from sqlalchemy.schema import Column
from sqlalchemy.sql import text
from sqlalchemy.types import BigInteger, Boolean, Integer, String, Text, TIMESTAMP

from app.models.base import Base


class Homework(Base):
    """作业
    数据表: homework - 描述发布的作业本身的信息
    """
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id，主键')
    publisher_id = Column(BigInteger, nullable=False, comment='发布者用户id')
    subject_id = Column(Integer, nullable=False, comment='学科id')
    pub_time = Column(TIMESTAMP, nullable=False, comment='发布时间')
    end_time = Column(TIMESTAMP, nullable=False, comment='截止时间')
    title = Column(String(20), nullable=False, comment='作业标题')
    desc = Column(Text, nullable=False, comment='作业描述')
    is_delete = Column(
        Boolean, nullable=False, server_default=text('False'), comment='是否删除'
    )

    __idx_list__ = ('publisher_id', 'pub_time', 'end_time')


class HomeworkAssign(Base):
    """作业发布范围
    数据表: homework_scope - 描述作业的发布范围
    """
    __tablename__ = 'homework_assign'  # noqa

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id，主键')
    homework_id = Column(BigInteger, nullable=False, comment='作业id')
    class_id = Column(BigInteger, nullable=False, comment='班级id')
    group_id = Column(BigInteger, nullable=False, comment='小组id，0 表示全班')

    __no_create_time__ = True
    __no_update_time__ = True
    __idx_list__ = ('homework_id', 'class_id', 'group_id')
    __arg_list__ = (UniqueConstraint('homework_id', 'class_id', 'group_id'), )


class HomeworkAnswer(Base):
    """作业作答
    数据表: homework_answer - 描述学生的作业作答信息
    """
    __tablename__ = 'homework_answer'  # noqa

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id，主键')
    submitter_member_id = Column(BigInteger, nullable=False, comment='提交人成员id')
    homework_id = Column(BigInteger, nullable=False, comment='作业id')
    status_id = Column(BigInteger, nullable=False, comment='关联的作业作答情况id')
    evaluation_id = Column(BigInteger, comment='关联的作业点评id')
    answer_check_id = Column(BigInteger, comment='关联的作业批改id')
    category = Column(String(2), nullable=False, server_default='1', comment='作答类型: '
                                                                             '1-作答'
                                                                             '2-重做'
                                                                             '3-订正')
    desc = Column(Text, nullable=False, comment='作答描述')

    __idx_list__ = ('submitter_member_id', )


class HomeworkAnswerStatus(Base):
    """作业作答情况
    数据表: homework_answer_status - 描述学生的作业作答情况
    """
    __tablename__ = 'homework_answer_status'  # noqa

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id，主键')
    homework_id = Column(BigInteger, nullable=False, comment='作业id')
    student_class_id = Column(BigInteger, nullable=False, comment='学生所属班级id')
    student_name = Column(String, nullable=False, comment='学生姓名')
    score = Column(String(2), comment='作业评分: A B C D E 0表示已阅')
    status = Column(String(2), nullable=False, server_default='1', comment='作业状态 '
                                                                           '1-待提交 '
                                                                           '2-已提交 '
                                                                           '3-待重做 '
                                                                           '4-已批改 '
                                                                           '5-已订正 '
                                                                           '6-未反馈')

    __idx_list__ = ('homework_id', 'student_class_id', 'student_name')


class HomeworkEvaluate(Base):
    """作业点评
    数据表: homework_comment - 描述学生的作业点评信息
    """
    __tablename__ = 'homework_comment'  # noqa

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id，主键')
    reviewer_member_id = Column(BigInteger, nullable=False, comment='点评人成员id')
    comment = Column(String, nullable=False, comment='点评正文')
    rejected = Column(
        Boolean, nullable=False, server_default=text('False'), comment='是否打回'
    )
    score = Column(String(2), comment='作业评分: A B C D E 0表示已阅')

    __idx_list__ = ('reviewer_member_id', )


class HomeworkAnswerCheck(Base):
    """作业批改
    数据表: homework_answer_comment - 描述老师对学生作业作答的批改
    """
    __tablename__ = 'homework_answer_check'  # noqa

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id，主键')
    reviewer_member_id = Column(BigInteger, nullable=False, comment='批改人成员id')
    category = Column(String(2), nullable=False, comment='批改类型: 1-大图批改')
    content = Column(String, nullable=False, comment='批改内容')

    __idx_list__ = ('reviewer_member_id', )
