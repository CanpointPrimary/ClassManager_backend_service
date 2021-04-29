from flask_restful import fields

student_fields = {
        'username': fields.String,
        'nickname': fields.String,
        'mobile': fields.String,
        'classname': fields.String,
        'relatives': fields.Integer
}