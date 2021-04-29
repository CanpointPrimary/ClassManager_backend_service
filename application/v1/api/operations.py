from flask_restful import Resource
from flask import jsonify
from flask import g

from v1.common.parser.opera_parser import operation_parse
from v1.utils.token import login_required
from v1.utils.code import Code
from models import Operations
from models import Teachers
from models import Students


class TeacherReleaseWorksResource(Resource):
    """
    release operation
    """
    @login_required
    def post(self, teaId):
        """
        release work
        :param teaId:
        :return:
        """
        args = operation_parse.parse_args()
        opera = Operations()
        opera.title = args.get('title')
        opera.content = args.get('content')
        opera.status = args.get('status')
        teacher = Teachers.query.filter_by(teaId=teaId).first()
        try:
            opera.add()
        except Exception as e:
            return e
        teacher.operations.append(opera)
        data = {
            'code': Code.OK,
            'msg': 'release success'
        }
        return jsonify(data)