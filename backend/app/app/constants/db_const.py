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
    PRODUCT_SUGGESTION = '1'  # 产品建议

    # ------------- 文件信息 file_info 相关 --------------
    IMAGE = '1'  # 图像
    VIDEO = '2'  # 视频
    AUDIO = '3'  # 音频
    DOC = '4'    # 文档

    # ----------- 文件引用 file_reference 相关 -----------
    REF_BY_USER_FEEDBACK = '1'    # 用户反馈
    REF_BY_HOMEWORK = '2'         # 作业
    REF_BY_HOMEWORK_ANSWER = '3'  # 作业作答

    # ---------------- 消息 message 相关 ----------------
    SCHOOL_HOMEWORK_HINT = '1'     # 校本作业提示
    SCHOOL_HOMEWORK_COMMENT = '2'  # 校本作业评论

    # ----------- 作业发布 homework_assign 相关 ----------
    ASSIGNED4WHOLE_CLASS = '0'  # 作业发布给全班所有人

    # ------------- 作业 homework_answer 相关 ------------
    ANSWER = '1'      # 作答
    REWORKING = '2'   # 重做
    CORRECTION = '3'  # 订正

    # ---------- 作业 homework_answer_status 相关 --------
    NEED2SUBMIT = '1'  # 待提交
    SUBMITTED = '2'    # 已提交
    NEED2REWORK = '3'  # 待重做 / 已打回
    CHECKED = '4'      # 已批改
    CORRECTED = '5'    # 已订正
    NO_FEEDBACK = '6'  # 未反馈

    EXPIRED_STATUS = {NEED2SUBMIT, NEED2REWORK}

    # --------- 作业发布 homework_answer_check 相关 -------
    IMAGE_MARK = '1'  # 大图批改
