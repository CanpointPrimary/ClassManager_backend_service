from flask_restful import inputs
from flask_restful.reqparse import RequestParser

teacher_parser = RequestParser()
teacher_parser.add_argument('username', type=str, required=True, help='Please fill in your real name')
teacher_parser.add_argument('mobile', type=inputs.regex(r'^1[3-9]\d{9}$'), required=True,
                            help='Please fill in the real phone number')
teacher_parser.add_argument('subject', type=int, help='Please choose the correct course')
teacher_parser.add_argument('classId', type=int, help='Please fill in the correct class code')
teacher_parser.add_argument('isHasClass', type=bool)