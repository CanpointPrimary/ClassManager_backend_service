from flask_restful import fields

subjects_fields = {
        'subjectName': fields.String
}

class_fields = {
        'className': fields.String
}

teacher_member_fields = {
        'username': fields.String,
        'subject': fields.Nested(subjects_fields)
}
student_member_fields = {
        'username': fields.String,
        'relatives': fields.Integer
}
class_member_fields = {
        'className': fields.String,
        'teachers': fields.Nested(teacher_member_fields),
        'students': fields.Nested(student_member_fields)
}