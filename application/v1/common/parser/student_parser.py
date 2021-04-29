from flask_restful.reqparse import RequestParser

student_parser = RequestParser()
student_parser.add_argument('username', type=str, required=True, help='Please fill in your real name')
student_parser.add_argument('mobile', type=str, required=True, help='Please fill in the real phone number')
student_parser.add_argument('classId', type=int, required=True, help='Please fill in the correct class number')
student_parser.add_argument('relatives', type=str, required=True, help='please fill in your kinship')
student_parser.add_argument('isHasClass', type=bool)

modify_student_parser = RequestParser()
modify_student_parser.add_argument('username', type=str, required=True, help='please fill in your real name')