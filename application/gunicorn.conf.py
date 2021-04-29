from gevent import monkey
monkey.patch_all()
import multiprocessing

bind = ['0.0.0.0:8000']
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
worker_class = 'gevent'
proc_name = 'application'
pidfile = '/log/gunicorn.pid'
timeout = 30
max_requests = 6000
loglevel = 'debug'
logfile = 'log/debug.log'
errorlog = 'log/error.log'
accesslog = 'log/access.log'
