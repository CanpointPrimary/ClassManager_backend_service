#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date: 2021/7/13
# @Author: gray

"""
内部相关业务逻辑
"""

import json
import requests
import time
from hashlib import md5
from loguru import logger
from typing import Dict, List, Tuple

from sqlalchemy.engine import Row
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.constants import DBConst
from app.core.config import settings
from app.crud import region, sys_config
from app.models import School
from app.schemas.sync_school import SyncSchoolRespContent, SyncSchool


DISABLED_SCHOOL = 0  # 已停用，软删除标识


class APIGateway(object):
    """
    通过API网关调用其他接口
    """

    @staticmethod
    def list_school(
        page_size: int = settings.SYNC_SCHOOL_PAGE_SIZE,
        curr_page: int = 1
    ) -> requests.Response:
        """
        调用一次API网关 列出学校信息 接口，获取一页学校信息，返回响应对象

        Parameters
        ----------
        page_size : 单次请求时，数据分页的一页的数据量
        curr_page : 单次请求时，数据分页的页码
        """
        # signature=md5(apiId+accessKeyID+accessKeySecret+appKey+appSecret+timestamp)
        timestamp = str(int(time.time()))
        origin = (
                settings.SYNC_SCHOOL_API_ID + settings.API_GW_ACCESS_KEY_ID
                + settings.API_GW_ACCESS_KEY_SECRET + settings.API_GW_APP_KEY
                + settings.API_GW_APP_SECRET + timestamp
        )
        signature = md5(origin.encode('utf8')).hexdigest()
        headers = {
            'apiId': settings.SYNC_SCHOOL_API_ID,
            'accessKeyID': settings.API_GW_ACCESS_KEY_ID,
            'timestamp': timestamp,
            'signature': signature,
            'appKey': settings.API_GW_APP_KEY,
        }
        params = {
            'pageSize': page_size,
            'currPage': curr_page,
        }
        return requests.get(settings.SYNC_SCHOOL_URL, headers=headers, params=params)  # noqa

    @classmethod
    def sync_school_data(cls, db: Session) -> None:
        """
        通过API网关接口同步学校数据并更新到数据库
        """
        # 查询 全国地区、学段 相关的系统配置
        sys_area = region.get_area_tree(db)
        sys_stage = sys_config.get_config_by_type(db, DBConst.SCHOOL_STUDY_STAGE)  # noqa
        sys_stage = {x.value: x.key for x in sys_stage}
        # {'小学': '1', '初中': '2', '高中': '3'}

        # 调用接口，获取 总页数 和 第一页学校数据
        resp = cls.list_school()
        total_page, school_list = cls.preprocess_resp(resp, sys_area, sys_stage)
        # 第一页学校数据 更新到数据库
        cls.update_school_data(db, school_list)
        if total_page < 2:
            return
        # 从第二页开始获取学校数据并更新到数据库
        for page_no in range(2, total_page + 1):
            resp = cls.list_school(curr_page=page_no)
            _, school_list = cls.preprocess_resp(resp, sys_area, sys_stage)
            cls.update_school_data(db, school_list)

    @staticmethod
    def preprocess_resp(
        resp: requests.Response, sys_area: List[Row], sys_stage: Dict[str, str]
    ) -> Tuple[int, List[Dict]]:
        """
        预处理 API网关接口返回的响应数据
        匹配 所属地区、学段 信息
        """
        # 结构化响应数据
        resp_content = json.loads(resp.text)
        content = SyncSchoolRespContent(**resp_content)
        total_page: int = content.data.totalPage
        school_list: List[SyncSchool] = content.data.list

        # 匹配学校的 所属地区、学段
        invalid_list: List[SyncSchool] = []  # 无法识别的学校
        valid_list: List[dict] = []          # 已识别待更新到数据库的学校
        for school in school_list:
            if school.status == DISABLED_SCHOOL:
                continue
            match_area = [x for x in sys_area if x.name == school.areaName]
            if len(match_area) > 1:
                match_area = [
                    x for x in match_area
                    if x.name == school.areaName
                    and x.parent_name == school.cityName
                ]
            if len(match_area) != 1:
                invalid_list.append(school)
                continue
            region_code = match_area[0].code

            stages = []
            stage_list = school.periodName.split(',')
            for stage in stage_list:
                stage_key = sys_stage.get(stage)
                if not stage_key:
                    invalid_list.append(school)
                    continue
                stages.append(stage_key)
            study_stage = ','.join(stages)

            valid_list.append(
                {
                    'name': school.schoolName,
                    'region_code': region_code,
                    'address': school.address,
                    'study_stage': study_stage,
                    'school_id': school.schoolId,
                    'parent_org_id': school.parentOrgId,
                    'curr_cpscode': school.currCpscode,
                    'data_source': DBConst.SYNC_FROM_API,
                }
            )
        # 无法识别的学校数据记录日志
        if invalid_list:
            logger.error(f'Unrecognized school data in synchronization: '
                         f'{invalid_list}\nraw API message: {resp.text}')
        return total_page, valid_list

    @staticmethod
    def update_school_data(
        db: Session, school_list: List[dict]
    ) -> None:
        """
        更新学校数据到数据库
        该部分数据来源于 API网关同步，school_id 是学校数据在数据源端的唯一标识
        school_id 字段有唯一索引
        如果 school_id 已存在则更新该条记录的数据，如不存在则插入新记录
        """
        batch_upsert = insert(School).values(school_list)
        batch_upsert = batch_upsert.on_conflict_do_update(
            index_elements=[School.school_id],
            set_={
                'name': batch_upsert.excluded.name,
                'region_code': batch_upsert.excluded.region_code,
                'address': batch_upsert.excluded.address,
                'study_stage': batch_upsert.excluded.study_stage,
                'parent_org_id': batch_upsert.excluded.parent_org_id,
                'curr_cpscode': batch_upsert.excluded.curr_cpscode,
                'data_source': batch_upsert.excluded.data_source,
                'update_time': text('CURRENT_TIMESTAMP'),
            }
        )
        db.execute(batch_upsert)
        db.commit()


if __name__ == '__main__':
    from app.db.session import SessionLocal

    session = SessionLocal()
    APIGateway.sync_school_data(session)
