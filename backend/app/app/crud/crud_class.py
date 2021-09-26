#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/7/30
# Author: gray

"""
CRUD模块 - 学校相关 非复杂业务CRUD
"""

from typing import List, Tuple

from sqlalchemy.engine.row import Row
from sqlalchemy.orm import Session
from sqlalchemy.sql import false, func, null

from app.crud.base import CRUDBase
from app.constants import DBConst
from app.models import Apply4Class, Class, ClassMember, \
    Group, GroupMember, Subject, School


class CRUDClass(CRUDBase[Class, Class, Class]):
    """
    班级相关CRUD  模型类: Class  数据表: class
    """
    def update_audit_need_for_joining(
        self, db: Session, member_id: int, need_audit: bool
    ) -> int:
        """
        修改班级入班是否需要审核
        """
        sq = db.query(ClassMember.class_id.label('class_id')).filter(
            ClassMember.id == member_id, ClassMember.is_delete == false()
        ).subquery()
        res = db.query(self.model).filter(Class.id == sq.c.class_id)\
            .update({Class.need_audit: need_audit}, synchronize_session=False)
        db.commit()
        return res

    def class_exists(self, db: Session, class_id: int) -> Row:
        """
        查询 class_id 对应班级是否存在
        """
        return (
            db.query(self.model.id, self.model.contact, self.model.need_audit)
            .filter(
                Class.id == class_id,
                Class.is_delete == false(),
            )
            .first()
        )

    def get_class_id_by_telephone(self, db: Session, telephone: int) -> int:
        """
        根据班主任的电话号码获取班级码
        """
        return (
            db.query(self.model.id.label('class_code'))
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
    def is_teacher_in_class(self, db: Session, user_id: int) -> Row:
        """
        查询老师是否在班，如已在班，返回任教学科
        """
        return (
            db.query(
                self.model.subject_id.label('id'), Subject.name.label('name')
            )
            .join(Subject, self.model.subject_id == Subject.id)
            .filter(
                ClassMember.user_id == user_id,
                ClassMember.member_role.in_(
                    (DBConst.HEADTEACHER, DBConst.TEACHER)
                ),
                ClassMember.is_delete == false(),
            )
            .first()
        )

    def is_student_in_class(self, db: Session, user_id: int, name: str) -> Row:
        """
        查询学生是否已在班
        """
        return (
            db.query(func.count(self.model.id))
            .filter(
                ClassMember.user_id == user_id,
                ClassMember.name == name,
                ClassMember.is_delete == false(),
            )
            .scalar()
        )

    def get_family_members(self, db: Session, class_id: int, name: str) -> List[Row]:
        """
        根据班级码和学生姓名查询亲属列表
        """
        return (
            db.query(self.model.id, self.model.name,
                     self.model.family_relation, self.model.telephone)
            .filter(
                ClassMember.class_id == class_id,
                ClassMember.name == name,
                ClassMember.member_role == DBConst.STUDENT,
                ClassMember.is_delete == false(),
            )
            .all()
        )

    def get_current_member(self, db: Session, user_id: int, member_id: int) -> Row:
        """
        查询当前用户的班级成员信息
        """
        return (
            db.query(self.model.id, self.model.class_id, self.model.name,
                     self.model.member_role, self.model.subject_id,
                     self.model.family_relation, Class.class_, Class.grade)
            .join(Class, ClassMember.class_id == Class.id)
            .filter(
                ClassMember.id == member_id,
                ClassMember.user_id == user_id,
                ClassMember.is_delete == false(),
                Class.is_delete == false(),
            )
            .first()
        )

    def get_class_list(
        self, db: Session, user_id: int, page: int, page_size: int
    ) -> List[Tuple[Row, int]]:
        """
        根据用户id查询其所在班级列表
        """
        return (
            db.query(func.count(self.model.id).over().label('total'),
                     self.model.id, self.model.class_id.label('class_code'),
                     self.model.name, self.model.member_role,
                     self.model.family_relation, Class.class_, Class.grade,
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

    def get_member_role(self, db: Session, member_id: int) -> Row:
        """
        查询当前班级成员的角色
        """
        return (
            db.query(self.model.class_id,
                     self.model.member_role,
                     self.model.is_delete)
            .filter(ClassMember.id == member_id)
            .first()
        )

    def get_class_id(self, db: Session, member_id: int) -> int:
        """
        根据 member_id 查询成员当前所在班的 class_id
        """
        return (
            db.query(self.model.class_id)
            .filter(
                ClassMember.member_id == member_id,
                ClassMember.is_delete == false(),
            )
            .first()
        )

    def get_class_members(self, db: Session, class_id: int) -> List[Row]:
        """
        根据 class_id 查询该班所有班级成员的信息
        """
        return (
            db.query(self.model.id, self.model.name, self.model.member_role,
                     self.model.family_relation, self.model.subject_id,
                     self.model.telephone)
            .filter(
                ClassMember.class_id == class_id,
                ClassMember.is_delete == false(),
            )
            .order_by(ClassMember.create_time.desc())
            .all()
        )

    def subject_teacher_exists(
        self, db: Session, class_id: int, subject_id: int
    ) -> Row:
        """
        查询对应科目是否已有任课老师，如有，返回该科目名称
        """
        return (
            db.query(self.model.id, Subject.name)
            .join(Subject, self.model.subject_id == Subject.id)
            .filter(
                ClassMember.class_id == class_id,
                ClassMember.subject_id == subject_id,
                ClassMember.is_delete == false(),
                Subject.is_delete == false(),
            )
            .first()
        )

    def member_exists(self, db: Session, member_id: int, user_id: int) -> int:
        """
        查询班级成员是否存在
        """
        return (
            db.query(func.count(self.model.id))
            .filter(
                ClassMember.id == member_id,
                ClassMember.user_id == user_id,
                ClassMember.is_delete == false(),
            )
            .scalar()
        )

    def update_member(self, db: Session, member_id: int, member: Row) -> int:
        """
        更新班级成员信息
        """
        res = (
            db.query(self.model)
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

    def delete_member(self, db: Session, member_id: int) -> int:
        """
        删除班级成员
        """
        res = (
            db.query(self.model)
            .filter(ClassMember.id == member_id)
            .update({ClassMember.is_delete: True})
        )
        db.commit()
        return res

    def check_group_members(
        self, db: Session, class_id: int, members: List[int]
    ) -> int:
        """
        检查小组成员是否都在班级成员中
        """
        return (
            db.query(func.count(self.model.id))
            .filter(
                ClassMember.class_id == class_id,
                ClassMember.member_role == DBConst.STUDENT,
                ClassMember.id.in_(members),
                ClassMember.is_delete == false(),
            )
            .scalar()
        )


class CRUDApply4Class(CRUDBase[Apply4Class, Apply4Class, Apply4Class]):
    """
    班级成员相关CRUD  模型类: ClassMember  数据表: class_member
    """
    def get_apply_records(self, db: Session, class_id: int) -> List[Row]:
        """
        根据 class_id 查询该班级的所有审核记录
        """
        return (
            db.query(self.model.id, self.model.name, self.model.subject_id,
                     self.model.family_relation, self.model.telephone,
                     self.model.result, self.model.create_time)
            .filter(self.model.class_id == class_id)
            .all()
        )

    def get_reviewing_list(
        self, db: Session, user_id: int, page: int, page_size: int, rejected: bool
    ) -> List[Row]:
        """
        根据用户id查询审核未通过的入班申请
        """
        if rejected:
            filter_cond = Apply4Class.result != DBConst.PASS
        else:
            filter_cond = Apply4Class.result == DBConst.REVIEWING
        return (
            db.query(func.count(self.model.id).over().label('total'),
                     self.model.id, self.model.name, self.model.family_relation,
                     self.model.subject_id, self.model.result,
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

    def teacher_apply_exists(
        self, db: Session, user_id: int, class_id: int
    ) -> int:
        """
        查询老师的入班申请是否已提交，如已提交，返回入班申请相关信息
        """
        return (
            db.query(func.count(self.model.id))
            .filter(
                Apply4Class.user_id == user_id,
                Apply4Class.class_id == class_id,
                Apply4Class.result != DBConst.REJECT,
                Apply4Class.subject_id != null(),
            )
            .scalar()
        )

    def student_apply_exists(
        self, db: Session, user_id: int, class_id: int
    ) -> List[Row]:
        """
        查询 同一用户在同一班级内同一学生名字提交学生入班申请的数量
        """
        return (
            db.query(self.model.name)
            .filter(
                Apply4Class.user_id == user_id,
                Apply4Class.class_id == class_id,
                Apply4Class.result != DBConst.REJECT,
                Apply4Class.subject_id == null(),
            )
            .all()
        )

    def get_apply_by_id(self, db: Session, user_id: int, apply_id: int) -> Row:
        """
        根据id查询入班申请信息
        """
        return (
            db.query(
                self.model.name, self.model.subject_id, self.model.class_id,
                self.model.family_relation, self.model.telephone,
            )
            .filter(
                Apply4Class.id == apply_id,
                Apply4Class.user_id == user_id,
            )
            .first()
        )

    def is_apply_reviewing(self, db: Session, apply_id: int, class_id: int) -> Row:
        """
        根据id查询入班申请申请人id、申请状态
        """
        return (
            db.query(self.model.result)
            .filter(
                Apply4Class.id == apply_id,
                Apply4Class.class_id == class_id,
            )
            .first()
        )

    def update_apply_result(
        self, db: Session, apply_id: int, member_id: int, result: str
    ) -> int:
        """
        修改入班申请审核结果
        """
        res = db.query(self.model).filter(Apply4Class.id == apply_id)\
            .update(
            {Apply4Class.result: result, Apply4Class.auditor_member_id: member_id}
        )
        db.commit()
        return res


class CRUDGroup(CRUDBase[Group, Group, Group]):
    """
    班级小组相关CRUD  模型类: Group  数据表: group
    """
    def get_groups_of_class(self, db: Session, class_id: int) -> List[Group]:
        """
        根据班级id查询该班所有班级小组信息
        """
        return db.query(self.model).filter(Group.class_id == class_id).all()

    def group_exists(
        self, db: Session, class_id: int, name: str = None, group_id: int = None
    ) -> int:
        """
        判断小组是否存在
        """
        filter_cond = [Group.class_id == class_id]
        filter_cond.append(Group.name == name) if name else ...
        filter_cond.append(Group.id == group_id) if group_id else ...
        return db.query(func.count(self.model.id)).filter(*filter_cond).scalar()

    def update_group(self, db: Session, group_id, name: str) -> int:
        """
        更新班级小组信息
        """
        res = db.query(self.model).filter(Group.group_id == group_id)\
            .update({Group.name: name})
        db.commit()
        return res

    def delete_by_id(self, db: Session, group_id) -> int:
        """
        根据 小组id 删除小组
        """
        res = db.query(self.model).filter(Group.id == group_id).delete()
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
            db.query(ClassMember.id, ClassMember.name, ClassMember.family_relation)
            .join(ClassMember, ClassMember.id == GroupMember.member_id)
            .filter(
                GroupMember.group_id == group_id,
                ClassMember.class_id == class_id,
                ClassMember.is_delete == false(),
            )
            .all()
        )

    def get_ids_to_del(
        self, db: Session, group_id: int, members: List[int]
    ) -> List[Row]:
        """
        查询需要删除的组员的id
        """
        return (
            db.query(self.model.id)
            .filter(
                GroupMember.group_id == group_id,
                GroupMember.member_id.notin_(members),
            )
            .all()
        )

    def delete_by_id(self, db: Session, ids2del: List[int]) -> int:
        """
        根据 成员id 删除组员
        """
        res = db.query(self.model).filter(GroupMember.id.in_(ids2del)).delete()
        db.commit()
        return res

    def delete_by_group(self, db: Session, group_id):
        """
        根据 小组id 删除组员
        """
        res = db.query(self.model).filter(GroupMember.group_id == group_id).delete()
        db.commit()
        return res


class_ = CRUDClass(Class)
class_member = CRUDClassMember(ClassMember)
apply4class = CRUDApply4Class(Apply4Class)
group = CRUDGroup(Group)
group_member = CRUDGroupMember(GroupMember)
