from flask import jsonify, session
from flask import g
from flask import make_response
from flask_restful import Resource
from flask_restful import marshal

from v1.utils.code import Code
from v1.utils.token import login_required
from v1.common.parser.user_parse import register_student
from v1.common.parser.student_parser import modify_student_parser
from v1.common.fields.student_fields import student_fields
from models import Students


class StudentsResource(Resource):
    @login_required
    def post(self):
        """
        register student
        :return:
        """
        student = Students()
        args = register_student.parse_args()
        student.username = args.get('username')
        student.nickname = args.get('nickname')
        student.sex = args.get('sex')
        student.mobile = args.get('mobile')
        student.age = args.get('age')
        student.identifyId = g.user.identifyId
        student.isActive = g.user.isActive
        student.avatar = g.user.avatar
        student.status = True
        try:
            student.add()
        except Exception as e:
            return e
        data = {
            'code': Code.CREATE_SUCCESS,
            'msg': 'success',
            'student': marshal(student, register_student)
        }
        response = make_response(jsonify(data))
        return response


class StudentCenterResource(Resource):
    """
    student center
    """
    @login_required
    def get(self, stuId):
        """
        Get basic student information
        :param stuId:
        :return:
        """
        student = Students.query.filter_by(stuId=stuId).first()
        data = {
            'code': Code.OK,
            'msg': 'success',
            'student': marshal(student, student_fields)
        }
        response = make_response(jsonify(data))
        return response

    @login_required
    def put(self, stuId):
        """
        modify basic student information
        :param stuId:
        :return:
        """
        student = Students.query.filter_by(stuId=stuId).first()
        args = modify_student_parser.parse_args()
        student.username = args.get('username')
        try:
            student.update()
        except Exception as e:
            return e
        data = {
            'code': Code.CREATE_SUCCESS,
            'msg': 'success',
            'student': marshal(student, student_fields)
        }
        response = make_response(jsonify(data))
        return response

    @login_required
    def delete(self, stuId):
        """
        logout
        :param stuId:
        :return:
        """
        session.pop(stuId)
        return jsonify({'code': Code.OK})
