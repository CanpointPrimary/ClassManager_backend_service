from fastapi import APIRouter

from app.api.class_manager import (
    classes, configurations, feedbacks, login, pages, users, school_homework
)

api_router = APIRouter()
api_router.include_router(classes.router, prefix='/classes', tags=['classes'])
api_router.include_router(
    configurations.router, prefix='/configurations', tags=['configurations']
)
api_router.include_router(
    feedbacks.router, prefix='/feedbacks', tags=['feedbacks']
)
api_router.include_router(login.router, tags=["login"])
api_router.include_router(pages.router, prefix='/pages', tags=['pages'])
api_router.include_router(users.router, prefix='/users', tags=['users'])
api_router.include_router(
    school_homework.router, prefix='/homeworks', tags=['school_homework']
)
