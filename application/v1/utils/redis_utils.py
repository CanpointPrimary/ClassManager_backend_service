from redis.sentinel import Sentinel
from flask import jsonify

sentinel = Sentinel([('redis', 26379)], socket_timeout=0.1)
rds = sentinel.master_for('master', socket_timeout=0.1)


def ping(request):
    rds.incr('count', 1)
    cnt = rds.get('count')
    cnt = b'0' if cnt is None else cnt
    return jsonify(cnt.decode())
