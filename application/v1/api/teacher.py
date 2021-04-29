from flask import g
from flask import jsonify
from flask import make_response
from flask_restful import Resource
from flask_restful import marshal

from v1.utils.token import login_required
from v1.utils.code import Code
from models import Teachers
from v1.common.parser.user_parse import register_teacher
from v1.common.fields.user_fields import register_teacher_fields


class TeachersResource(Resource):
    """
    teacher joins the class
    """
    @login_required
    def post(self):
        teacher = Teachers()
        args = register_teacher.parse_args()
        teacher.username = args.get('username')
        teacher.nickname = args.get('nickname')
        teacher.sex = args.get('sex')
        teacher.mobile = args.get('mobile')
        teacher.age = args.get('age')
        teacher.avatar = args.get('avatar')
        teacher.isHeadTeacher = args.get('isHeadTeacher')
        teacher.identifyId = g.user.identifyId
        teacher.isActive = g.user.isActive
        teacher.status = True
        try:
            teacher.add()
        except Exception as e:
            return e
        data = {
            'code': Code.CREATE_SUCCESS,
            'msg': 'success',
            'teacher': marshal(teacher, register_teacher_fields)
        }
        response = make_response(jsonify(data))
        return response


class HeadTeacherResource(Resource):
    """
    headerTeacher
    """
    @login_required
    def put(self):
        pass


class OrdinaryTeacherResource(Resource):
    """
    ordinary teacher
    """
    @login_required
    def get(self):
        pass