#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# Date: 2021/7/27
# Author: gray

from app.constants.base import Const


class Response(object):
    """
    错误响应类
    该类的实例是不可变对象
    支持 星号解包 的方式传递实例变量

    Example:
        from app.exceptions import BizHTTPException

        response = Response(status_code=404, detail='Not found', desc='找不到资源')
        raise BizHTTPException(*response)
    """
    def __init__(self, status_code: int, statement: str, message: str) -> None:
        super().__setattr__('status_code', status_code)
        super().__setattr__('statement', statement)
        super().__setattr__('message', message)

    def __setattr__(self, key, value):
        raise TypeError(f'object is immutable')

    def __iter__(self):
        return iter(self.__dict__.values())


class RespError(Const):
    """
    错误响应相关常量或枚举值
    """
    SERVER_TOO_BUSY = Response(500, 'Server is too busy', '系统繁忙')
    INVALID_CODE = Response(400, 'Invalid code', '无效的code')
    USED_CODE = Response(403, 'Used code', '已使用过的code')
    USER_REQUESTS_TOO_FREQUENTLY = Response(
        403, 'User requests too frequently', '用户请求过于频繁'
    )
    HIGH_RISK_USER = Response(403, 'High-risk users', '高风险等级用户')
    AUTHENTICATE_FAILED = Response(
        500, 'Failed to authenticate user', '用户身份验证失败'
    )
    INTERNAL_SERVER_ERROR = Response(500, 'Internal server error', '服务器内部错误')

    INVALID_TOKEN = Response(403, 'Invalid token', '无效的Token')
    TOKEN_EXPIRED = Response(401, 'Token expired', '已过期的Token')
    USER_DISABLED = Response(403, 'User disabled', '用户已停用')
    USER_NOT_FOUND = Response(404, 'User not found', '找不到用户')

    INVALID_PARAMETER = Response(400, 'Invalid parameter', '无效的请求参数')
    MISSING_PARAMETER = Response(400, 'Missing parameter', '缺失必要参数')

    FORBIDDEN = Response(403, 'Not authenticated', '禁止访问')

    DUPLICATE_MEMBER = Response(400, 'User already in class', '用户已在班')
    DUPLICATE_TEACHER = Response(400, 'Teacher already in class', '已是{}老师')
    DUPLICATE_APPLY = Response(400, 'Duplicate apply for class', '重复提交的申请')
    TEACHER_EXISTS = Response(
        400, 'Subject teacher already in class', '{}任课老师已在班'
    )
    TOO_MANY_APPLY = Response(
        400, 'Too many apply in class', '同一班级申请数量超过上限'
    )
    INCORRECT_CAPTCHA = Response(400, 'Incorrect captcha', '验证码错误')
    AUTHORIZATION_DENIED = Response(403, 'Authorization denied', '权限不足')
    INVALID_INVITATION = Response(400, 'Invalid invitation info', '无效的邀请信息')
    GEN_WXACODE_FAILED = Response(500, 'Generate wxacode failed', '小程序码生成失败')
    GEN_WX_URL_LINK_FAILED = Response(
        500, 'Generate wx url link failed', '小程序链接生成失败'
    )
    FILE_NUMBER_OUT_OF_LIMIT = Response(
        400, 'Number of upload files out of limit', '上传文件数量超出限制'
    )
    FILESIZE_OUT_OF_LIMIT = Response(
        413, 'Size of upload file out of limit', '上传文件大小超出限制'
    )
    INVALID_UPLOADED_FILETYPE = Response(
        400, 'Invalid uploaded file type', '上传文件类型非法'
    )
    UPLOADED_FILE_NOT_FOUND = Response(400, 'Upload file not found', '未找到上传文件')
    INVALID_CLASS_CODE = Response(400, 'Class not exists', '无效的班级码')
    INVALID_SUBJECT = Response(400, 'Subject not exists', '无效的学科')
    INVALID_CLASS_APPLY = Response(400, 'Invalid class apply', '无效的入班申请')
    INVALID_FAMILY_RELATION = Response(
        400, 'Invalid family relation', '无效的亲属关系'
    )
    HEADTEACHER_DELETE = Response(
        400, 'Headteacher can not delete him/her self', '班主任不能从班级中删除自己'
    )
    DEPRECATED_API = Response(403, 'API deprecated', '废弃的接口')
    DISABLED_CLASS_MEMBERSHIP = Response(
        403, 'Disabled class membership', '当前班级成员身份已失效'
    )
    CLASS_MEMBER_NOT_FOUND = Response(
        400, 'Class member not found', '找不到班级成员信息'
    )
    REVIEWED_APPLY = Response(400, 'Apply has been reviewed', '该申请已被审核')
    GROUP_EXISTS = Response(400, 'Group already exists', '班级小组已存在')
    GROUP_NOT_FOUND = Response(400, 'Group not found', '不存在的班级小组')
