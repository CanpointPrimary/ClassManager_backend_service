#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/8/30
# Author: gray

"""
CRUD模块 - 用户反馈相关 非复杂业务CRUD
"""

from app.crud.base import CRUDBase
from app.models import Feedback


class CRUDFeedback(CRUDBase[Feedback, Feedback, Feedback]):
    """
    用户反馈相关CRUD  模型类: Feedback  数据表: feedback
    """
    ...


feedback = CRUDFeedback(Feedback)
