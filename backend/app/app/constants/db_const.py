#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date: 2021/7/15
# @Author: gray

from app.constants.base import Const


class DBConst(Const):
    """
    数据库相关常量或枚举值
    """

    # ------------ 系统配置表 sys_config 相关 ------------
    SCHOOL_STUDY_STAGE = '1'  # 配置类型为该值的配置项，为 学校学段 配置
    FAMILY_RELATION = '2'     # 配置类型为该值的配置项，为 亲属关系 配置

    # -------------- 学校信息表 school 相关 --------------
    SYNC_FROM_API = '1'  # 标识学校数据来源于 API网关同步

    # -------------- 全国地区表 region 相关 --------------
    PROVINCE = '1'  # 省级行政区
    CITY = '2'      # 地级行政区
    AREA = '3'      # 县级行政区

    # ----- 页面图片 entrance_page homepage_menu 相关 ----
    PIC_ACTIVATED = '1'    # 图片已启用
    PIC_INACTIVATED = '0'  # 图片已停用
    STARTUP = '1'   # 启动页图片
    GUIDANCE = '2'  # 引导页图片

    # ----------- 班级成员表 class_member 相关 -----------
    HEADTEACHER = '1'  # 班级成员身份: 班主任
    TEACHER = '2'      # 班级成员身份: 任课老师
    STUDENT = '3'      # 班级成员身份: 学生

    REJECT = '0'     # 驳回
    REVIEWING = '1'  # 审核中
    PASS = '2'       # 通过

    # -------------- 用户反馈 feedback 相关 --------------
    PRODUCT_SUGGESTION = '0'  # 产品建议
