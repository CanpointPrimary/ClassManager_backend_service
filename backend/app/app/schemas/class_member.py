#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/9/8
# Author: gray

from pydantic import BaseModel, constr


TELEPHONE_REGEX = r'^1[358]\d{9}$|^147\d{8}$|^179\d{8}$'


class ClassMember(BaseModel):
    name: str
    family_relation: str = None
    subject_id: int = None
    telephone: constr(regex=TELEPHONE_REGEX)
