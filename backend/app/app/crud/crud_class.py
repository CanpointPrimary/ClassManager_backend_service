#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/7/30
# Author: gray

"""
CRUD模块 - 学校相关 非复杂业务CRUD
"""

from typing import List, Tuple, Optional, Set

from sqlalchemy.engine.row import Row
from sqlalchemy.orm import Session
from sqlalchemy.sql import false, func, null, text, true

from app.crud.base import CRUDBase
from app.constants import DBConst
from app.models import Apply4Class, Class, ClassMember, \
    Group, GroupMember, Subject, School


class CRUDClass(CRUDBase[Class, Class, Class]):
    """
    班级相关CRUD  模型类: Class  数据表: class
    """
    @staticmethod
    def update_audit_need_for_joining(
        db: Session, class_id: int, need_audit: bool
    ) -> int:
        """
        修改班级入班是否需要审核
        """
        res = (
            db.query(Class)
            .filter(Class.id == class_id)
            .update({Class.need_audit: need_audit})
        )
        db.commit()
        return res

    @staticmethod
    def class_exists(db: Session, class_id: int) -> Row:
        """
        查询 class_id 对应班级是否存在
        """
        return (
            db.query(Class.id, Class.contact, Class.need_audit)
            .filter(
                Class.id == class_id,
                Class.is_delete == false(),
            )
            .first()
        )

    @staticmethod
    def get_class_id_by_telephone(db: Session, telephone: int) -> int:
        """
        根据班主任的电话号码获取班级码
        """
        return (
            db.query(Class.id.label('class_code'))
            .filter(
                Class.contact == telephone,
                Class.is_delete == false(),
            )
            .first()
        )


class CRUDClassMember(CRUDBase[ClassMember, ClassMember, ClassMember]):
    """
    班级成员相关CRUD  模型类: ClassMember  数据表: class_member
    """
    @staticmethod
    def is_teacher_in_class(db: Session, user_id: int) -> Row:
        """
        查询老师是否在班，如已在班，返回任教学科
        """
        return (
            db.query(ClassMember.subject_id.label('id'), Subject.name.label('name'))
            .join(Subject, ClassMember.subject_id == Subject.id)
            .filter(
                ClassMember.user_id == user_id,
                ClassMember.member_role.in_((DBConst.HEADTEACHER, DBConst.TEACHER)),
                ClassMember.is_delete == false(),
            )
            .first()
        )

    @staticmethod
    def is_student_in_class(db: Session, user_id: int, name: str) -> Optional[int]:
        """
        查询学生是否已在班
        """
        return (
            db.query(text('1'))
            .filter(
                ClassMember.user_id == user_id,
                ClassMember.name == name,
                ClassMember.is_delete == false(),
            )
            .scalar()
        )

    @staticmethod
    def get_family_members(db: Session, class_id: int, name: str) -> List[Row]:
        """
        根据班级码和学生姓名查询亲属列表
        """
        return (
            db.query(ClassMember.id, ClassMember.name,
                     ClassMember.family_relation, ClassMember.telephone)
            .filter(
                ClassMember.class_id == class_id,
                ClassMember.name == name,
                ClassMember.member_role == DBConst.STUDENT,
                ClassMember.is_delete == false(),
            )
            .all()
        )

    @staticmethod
    def get_current_member(db: Session, user_id: int, member_id: int) -> Row:
        """
        查询当前用户的班级成员信息
        """
        return (
            db.query(ClassMember.id, ClassMember.class_id, ClassMember.name,
                     ClassMember.member_role, ClassMember.subject_id,
                     ClassMember.family_relation, Class.class_, Class.grade)
            .join(Class, ClassMember.class_id == Class.id)
            .filter(
                ClassMember.id == member_id,
                ClassMember.user_id == user_id,
                ClassMember.is_delete == false(),
                Class.is_delete == false(),
            )
            .first()
        )

    @staticmethod
    def get_class_list(
        db: Session, user_id: int, page: int, page_size: int
    ) -> List[Tuple[Row, int]]:
        """
        根据用户id查询其所在班级列表
        """
        return (
            db.query(func.count(ClassMember.id).over().label('total'),
                     ClassMember.id, ClassMember.class_id.label('class_code'),
                     ClassMember.name, ClassMember.member_role,
                     ClassMember.family_relation, Class.class_, Class.grade,
                     School.id.label('school_id'),
                     School.name.label('school_name'))
            .join(Class, ClassMember.class_id == Class.id)
            .outerjoin(School, School.id == Class.school_id)
            .filter(
                ClassMember.user_id == user_id,
                ClassMember.is_delete == false(),
                Class.is_delete == false(),
            )
            .order_by(ClassMember.create_time.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

    @staticmethod
    def get_teacher_class_charge_list(
        db: Session, user_id: int, subject_id: int, class_set: Set[int]
    ) -> List[Row]:
        """
        根据 用户id、科目id 获取教师执教班级列表
        """
        return (
            db.query(ClassMember.id, ClassMember.class_id)
            .filter(
                ClassMember.user_id == user_id,
                ClassMember.class_id.in_(class_set) if class_set else 1 == 1,
                ClassMember.is_delete == false(),
                ClassMember.subject_id == subject_id
            )
            .all()
        )

    @staticmethod
    def get_member_info(db: Session, member_id: int) -> Row:
        """
        查询当前班级成员的角色
        """
        return (
            db.query(ClassMember.class_id, ClassMember.member_role,
                     ClassMember.subject_id, ClassMember.is_delete, ClassMember.name)
            .filter(ClassMember.id == member_id)
            .first()
        )

    @staticmethod
    def get_class_id(db: Session, member_id: int) -> Row:
        """
        根据 member_id 查询成员当前所在班的 class_id
        """
        return (
            db.query(ClassMember.class_id)
            .filter(
                ClassMember.member_id == member_id,
                ClassMember.is_delete == false(),
            )
            .first()
        )

    @staticmethod
    def get_class_members(db: Session, class_id: int) -> List[Row]:
        """
        根据 class_id 查询该班所有班级成员的信息
        """
        return (
            db.query(ClassMember.id, ClassMember.name, ClassMember.member_role,
                     ClassMember.family_relation, ClassMember.subject_id,
                     ClassMember.telephone)
            .filter(
                ClassMember.class_id == class_id,
                ClassMember.is_delete == false(),
            )
            .order_by(ClassMember.create_time.desc())
            .all()
        )

    @staticmethod
    def subject_teacher_exists(db: Session, class_id: int, subject_id: int) -> Row:
        """
        查询对应科目是否已有任课老师，如有，返回该科目名称
        """
        return (
            db.query(ClassMember.id, Subject.name)
            .join(Subject, ClassMember.subject_id == Subject.id)
            .filter(
                ClassMember.class_id == class_id,
                ClassMember.subject_id == subject_id,
                ClassMember.is_delete == false(),
                Subject.is_delete == false(),
            )
            .first()
        )

    @staticmethod
    def member_exists(db: Session, member_id: int, user_id: int) -> Optional[int]:
        """
        查询班级成员是否存在
        """
        return (
            db.query(text('1'))
            .filter(
                ClassMember.id == member_id,
                ClassMember.user_id == user_id,
                ClassMember.is_delete == false(),
            )
            .scalar()
        )

    @staticmethod
    def update_member(db: Session, member_id: int, member: Row) -> int:
        """
        更新班级成员信息
        """
        res = (
            db.query(ClassMember)
            .filter(ClassMember.id == member_id)
            .update(
                {
                    ClassMember.name: member.name,
                    ClassMember.family_relation: member.family_relation,
                    ClassMember.subject_id: member.subject_id,
                    ClassMember.telephone: member.telephone,
                }
            )
        )
        db.commit()
        return res

    @staticmethod
    def delete_member(db: Session, member_id: int) -> int:
        """
        删除班级成员
        """
        res = (
            db.query(ClassMember)
            .filter(ClassMember.id == member_id)
            .update({ClassMember.is_delete: true()})
        )
        db.commit()
        return res

    @staticmethod
    def get_stu_names(
        db: Session, class_id: int, stu_names: List[str] = None
    ) -> List[Row]:
        """
        根据 班级id、学生姓名列表 查询 对应班级的姓名在列表中的学生，返回所有的学生姓名
        """
        return (
            db.query(ClassMember.name)
            .distinct(ClassMember.name)
            .filter(
                ClassMember.class_id == class_id,
                ClassMember.member_role == DBConst.STUDENT,
                ClassMember.name.in_(stu_names) if stu_names else 1 == 1,
                ClassMember.is_delete == false(),
            )
            .all()
        )


class CRUDApply4Class(CRUDBase[Apply4Class, Apply4Class, Apply4Class]):
    """
    班级成员相关CRUD  模型类: ClassMember  数据表: class_member
    """
    @staticmethod
    def get_apply_records(db: Session, class_id: int) -> List[Row]:
        """
        根据 class_id 查询该班级的所有审核记录
        """
        return (
            db.query(Apply4Class.id, Apply4Class.name, Apply4Class.subject_id,
                     Apply4Class.family_relation, Apply4Class.telephone,
                     Apply4Class.result, Apply4Class.create_time)
            .filter(Apply4Class.class_id == class_id)
            .all()
        )

    @staticmethod
    def get_reviewing_list(
        db: Session, user_id: int, page: int, page_size: int, rejected: bool
    ) -> List[Row]:
        """
        根据用户id查询审核未通过的入班申请
        """
        if rejected:
            filter_cond = Apply4Class.result != DBConst.PASS
        else:
            filter_cond = Apply4Class.result == DBConst.REVIEWING
        return (
            db.query(func.count(Apply4Class.id).over().label('total'),
                     Apply4Class.id, Apply4Class.name, Apply4Class.family_relation,
                     Apply4Class.subject_id, Apply4Class.result,
                     Class.class_.label('class'), Class.grade)
            .join(Class, Apply4Class.class_id == Class.id)
            .filter(
                Apply4Class.user_id == user_id,
                filter_cond,
                Class.is_delete == false(),
            )
            .order_by(Apply4Class.create_time.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

    @staticmethod
    def teacher_apply_exists(
        db: Session, user_id: int, class_id: int
    ) -> Optional[int]:
        """
        查询老师的入班申请是否已提交
        """
        return (
            db.query(text('1'))
            .filter(
                Apply4Class.user_id == user_id,
                Apply4Class.class_id == class_id,
                Apply4Class.result != DBConst.REJECT,
                Apply4Class.subject_id != null(),
            )
            .scalar()
        )

    @staticmethod
    def student_apply_exists(
        db: Session, user_id: int, class_id: int
    ) -> List[Row]:
        """
        查询 同一用户在同一班级内同一学生名字提交学生入班申请的数量
        """
        return (
            db.query(Apply4Class.name)
            .filter(
                Apply4Class.user_id == user_id,
                Apply4Class.class_id == class_id,
                Apply4Class.result != DBConst.REJECT,
                Apply4Class.subject_id == null(),
            )
            .all()
        )

    @staticmethod
    def get_apply_by_id(db: Session, user_id: int, apply_id: int) -> Row:
        """
        根据id查询入班申请信息
        """
        return (
            db.query(Apply4Class.name, Apply4Class.subject_id,
                     Apply4Class.class_id, Apply4Class.family_relation,
                     Apply4Class.telephone)
            .filter(
                Apply4Class.id == apply_id,
                Apply4Class.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def is_apply_reviewing(db: Session, apply_id: int, class_id: int) -> Row:
        """
        根据id查询入班申请申请人id、申请状态
        """
        return (
            db.query(Apply4Class.result)
            .filter(
                Apply4Class.id == apply_id,
                Apply4Class.class_id == class_id,
            )
            .first()
        )

    @staticmethod
    def update_apply_result(
        db: Session, apply_id: int, member_id: int, result: str
    ) -> int:
        """
        修改入班申请审核结果
        """
        res = (
            db.query(Apply4Class).filter(Apply4Class.id == apply_id)
            .update(
                {
                    Apply4Class.result: result,
                    Apply4Class.auditor_member_id: member_id,
                }
            )
        )
        db.commit()
        return res


class CRUDGroup(CRUDBase[Group, Group, Group]):
    """
    班级小组相关CRUD  模型类: Group  数据表: group
    """
    @staticmethod
    def get_class_groups(db: Session, class_id: int) -> List[Row]:
        """
        根据班级id查询该班所有班级小组信息
        """
        return (
            db.query(Group.id, Group.name)
            .filter(Group.class_id == class_id)
            .all()
        )

    @staticmethod
    def group_exists(
        db: Session, class_id: int, name: str = None, group_id: int = None
    ) -> Optional[int]:
        """
        判断小组是否存在
        """
        filter_cond = [Group.class_id == class_id]
        filter_cond.append(Group.name == name) if name else ...
        filter_cond.append(Group.id == group_id) if group_id else ...
        return db.query(text('1')).filter(*filter_cond).scalar()

    @staticmethod
    def update_group_name(db: Session, group_id, name: str) -> int:
        """
        更新班级小组信息
        """
        res = (
            db.query(Group)
            .filter(Group.group_id == group_id)
            .update({Group.name: name})
        )
        db.commit()
        return res

    @staticmethod
    def delete_by_id(db: Session, group_id) -> int:
        """
        根据 小组id 删除小组
        """
        res = db.query(Group).filter(Group.id == group_id).delete()
        db.commit()
        return res


class CRUDGroupMember(CRUDBase[GroupMember, GroupMember, GroupMember]):
    """
    小组成员相关CRUD  模型类: GroupMember  数据表: group_member
    """
    @staticmethod
    def get_members_of_group(db: Session, class_id: int, group_id: int) -> List[Row]:
        """
        根据 class_id 和 group_id 查询小组成员信息
        """
        return (
            db.query(ClassMember.name)
            .distinct(ClassMember.name)
            .join(ClassMember, ClassMember.name == GroupMember.name)
            .filter(
                GroupMember.group_id == group_id,
                ClassMember.class_id == class_id,
                ClassMember.is_delete == false(),
            )
            .all()
        )

    @staticmethod
    def get_names2del(
        db: Session, group_id: int, stu_names: List[str]
    ) -> List[Row]:
        """
        查询 修改小组信息时需要删除的小组成员的id
        """
        return (
            db.query(GroupMember.id)
            .filter(
                GroupMember.group_id == group_id,
                GroupMember.name.notin_(stu_names),
            )
            .all()
        )

    @staticmethod
    def delete_by_names(db: Session, names2del: List[int]) -> int:
        """
        根据 成员id 删除组员
        """
        res = db.query(GroupMember).filter(GroupMember.name.in_(names2del)).delete()
        db.commit()
        return res

    @staticmethod
    def delete_by_group_id(db: Session, group_id) -> int:
        """
        根据 小组id 删除组员
        """
        res = db.query(GroupMember).filter(GroupMember.group_id == group_id).delete()
        db.commit()
        return res


class_ = CRUDClass(Class)
class_member = CRUDClassMember(ClassMember)
apply4class = CRUDApply4Class(Apply4Class)
group = CRUDGroup(Group)
group_member = CRUDGroupMember(GroupMember)
