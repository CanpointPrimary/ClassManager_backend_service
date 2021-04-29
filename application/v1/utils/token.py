from functools import wraps
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature, BadData
from flask import request
from flask import jsonify
from flask import g

from models import Users
from config import Config
from v1.utils.code import Code


def generate_access_token(useId, identifyId, expires_in=120):
    """
    create business access_token
    :param useId:
    :param identifyId
    :param expires_in: expiration time is two hours
    :return:
    """

    access_it = Serializer(Config.SECRET_KEY, expires_in)
    access_payload = {
        'flag': 0,
        'user_id': useId,
        'identify_id': identifyId,
        'iat': 'qin'
    }
    access_token = access_it.dumps(access_payload).decode('utf-8')
    return access_token


def generate_refresh_token(useId, identifyId, expires_in=20160):
    """
    create refresh token
    :param useId:
    :param identifyId
    :param expires_in: expiration time two weeks
    :return:
    """
    refresh_it = Serializer(Config.SECRET_KEY, expires_in)
    refresh_payload = {
        'user_id': useId,
        'identify_id': identifyId,
        'flag': 1,
        'iat': 'qin'
    }
    refresh_token = refresh_it.dumps(refresh_payload).decode('utf-8')
    return refresh_token


def access_loads_token(token, expires_in=120):
    """
    decrypt token
    :param token:
    :param expires_in:
    :return:
    """
    access_it = Serializer(Config.SECRET_KEY, expires_in)
    try:
        payload = access_it.loads(token.encode('utf-8'))
    except SignatureExpired:
        return jsonify({'msg': 'token expired'})
    except BadSignature:
        return jsonify({' msg': 'failure'})
    return payload


def refresh_loads_token(token, expires_in=20160):
    """
    decrypt refresh token
    :param token:
    :param expires_in:
    :return:
    """
    refresh_it = Serializer(Config.SECRET_KEY, expires_in)
    try:
        payload = refresh_it.loads(token.encode('utf-8'))
    except SignatureExpired:
        return jsonify({'msg': 'token expired'})
    except BadSignature:
        return jsonify({' msg': 'failure'})
    return payload


def identify(token):
    """
    determine the identity of the token
    :param token:
    :return:
    """
    payload = access_loads_token(token)
    print(payload)
    if not payload:
        return False
    if 'flag' in payload:
        if payload['flag'] == 1:
            return False
        elif payload['flag'] == 0:
            useId = payload['user_id']
            identifyId = payload['identify_id']
            return useId, identifyId
    else:
        return False


def login_required(func):
    """
    login protection
    :param func:
    :return:
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('access_token', default=None)
        if not token:
            return jsonify({'code': Code.NOT_FOUND, 'msg': 'please sign in'})
        useId, identifyId = identify(token)
        if not useId:
            return jsonify({'code': Code.NOT_FOUND, 'msg': 'please sign in'})
        user = Users.query.filter_by(openId=useId).first()
        if not user and not identifyId:
            return jsonify({'code': Code.NOT_FOUND, 'msg': 'please sign in'})
        g.user = user
        return func(*args, **kwargs)
    return wrapper