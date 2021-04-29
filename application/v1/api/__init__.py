from flask import Blueprint
from flask_restful import Api

from v1.api.users import RegisterUsersResource
from v1.api.users import LoginUserResource
from v1.api.refresh_token import RefreshTokenResource
from v1.api.teacher import TeachersResource
from v1.api.teacher import HeadTeacherResource
from v1.api.teacher import OrdinaryTeacherResource
from v1.api.student import StudentsResource
from v1.api.student import StudentCenterResource
from v1.api.classes import AddStudentClass
from v1.api.classes import AddTeacherClass
from v1.api.classes import ClassMemberResource
from v1.api.operations import TeacherReleaseWorksResource

# create blueprint
api = Blueprint('', __name__)

# create views
user_api = Api(api, '/users')
user_api.add_resource(RegisterUsersResource, '/register')
user_api.add_resource(LoginUserResource, '/login')
user_api.add_resource(RefreshTokenResource, '/token')

teacher_api = Api(api, '/teachers')
teacher_api.add_resource(TeachersResource, '/teacher')
teacher_api.add_resource(HeadTeacherResource, '/headteacher', endpoint='head')
teacher_api.add_resource(OrdinaryTeacherResource, '/ordteacher', endpoint='ord')

student_api = Api(api, '/students')
student_api.add_resource(StudentsResource, '/student')
student_api.add_resource(StudentCenterResource, '/student_center/<stuId>')

class_api = Api(api, '/classes')
class_api.add_resource(AddStudentClass, '/student')
class_api.add_resource(AddTeacherClass, '/teacher')
class_api.add_resource(ClassMemberResource, '/member/<classId>')

opera_api = Api(api, '/operations')
opera_api.add_resource(TeacherReleaseWorksResource, '/release/<teaId>')
