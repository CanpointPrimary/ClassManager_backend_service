from flask_restful import fields

from common.fields.class_fields import subjects_fields
from common.fields.class_fields import class_fields

teacher_head_fields = {
        'username': fields.String,
        'nickname': fields.String,
        'uri': fields.Url('head'),
        'subject': fields.Nested(subjects_fields),
        'cla': fields.Nested(class_fields)
}

teacher_ord_fields = {
        'username': fields.String,
        'nickname': fields.String,
        'uri': fields.Url('ord'),
        'subject': fields.Nested(subjects_fields),
        'cla': fields.Nested(class_fields)
}
