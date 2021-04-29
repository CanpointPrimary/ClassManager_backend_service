from flask_restful import fields

login_fields = {
        'session': fields.String,
    }


register_fields = {
        'useId': fields.Integer,
        'username': fields.String,
        'nickname': fields.String,
        'mobile': fields.String,
        'sex': fields.Integer,
        'identifyId': fields.Integer,
        'avatar': fields.String,
        'age': fields.String,
        'isActive': fields.Boolean
    }

register_teacher_fields = {
        'teaId': fields.Integer,
        'username': fields.String,
        'nickname': fields.String,
        'mobile': fields.String,
        'sex': fields.Integer,
        'identifyId': fields.Integer,
        'avatar': fields.String,
        'age': fields.String,
        'isActive': fields.Boolean,
        'isHeadTeacher': fields.Boolean,
        'status': fields.Boolean
}

register_student_fields = {
        'stuId': fields.Integer,
        'username': fields.String,
        'nickname': fields.String,
        'mobile': fields.String,
        'sex': fields.Integer,
        'identifyId': fields.Integer,
        'avatar': fields.String,
        'age': fields.String,
        'isActive': fields.Boolean,
        'status': fields.Boolean,
}



