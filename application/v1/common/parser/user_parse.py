from flask_restful import inputs
from flask_restful.reqparse import RequestParser

login_parser = RequestParser()
login_parser.add_argument('js_code', type=str, required=True)


register_parser = RequestParser()
register_parser.add_argument('username', type=str, required=True, help='please fill in your real name')
register_parser.add_argument('nickname', type=str, help='')
register_parser.add_argument('openId', type=str, help='测试需要，正式不需要')
register_parser.add_argument('mobile', type=inputs.regex(r'^1[3-9]\d{9}$'), required=True,
                             help='please fill in the real phone number')
register_parser.add_argument('sex', choices=[0, 1], type=int, required=True)
register_parser.add_argument('age', type=int, required=False)
register_parser.add_argument('avatar', type=str)
register_parser.add_argument('identifyId', choices=[0, 1, 2], type=int, required=True)
register_parser.add_argument('isActive', type=bool)


register_teacher = register_parser.copy()
register_teacher.add_argument('isHeadTeacher', type=bool)

register_student = register_parser.copy()

