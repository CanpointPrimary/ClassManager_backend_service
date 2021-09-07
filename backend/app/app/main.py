import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.middleware import log_requests
from app.exceptions import (
    BizHTTPException, broad_exception_handler, http_exception_handler
)
from app.utils import init_logger


# 保存项目根路径到配置对象
settings.BASE_DIR = os.path.abspath(os.path.dirname(__file__))


app = FastAPI(
    title=settings.PROJECT_NAME,
    root_path=settings.BASE_DIR,
    description='ClassManager backend service',
    openapi_url=f"{settings.CLASS_MANAGER_STR}/openapi.json"
)

# 跨域配置
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# 初始化静态文件目录
@app.on_event('startup')
def startup_event():
    os.mkdir('static') if not os.path.exists('static') else ...
    os.mkdir('static/pics') if not os.path.exists('static/pics') else ...
    os.mkdir('upload') if not os.path.exists('upload') else ...
    os.mkdir('upload/pics') if not os.path.exists('upload/pics') else ...


# 注册API路由
app.include_router(api_router, prefix=settings.CLASS_MANAGER_STR)
# 挂载静态文件目录
STATIC_PATH = os.path.join(settings.BASE_DIR, 'static')
app.mount('/files', StaticFiles(directory=STATIC_PATH), name='static')
# 注册自定义异常处理函数
app.add_exception_handler(BizHTTPException, http_exception_handler)
app.add_exception_handler(Exception, broad_exception_handler)
# 注册中间件
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)
# 初始化日志
init_logger()
