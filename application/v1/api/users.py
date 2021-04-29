from flask_restful import Resource, marshal_with
from flask_restful import marshal
from flask import session
from flask import jsonify

from models import Users
from v1.utils.wechatSDK.wechat import WXSDK_jscode2session
from v1.utils.token import generate_access_token
from v1.utils.token import generate_refresh_token
from v1.utils.code import Code
from v1.common.fields.user_fields import login_fields
from v1.common.fields.user_fields import register_fields
from v1.common.parser.user_parse import login_parser
from v1.common.parser.user_parse import register_parser


class LoginUserResource(Resource):
    """
    Realize the login of ordinary users such as tourists. If you want to further operate and join the class,
    you must obtain the access token through registration
    """

    def post(self):
        log_args = login_parser.parse_args()
        resp = WXSDK_jscode2session(log_args['js_code'])

        if isinstance(resp, dict):
            openid = resp.get('openid')
            user = Users.get(openid)
            if not user:
                user.openId = openid
                user.add(user)
            # Update the openID in the cache
            session.update({'openid': openid})
            data = {
                'code': Code.CREATE_SUCCESS,
                'msg': 'login success',
                'user': marshal(user, login_fields)
            }
            return jsonify(data)


class RegisterUsersResource(Resource):
    """
    If the user wants to continue other operations (except tourists),
    then according to the logged-in openID,
    find out the corresponding user or corresponding student, and complete the registration.
    If you have already registered, you don’t need to
    """

    def post(self):

        """
        Verify the existence of openID, and then complete the registration
        :return: access_token, refresh_token
        """
        args = register_parser.parse_args()
        openid = session.get("openid")
        if openid is None:
            return jsonify({'code': Code.NOT_FOUND, 'msg': 'please login again'})
        user = Users()
        user.username = args.get('username')
        user.nickname = args.get('nickname')
        user.openId = args.get('openId')
        user.mobile = args.get('mobile')
        user.sex = args.get('sex')
        user.age = args.get('age')
        user.avatar = args.get('avatar')
        user.identifyId = args.get('identifyId')
        user.isActive = args.get('isActive')
        try:
            user.add()
        except Exception as e:
            return e
        access_token = generate_access_token(useId=user.useId, identifyId=user.identifyId)
        refresh_token = generate_refresh_token(useId=user.useId, identifyId=user.identifyId)

        data = {
            'code': Code.CREATE_SUCCESS,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': marshal(user, register_fields)
        }

        return jsonify(data)


