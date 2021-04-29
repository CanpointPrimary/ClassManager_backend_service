from flask_restful import Resource
from flask_restful import marshal
from flask import make_response, session
from flask import jsonify

from models import Classes
from models import Teachers
from models import Subjects
from models import Students
from v1.common.parser.student_parser import student_parser
from v1.common.fields.class_fields import class_fields
from v1.common.parser.teacher_parse import teacher_parser
from v1.common.fields.teacher_fields import teacher_head_fields
from v1.common.fields.teacher_fields import teacher_ord_fields
from v1.common.fields.student_fields import student_fields
from v1.utils.code import Code
from v1.utils.token import login_required


class AddTeacherClass(Resource):
    @login_required
    def put(self):
        """
        ordinary　teacher add class
        :return:
        """
        args = teacher_parser.parse_args()
        username = args.get('username')
        mobile = args.get('mobile')
        subject = args.get('subject')
        classId = args.get('classId')
        isHasClass = args.get('isHasClass')
        teacher = Teachers.query.filter_by(username=username, mobile=mobile).first()
        subject = Subjects.query.filter_by(subjectId=subject).first()
        classes = Classes.query.filter_by(classId=classId).first()
        if not teacher:
            return jsonify({'code': Code.NOT_FOUND, 'msg': 'please register'})
        if not subject:
            return jsonify({'code': Code.NOT_FOUND, 'msg': 'Please choose the correct course'})
        if not classId:
            return jsonify({'code': Code.NOT_FOUND, 'msg': 'Please fill in the correct class code'})
        classes.teachers.append(teacher)
        teacher.subjects.append(subject)
        teacher.isHasClass = isHasClass
        try:
            teacher.update()
        except Exception as e:
            return e
        if teacher.isHeadTeacher:
            data = {
                'code': Code.OK,
                'msg': 'join the class successfully',
                'teacher': marshal(teacher, teacher_head_fields)
            }
        else:
            data = {
                'code': Code.OK,
                'msg': 'join the class successfully',
                'teacher': marshal(teacher, teacher_ord_fields)
            }
        response = make_response(jsonify(data))
        return response


class AddStudentClass(Resource):
    @login_required
    def put(self):
        """
        student add class
        :return:
        """
        args = student_parser()
        username = args.get('username')
        mobile = args.get('mobile')
        classId = args.get('classId')
        relatives = args.get('relatives')
        isHasClass = args.get('isHasClass')
        student = Students.query.filter_by(username=username, mobile=mobile).first()
        classes = Classes.query.filter_by(classId=classId).first()
        if not student:
            return jsonify({'code': Code.NOT_FOUND, 'msg': 'please register'})
        if not classes:
            return jsonify({'code': Code.NOT_FOUND, 'msg': 'The entered class code is incorrect'})
        classes.students.append(student)
        student.relatives = relatives
        student.isHasClass = isHasClass
        try:
            student.update()
        except Exception as e:
            return e
        data = {
            'code': Code.OK,
            'msg': 'join the class successfully',
            'student': marshal(student, student_fields)
        }
        response = make_response(jsonify(data))
        return response


class ClassMemberResource(Resource):

    def get(self, classId):
        """
        get class members
        :param classId:
        :return:
        """
        classes = Classes.query.filter_by(classId=classId).first()

        data = {
            'code': Code.OK,
            'msg': 'success',
            'classes': marshal(classes, class_fields)
        }
        response = make_response(jsonify(data))
        return response

