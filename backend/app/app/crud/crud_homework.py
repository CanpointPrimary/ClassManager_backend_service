#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date: 2021/9/17
# Author: gray

"""
CRUD模块 - 作业相关
"""

from datetime import date, timedelta
from typing import Iterable, List, Optional, Union

from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.engine import Row
from sqlalchemy.orm import aliased, Session
from sqlalchemy.sql import and_, case, false, func, null, or_, text, true

from app import schemas
from app.crud.base import CRUDBase
from app.constants import DBConst
from app.models import (
    Class, ClassMember, FileInfo, FileReference, Group, GroupMember, Homework,
    HomeworkAnswer, HomeworkAnswerStatus, HomeworkAssign, HomeworkEvaluate,
    HomeworkAnswerCheck
)


class CRUDHomework(CRUDBase[Homework, Homework, Homework]):
    """
    作业相关CRUD  模型类: Homework  数据表: homework
    """
    @staticmethod
    def info(db: Session, homework_id: int, *extra_fields) -> Row:
        """查询作业的基本信息"""
        return (
            db.query(Homework.id, Homework.is_delete, *extra_fields)
            .filter(Homework.id == homework_id)
            .first()
        )

    @staticmethod
    def is_assigned4class(
            db: Session, homework_id: int, class_id: int
    ) -> Optional[int]:
        """根据 作业id、班级id 查询该作业是否在该班发布"""
        return (
            db.query(text('1'))
            .filter(
                HomeworkAssign.homework_id == homework_id,
                HomeworkAssign.class_id == class_id,
            )
            .scalar()
        )

    @staticmethod
    def get_homework_info(db: Session, homework_id: int) -> Row:
        """根据 作业id 查询作业的基本信息"""
        return (
            db.query(Homework.id,
                     Homework.end_time,
                     Homework.title,
                     Homework.desc)
            .filter(Homework.id == homework_id)
            .first()
        )

    @staticmethod
    def delete_homework(db: Session, homework_id: int, user_id: int) -> int:
        """
        删除作业
        """
        res = (
            db.query(Homework)
            .filter(
                Homework.id == homework_id,
                Homework.publisher_id == user_id,
                Homework.is_delete == false(),
            )
            .update({Homework.is_delete: true()})
        )
        return res

    @staticmethod
    def update_homework(
        db: Session, user_id: int, homework_id: int, sch_hw: schemas.SchoolHomework
    ) -> List[Row]:
        """
        更新作业信息
        """
        update_map = {
            Homework.pub_time: sch_hw.pub_time, Homework.end_time: sch_hw.end_time,
            Homework.title: sch_hw.title, Homework.desc: sch_hw.desc,
            Homework.images: sch_hw.images, Homework.videos: sch_hw.videos,
            Homework.audios: sch_hw.audios, Homework.docs: sch_hw.docs,
        }
        res = (
            db.query(Homework)
            .filter(
                Homework.id == homework_id,
                Homework.publisher_id == user_id,
                Homework.is_delete == false(),
            )
            .update(update_map)
        )
        return res

    @staticmethod
    def is_homework_exists(
        db: Session, homework_id: int, user_id: int
    ) -> Optional[int]:
        """
        根据 作业id 和 用户id 查询该用户发布的作业是否存在
        """
        return (
            db.query(text('1'))
            .filter(
                Homework.id == homework_id,
                Homework.publisher_id == user_id,
                Homework.is_delete == false(),
            )
            .scalar()
        )


class CRUDHomeworkAssign(CRUDBase[HomeworkAssign, HomeworkAssign, HomeworkAssign]):
    """
    作业发布相关CRUD  模型类: HomeworkAssign  数据表: homework_assign
    """
    @staticmethod
    def get_homework4the_day_assigned(
        db: Session, user_id: int, classes: Iterable, pub_date: date,
    ) -> List[Row]:
        """
        根据 用户id、班级id列表、发布时间 查询当天在该班级是否已发布过作业
        """
        next_day = pub_date + timedelta(days=1)
        return (
            db.query(HomeworkAssign.class_id)
            .distinct()
            .join(Homework, Homework.id == HomeworkAssign.homework_id)
            .filter(
                Homework.pub_time >= pub_date,
                Homework.pub_time < next_day,
                Homework.publisher_id == user_id,
                Homework.is_delete == false(),
                HomeworkAssign.class_id.in_(classes),
            )
            .all()
        )

    def get_assigned_class_scopes(
        self, db: Session, user_id: int, homework_id: int, pub_date: date,
    ) -> List[Row]:
        """
        根据 用户id、作业id、新的发布日期 查询新的发布日期当天是否已发布过作业
        """
        subquery = (
            db.query(HomeworkAssign.class_id)
            .distinct()
            .filter(HomeworkAssign.homework_id == homework_id)
            .subquery()
        )
        return self.get_homework4the_day_assigned(db, user_id, subquery, pub_date)

    @staticmethod
    def validate_assign_scope(
        db: Session,
        class_assigned_list: List[int],
        group_assigned_list: List[schemas.HomeworkAssignScope]
    ) -> int:
        """
        校验作业发布范围: 小组发布的作业小组存在，全班发布的作业该班级有学生
        """
        filter_cond = [
            and_(
                Group.class_id == scope.class_id,
                Group.id.in_(scope.groups),
            )
            for scope in group_assigned_list
        ]
        groups_sub_scalar = (
            db.query(func.count(Group.id))
            .filter(or_(False, *filter_cond))
            .scalar_subquery()
        )
        subquery = (
            db.query(Class.id.label('id'), func.count(ClassMember.id))
            .join(ClassMember, ClassMember.class_id == Class.id)
            .filter(Class.id.in_(class_assigned_list))
            .group_by(Class.id)
            .subquery()
        )
        classes_sub_scalar = (
            db.query(func.count(subquery.c.id)).filter().scalar_subquery()
        )
        return db.query(groups_sub_scalar + classes_sub_scalar).scalar()

    @staticmethod
    def get_homework_assign_students(
        db: Session,
        class_assigned_list: List[int],
        group_assigned_list: List[schemas.HomeworkAssignScope],
    ) -> List[Row]:
        """
        根据作业发布范围查询作业发布范围内的所有学生的班级id、姓名
        """
        filter_cond = [
            and_(
                Group.class_id == scope.class_id,
                Group.id.in_(scope.groups),
            )
            for scope in group_assigned_list
        ]
        union_query = (
            db.query(Group.class_id, GroupMember.name)
            .distinct()
            .join(GroupMember, Group.id == GroupMember.group_id)
            .filter(or_(False, *filter_cond))
        )
        filter_cond = [
            and_(
                ClassMember.class_id == class_id,
                ClassMember.member_role == DBConst.STUDENT,
                ClassMember.is_delete == false(),
            )
            for class_id in class_assigned_list
        ]
        return (
            db.query(ClassMember.class_id, ClassMember.name)
            .distinct()
            .filter(or_(False, *filter_cond))
            .union_all(union_query)
            .all()
        )

    @staticmethod
    def get_homework_assign_available_groups(
        db: Session, user_id: int, subject_id: int, pub_date: date
    ) -> List[Row]:
        """
        查询合法的校本作业发送对象
        """
        next_day = pub_date + timedelta(days=1)
        sq = (
            db.query(HomeworkAssign.class_id)
            .distinct()
            .join(Homework, Homework.id == HomeworkAssign.homework_id)
            .filter(
                Homework.pub_time >= pub_date,
                Homework.pub_time < next_day,
                Homework.publisher_id == user_id,
                Homework.is_delete == false(),
            )
            .subquery()
        )
        return (
            db.query(
                Class.id, Class.class_, Class.grade,
                func.array_agg(
                    func.concat('{"id":"', Group.id, '","name":"', Group.name, '"}')
                )
            )
            .join(ClassMember, ClassMember.class_id == Group.class_id)
            .join(Class, Class.id == Group.class_id)
            .filter(
                ClassMember.subject_id == subject_id,
                ClassMember.user_id == user_id,
                ClassMember.member_role != DBConst.STUDENT,
                ClassMember.is_delete == false(),
                Class.id.notin_(sq),
            )
            .group_by(Class.id, Class.class_, Class.grade)
            .all()
        )


class CRUDHomeworkAnswer(CRUDBase[HomeworkAnswer, HomeworkAnswer, HomeworkAnswer]):
    """
    作业作答相关CRUD  模型类: HomeworkAnswer  数据表: homework_answer
    """
    @staticmethod
    def make_file_type_case(file_type):
        return case([(FileInfo.category == file_type, FileInfo.id)])

    @staticmethod
    def get_stu_homework_answers(db: Session, status_id: int) -> List[Row]:
        """
        查询学生作业作答信息
        """
        return (
            db.query(
                HomeworkAnswer.id.label('answer_id'),
                HomeworkAnswer.desc,
                ClassMember.name.label('reviewer'),
                HomeworkEvaluate.comment,
                HomeworkEvaluate.score,
                HomeworkEvaluate.rejected,
            )
            .outerjoin(HomeworkEvaluate,
                       HomeworkEvaluate.id == HomeworkAnswer.evaluation_id)
            .outerjoin(ClassMember,
                       ClassMember.id == HomeworkEvaluate.reviewer_member_id)
            .filter(
                HomeworkAnswer.status_id == status_id,
            )
            .all()
        )
    
    def get_homework_answer_file_ids(
        self, db: Session, status_id: Union[int, Iterable[int]]
    ) -> List[Row]:
        """
        根据 status_id 查询单个学生作业作答中引用附件的文件id
        """
        if isinstance(status_id, int):
            cond = HomeworkAnswer.status_id == status_id
        else:
            cond = HomeworkAnswer.status_id.in_(status_id)
        return (
            db.query(
                HomeworkAnswer.id,
                func.array_remove(
                    func.array_agg(self.make_file_type_case(DBConst.IMAGE)), None
                ).label('images'),
                func.array_remove(
                    func.array_agg(self.make_file_type_case(DBConst.VIDEO)), None
                ).label('videos'),
                func.array_remove(
                    func.array_agg(self.make_file_type_case(DBConst.AUDIO)), None
                ).label('audios'),
                func.array_remove(
                    func.array_agg(self.make_file_type_case(DBConst.DOC)), None
                ).label('docs'),
            )
            .join(FileReference, FileInfo.id == FileReference.file_id)
            .join(HomeworkAnswer, HomeworkAnswer.id == FileReference.referenced_id)
            .filter(
                FileReference.ref_type == DBConst.REF_BY_HOMEWORK_ANSWER,
                cond,
            )
            .group_by(HomeworkAnswer.id)
            .all()
        )

    @staticmethod
    def get_class_homework_answers(
        db: Session, homework_id: int, class_id: int, homework_expired: bool,
        page: int, page_size: int
    ) -> List[Row]:
        # 如果作业已截止，则判断 待提交 / 待重做 的作业为 未反馈
        if homework_expired:
            status_field_stmt = case(
                [(HomeworkAnswerStatus.status.in_(DBConst.EXPIRED_STATUS),
                  DBConst.NO_FEEDBACK)],
                else_=HomeworkAnswerStatus.status
            )
        else:
            status_field_stmt = HomeworkAnswerStatus
        return (
            db.query(
                HomeworkAnswerStatus.id.label('status_id'),
                HomeworkAnswerStatus.student_name,
                status_field_stmt,
                func.json_agg(
                    aggregate_order_by(
                        func.json_build_object(
                            'answer_id', HomeworkAnswer.id,
                            'desc', HomeworkAnswer.desc,
                            'reviewer', ClassMember.name,
                            'comment', HomeworkEvaluate.comment,
                            'score', HomeworkEvaluate.score,
                            'rejected', HomeworkEvaluate.rejected,
                        ),
                        HomeworkAnswer.create_time.desc()
                    )
                ).label('answers')
            )
            .select_from(HomeworkAnswerStatus)
            .join(HomeworkAnswer,
                  HomeworkAnswer.status_id == HomeworkAnswerStatus.id)
            .outerjoin(HomeworkEvaluate,
                       HomeworkEvaluate.id == HomeworkAnswer.evaluation_id)
            .outerjoin(ClassMember,
                       ClassMember.id == HomeworkEvaluate.reviewer_member_id)
            .filter(
                HomeworkAnswerStatus.homework_id == homework_id,
                HomeworkAnswerStatus.student_class_id == class_id,
            )
            .group_by(
                HomeworkAnswerStatus.id,
                HomeworkAnswerStatus.student_name,
                HomeworkAnswerStatus.status
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

    @staticmethod
    def count_rejected(
        db: Session, homework_id: int, class_id: int, student_names: Iterable[str]
    ) -> List[Row]:
        """
        根据 作业id、班级id、学生名单 查询各学生作答被打回的次数
        """
        return (
            db.query(HomeworkAnswerStatus.student_name,
                     func.count(HomeworkAnswer.id).label('rejected_times'))
            .join(HomeworkAnswer,
                  HomeworkAnswer.status_id == HomeworkAnswerStatus.id)
            .join(HomeworkEvaluate,
                  HomeworkEvaluate.id == HomeworkAnswer.evaluation_id)
            .filter(
                HomeworkAnswerStatus.homework_id == homework_id,
                HomeworkAnswerStatus.student_class_id == class_id,
                HomeworkAnswerStatus.student_name.in_(student_names),
                HomeworkAnswer.homework_id == homework_id,
                HomeworkEvaluate.rejected == true(),
            )
            .group_by(HomeworkAnswerStatus.student_name)
            .all()
        )

    @staticmethod
    def get_answer_status(
        db: Session, homework_id: int, user_id: int, class_id: int, answer_id: int
    ) -> Row:
        return (
            db.query(HomeworkAnswerStatus.id.label('status_id'),
                     HomeworkAnswerStatus.status,
                     HomeworkAnswerStatus.student_name)
            .join(Homework, Homework.id == HomeworkAnswer.homework_id)
            .join(HomeworkAnswerStatus,
                  HomeworkAnswerStatus.id == HomeworkAnswer.status_id)
            .filter(
                Homework.id == homework_id,
                Homework.publisher_id == user_id,
                Homework.is_delete == false(),
                HomeworkAnswer.id == answer_id,
                HomeworkAnswer.homework_id == homework_id,
                HomeworkAnswer.evaluation_id == null(),
                HomeworkAnswer.answer_check_id == null(),
                HomeworkAnswerStatus.homework_id == homework_id,
                HomeworkAnswerStatus.student_class_id == class_id,
            )
            .first()
        )

    @staticmethod
    def get_correction_times(db: Session, homework_id: int, student_name: str
                             ) -> int:
        """根据 作业id、学生姓名 查询该学生已经订正作业的次数"""
        return (
            db.query(func.count(HomeworkAnswer.id))
            .join(HomeworkAnswerStatus,
                  HomeworkAnswerStatus.id == HomeworkAnswer.status_id)
            .filter(
                HomeworkAnswer.homework_id == homework_id,
                HomeworkAnswer.category == DBConst.CORRECTION,
                HomeworkAnswerStatus.homework_id == homework_id,
                HomeworkAnswerStatus.student_name == student_name,
            )
            .scalar()
        )

    @staticmethod
    def get_existed_answers(
        db: Session, homework_id: int, user_id: int,
        class_id: int, answer_ids: Iterable[int],
    ) -> List[Row]:
        """根据 教师用户id、作业id、作答id列表 查询作答列表中合法的作答，
        返回作答情况id、学生姓名、作答情况
        """
        return (
            db.query(HomeworkAnswerStatus.id,
                     HomeworkAnswerStatus.student_name,
                     HomeworkAnswerStatus.status)
            .distinct()
            .select_from(HomeworkAnswer)
            .join(Homework, Homework.id == HomeworkAnswer.homework_id)
            .join(HomeworkAnswerStatus,
                  HomeworkAnswerStatus.id == HomeworkAnswer.status_id)
            .filter(
                Homework.id == homework_id,
                Homework.publisher_id == user_id,
                Homework.is_delete == false(),
                HomeworkAnswer.id.in_(answer_ids),
                HomeworkAnswer.homework_id == homework_id,
                HomeworkAnswer.evaluation_id == null(),
                HomeworkAnswer.answer_check_id == null(),
                HomeworkAnswerStatus.homework_id == homework_id,
                HomeworkAnswerStatus.student_class_id == class_id,
            )
            .all()
        )

    @staticmethod
    def update_evaluate(
        db: Session, answer_ids: Iterable[int], evaluation_id: int
    ) -> int:
        """更新作业作答关联的评论id"""
        res = (
            db.query(HomeworkAnswer)
            .filter(HomeworkAnswer.id.in_(answer_ids))
            .update({HomeworkAnswer.evaluation_id: evaluation_id})
        )
        return res

    @staticmethod
    def update_answer_check(
        db: Session, answer_id: int, answer_check_id: int
    ) -> int:
        """更新作业作答关联的批改id"""
        res = (
            db.query(HomeworkAnswer)
            .filter(HomeworkAnswer.id == answer_id)
            .update({HomeworkAnswer.answer_check_id: answer_check_id})
        )
        return res


class CRUDHomeworkAnswerStatus(
    CRUDBase[HomeworkAnswerStatus, HomeworkAnswerStatus, HomeworkAnswerStatus]
):
    """
    作业作答情况相关CRUD  模型类: HomeworkAnswerStatus  数据表: homework_answer_status
    """
    @staticmethod
    def update_answer_status_by_id(db: Session, answer_id: int, status: str) -> int:
        """
        根据 id 更新作业作答状态
        """
        res = (
            db.query(HomeworkAnswerStatus)
            .filter(HomeworkAnswerStatus.id == answer_id)
            .update({HomeworkAnswerStatus.status: status})
        )
        return res

    @staticmethod
    def get_stu_answer_status(
        db: Session, homework_id: int, class_id: int, student_name: str
    ) -> Row:
        """
        根据 作业id、学生班级、学生姓名 查询该学生在该作业的作答状态
        """
        return (
            db.query(HomeworkAnswerStatus.id.label('status_id'),
                     HomeworkAnswerStatus.status)
            .filter(
                HomeworkAnswerStatus.homework_id == homework_id,
                HomeworkAnswerStatus.student_name == student_name,
                HomeworkAnswerStatus.student_class_id == class_id,
            )
            .first()
        )

    @staticmethod
    def update_score_and_status_by_id(
        db: Session, status_id: Union[int, Iterable[int]],
        score: str, status: str,
    ) -> int:
        """
        更新作业评分
        """
        if isinstance(status_id, Iterable):
            cond = HomeworkAnswerStatus.id.in_(status_id)
        else:
            cond = HomeworkAnswerStatus.id == status_id
        res = (
            db.query(HomeworkAnswerStatus)
            .filter(cond)
            .update(
                {
                    HomeworkAnswerStatus.score: score,
                    HomeworkAnswerStatus.status: status,
                }
            )
        )
        return res

    @staticmethod
    def get_student_homework_list(
        db: Session, member_id: int, class_id: int, page: int, page_size: int
    ) -> List[Row]:
        """
        获取学生作业列表
        """
        teacher = aliased(ClassMember)
        return (
            db.query(func.count(Homework.id).over().label('total'), Homework.id,
                     Homework.pub_time, Homework.end_time, Homework.title,
                     Homework.desc, teacher.name.laber('publisher'))
            .join(
                HomeworkAnswerStatus, HomeworkAnswerStatus.homework_id == Homework.id
            )
            .join(ClassMember, HomeworkAnswerStatus.student_name == ClassMember.name)
            .join(
                teacher,
                and_(
                    teacher.user_id == Homework.publisher_id,
                    teacher.class_id == HomeworkAnswerStatus.student_class_id,
                )
            )
            .filter(
                ClassMember.id == member_id,
                HomeworkAnswerStatus.student_class_id == class_id,
                Homework.pub_time <= text('CURRENT_TIMESTAMP'),
                Homework.is_delete == false(),
                teacher.is_delete == false(),
            )
            .order_by(Homework.pub_time.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

    @staticmethod
    def get_teacher_homework_list(
        db: Session, user_id: int, class_id: int,
        subject_id: int, page: int, page_size: int
    ) -> List[Row]:
        """
        获取教师作业列表
        """
        case_stmt = case(
            [(HomeworkAnswerStatus.status == '1', text('1'))],
            else_=text('0')
        )
        sq = (
            db.query(
                Homework.id, Homework.pub_time, Homework.end_time,
                Homework.title, Homework.desc, Homework.publisher_id,
                func.round(
                    100 * func.sum(case_stmt) / func.count(HomeworkAnswerStatus.id),
                    0
                )
            )
            .distinct(Homework.id)
            .join(HomeworkAssign, HomeworkAssign.homework_id == Homework.id)
            .join(
                HomeworkAnswerStatus,
                HomeworkAnswerStatus.homework_id == Homework.id
            )
            .filter(
                HomeworkAssign.class_id == class_id,
                Homework.publisher_id == user_id if user_id else 1 == 1,
                Homework.subject_id == subject_id if subject_id else 1 == 1,
                Homework.pub_time <= text('CURRENT_TIMESTAMP'),
                Homework.is_delete == false(),
            )
            .group_by(Homework.id)
            .subquery()
        )
        return (
            db.query(sq, ClassMember.name)
            .join(
                ClassMember,
                and_(ClassMember.user_id == sq.c.publisher_id,
                     ClassMember.is_delete == false())
            )
            .filter(ClassMember.class_id == class_id)
            .order_by(sq.c.pub_time.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )


class CRUDHomeworkEvaluate(
    CRUDBase[HomeworkEvaluate, HomeworkEvaluate, HomeworkEvaluate]
):
    ...


class CRUDHomeworkAnswerCheck(
    CRUDBase[HomeworkAnswerCheck, HomeworkAnswerCheck, HomeworkAnswerCheck]
):
    ...


homework = CRUDHomework(Homework)
homework_assign = CRUDHomeworkAssign(HomeworkAssign)
homework_answer = CRUDHomeworkAnswer(HomeworkAnswer)
homework_answer_status = CRUDHomeworkAnswerStatus(HomeworkAnswerStatus)
homework_evaluate = CRUDHomeworkEvaluate(HomeworkEvaluate)
homework_answer_check = CRUDHomeworkAnswerCheck(HomeworkAnswerCheck)
