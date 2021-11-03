#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date: 2021/10/20
# @Author: gray

"""
约束类型
"""

from pydantic.types import constr


Str = constr(min_length=1, strip_whitespace=True)
Str10 = constr(min_length=1, max_length=10, strip_whitespace=True)
StrLeast10 = constr(min_length=10, strip_whitespace=True)
