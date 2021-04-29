from flask import request
from flask import jsonify
from flask_restful import Resource

from v1.utils.token import refresh_loads_token
from v1.utils.token import generate_access_token
from v1.utils.code import Code


class RefreshTokenResource(Resource):
    """
    Refresh the token and get a new business token
    """
    def get(self):
        refresh_token = request.args.get('refresh_token')
        if not refresh_token:
            return jsonify({'code': Code.NOT_FOUND, 'msg': 'please sign in'})
        payload = refresh_loads_token(refresh_token)
        if not payload:
            return jsonify({'code': Code.NOT_FOUND, 'msg': 'please sign in'})
        if 'open_id' not in payload:
            return jsonify({'code': Code.NOT_FOUND, 'msg': 'please sign in'})
        access_token = generate_access_token(openId=payload['open_id'], identifyId=payload['identify_id'])
        data = {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
        return jsonify(data)