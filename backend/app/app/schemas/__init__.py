"""
Schema - 结构体模型类 / 实体类
"""

from .class_member import ClassMember
from .external_api_msg import Code2SessionMsg, WXUrlLinkMsg, WXAccessTokenMsg
from .homework import HomeworkAssignScope, SchoolHomework, SchoolHomeworkAnswer, \
    SchoolHomeworkAssign, SchoolHomeworkAttachment
from .internal_type import Str, Str10, StrLeast10
from .internal_api_msg import SyncSchoolRespContent, SyncSchool
from .response import Response
from .token import Token, TokenPayload
