from flask_restful.reqparse import RequestParser

operation_parse = RequestParser()
operation_parse.add_argument('title', type=str, required=True, help='release operation name')
operation_parse.add_argument('content', type=str, required=True, help='fill in operation content')
operation_parse.add_argument('status', type=bool, help='operation whether to be released')