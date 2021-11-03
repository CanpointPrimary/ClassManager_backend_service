#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date: 2021/7/7
# @Author: gray

"""
ORM模型
统一导入模型类，供Alembic数据库迁移时自动生成迁移脚本
如果新增了模型类，请在此处导入新增的模型类，否则自动生成迁移脚本时不会生成对应的表
"""

from app.models.base import Base
from app.models.classes import Apply4Class, Class, ClassMember, Group, \
    GroupMember
from app.models.feedback import Feedback
from app.models.file import FileInfo, FileReference
from app.models.homework import Homework, HomeworkAnswer, HomeworkAnswerStatus,\
    HomeworkAssign, HomeworkEvaluate, HomeworkAnswerCheck
from app.models.message import Message, MessageContent
from app.models.page import HomepageMenu, EntrancePage
from app.models.school import School
from app.models.subject import Subject
from app.models.system import Region, SysConfig
from app.models.user import User
