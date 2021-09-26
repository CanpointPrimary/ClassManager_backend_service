import math
from typing import Dict, Generator, List, Tuple

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from pydantic import ValidationError
from redis import Redis
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import Session

from app import crud, schemas
from app.constants import DBConst, RespError
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.redis import redis
from app.exceptions import BizHTTPException


reusable_oauth2 = HTTPBearer(auto_error=False)


def get_request_id(request: Request) -> str:
    """
    从请求中获取 request_id
    """
    return request.state.request_id


def get_db() -> Generator:
    """
    获取数据库连接
    """
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close() if db else ...


def get_redis() -> Redis:
    """
    获取Redis连接
    """
    return redis


def get_token(
    credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
) -> schemas.TokenPayload:
    """
    校验Token，校验用户是否存在数据库中，返回Token payload
    """
    if not credentials:
        raise BizHTTPException(*RespError.FORBIDDEN)
    try:
        payload = jwt.decode(
            credentials.credentials, settings.SECRET_KEY,
            algorithms=[security.ALGORITHM], audience='ClassManager'
        )
        token = schemas.TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise BizHTTPException(*RespError.TOKEN_EXPIRED)
    except (jwt.JWTError, ValidationError):
        raise BizHTTPException(*RespError.INVALID_TOKEN)
    return token


def get_activated(
    db: Session = Depends(get_db),
    token: schemas.TokenPayload = Depends(get_token),
) -> schemas.TokenPayload:
    """
    校验用户是否停用，返回Token payload
    """
    user = crud.user.get_basic_info(db, user_id=token.sub)
    if not user:
        raise BizHTTPException(*RespError.USER_NOT_FOUND)
    if user.is_delete:
        raise BizHTTPException(*RespError.USER_DISABLED)
    token.member_id = user.current_member_id
    return token


def get_class_member(
    db: Session = Depends(get_db),
    token: schemas.TokenPayload = Depends(get_activated),
) -> schemas.TokenPayload:
    """
    校验用户当前班级成员身份是否有效，返回Token payload
    """
    cur_member = crud.class_member.get_member_role(db, token.member_id)
    # 若查无此班级成员则返回 权限不足
    if not cur_member:
        raise BizHTTPException(*RespError.AUTHORIZATION_DENIED)
    # 若此班级成员已被删除则返回 当前班级成员身份已失效
    if cur_member.is_delete:
        raise BizHTTPException(*RespError.DISABLED_CLASS_MEMBERSHIP)
    token.member_role = cur_member.member_role
    token.class_id = cur_member.class_id
    return token


def get_teacher(
    token: schemas.TokenPayload = Depends(get_class_member),
) -> schemas.TokenPayload:
    """
    校验用户当前在班身份是否教师
    """
    # 若班级成员身份不为教师则返回 权限不足
    if token.member_role not in (DBConst.HEADTEACHER, DBConst.TEACHER):
        raise BizHTTPException(*RespError.AUTHORIZATION_DENIED)
    return token


def get_headteacher(
    token: schemas.TokenPayload = Depends(get_class_member),
) -> schemas.TokenPayload:
    """
    校验用户当前在班身份是否班主任
    """
    # 若班级成员身份不为班主任则返回 权限不足
    if token.member_role != DBConst.HEADTEACHER:
        raise BizHTTPException(*RespError.AUTHORIZATION_DENIED)
    return token


def handle_paging_data(
    result_list: List[Tuple[Row, int]], page: int, page_size: int
) -> Dict:
    """
    处理数据库分页数据
    """
    data_list = [x[0] for x in result_list]
    total = result_list[0][1] if result_list else 0
    total_page = math.ceil(total / page_size)
    return {'list': data_list, 'total': total, 'page': page,
            'page_size': page_size, 'total_page': total_page}
