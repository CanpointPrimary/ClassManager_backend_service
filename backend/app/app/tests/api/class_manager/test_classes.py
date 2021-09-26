#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/8/9
# Author: gray

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.constants import DBConst
from app.core.config import settings
from app.models import Class, ClassMember
from app.tests.utils.utils import random_lower_string


def test_get_class_id_by_telephone(
    client: TestClient, token_headers: dict, db: Session
) -> None:
    fake_phone_no = '13111111111'
    fake_name = random_lower_string()
    fake_school_id = 999999
    fake_class = 2
    fake_grade = 2

    class_ = db.query(Class).filter(
        Class.school_id == fake_school_id,
        Class.class_ == fake_class,
        Class.grade == fake_grade,
    ).first()

    if not class_:
        class_ = Class(
            school_id=fake_school_id, class_=fake_class, grade=fake_grade
        )
        db.add(class_)
        db.commit()

    headteacher = db.query(ClassMember).filter(
        ClassMember.class_id == class_.id,
        ClassMember.member_role == DBConst.HEADTEACHER
    ).first()

    if not headteacher:
        headteacher = ClassMember(
            class_id=class_.id,
            name=fake_name,
            member_role=DBConst.HEADTEACHER,
            telephone=fake_phone_no,
        )
        db.add(headteacher)
        db.commit()
    fake_phone_no = headteacher.telephone

    resp = client.get(
        f'{settings.CLASS_MANAGER_STR}/classes/class_codes/',
        headers=token_headers,
        params={'telephone': fake_phone_no}
    )
    assert resp.status_code == 200
    content = resp.json()
    assert content
    assert content.get('class_code') == class_.id
