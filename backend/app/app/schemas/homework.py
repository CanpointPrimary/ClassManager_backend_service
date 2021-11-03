#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/9/24
# Author: gray

"""
结构体模型类 - 作业 相关
"""

from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel, validator, root_validator, conlist


class HomeworkAssignScope(BaseModel):
    class_id: int
    groups: List[int] = None

    @validator('groups')
    def validate_groups(cls, v):  # noqa
        if not v:
            return v
        if len(set(v)) != len(v):
            raise ValueError(f'Duplicate groups in {v}')


class SchoolHomeworkAttachment(BaseModel):
    images: conlist(int, max_items=12) = []
    videos: conlist(int, max_items=3) = []
    audios: conlist(int, max_items=3) = []
    docs: conlist(int, max_items=3) = []


class SchoolHomework(SchoolHomeworkAttachment):
    title: str
    desc: str
    pub_time: datetime
    end_time: datetime

    @validator('pub_time', 'end_time')
    def validate_pub_time(cls, v, field):  # noqa
        time_type = 'pub time' if field.name == 'pub_time' else 'end time'
        if v < datetime.today():
            raise ValueError(f'The {time_type} must be later than the current time')
        if v.date() >= (datetime.today() + timedelta(7)).date():
            raise ValueError(f'The {time_type} cannot be one week '
                             'later than the current day')
        return v

    @root_validator(pre=True)
    def validate_root(cls, values):  # noqa
        if values['pub_time'] >= values['end_time']:
            raise ValueError('The end time must be later than the pub time')
        return values

    @validator('title')
    def validate_title_length(cls, v):  # noqa
        if len(v) > 20:
            raise ValueError('Title length out of limit')
        return v


class SchoolHomeworkAssign(SchoolHomework):
    scope: List[HomeworkAssignScope]

    @validator('scope')
    def validate_scope_numbers(cls, v):  # noqa
        if not v or len(v) > 10:
            raise ValueError('Homework assign scope out of limit')
        return v


class SchoolHomeworkAnswer(SchoolHomeworkAttachment):
    desc: str
