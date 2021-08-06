import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware

from app.api.class_manager.api import api_router
from app.core.config import settings
from app.exceptions import http_exception_handler


# 保存项目根路径到配置对象
settings.BASE_DIR = os.path.abspath(os.path.dirname(__file__))


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.CLASS_MANAGER_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event('startup')
def startup_event():
    os.mkdir('static') if not os.path.exists('static') else ...
    os.mkdir('static/pics') if not os.path.exists('static/pics') else ...


# 注册API路由
app.include_router(api_router, prefix=settings.CLASS_MANAGER_STR)
# 挂载静态文件目录
STATIC_PATH = os.path.join(settings.BASE_DIR, 'static')
app.mount('/files', StaticFiles(directory=STATIC_PATH), name='static')
# 注册自定义异常处理函数
app.add_exception_handler(HTTPException, http_exception_handler)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', reload=True)  # local test
