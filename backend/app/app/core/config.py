import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, HttpUrl, PostgresDsn, \
    validator
# from app import local_env  # local test


class Settings(BaseSettings):
    BASE_DIR: str = None            # 项目根目录路径

    CLASS_MANAGER_STR: str = "/class_manager"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # AES加密用 KEY、向量
    AES_KEY: str = "a0210ae37f395d9a0ab95494883fb3ea"
    AES_IV: str = "0bdd880f310f4eaf"
    # 短信发送 时间间隔、超时时间
    SEND_SMS_INTERVAL_SECONDS: int = 1 * 60
    SMS_CAPTCHA_EXPIRE_SECONDS: int = 5 * 60
    # Token有效期 60 * 24 * 7 minutes = 7 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    SERVER_NAME: str
    SERVER_HOST: AnyHttpUrl
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:80", "http://localhost:3000", \  # noqa
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:  # noqa
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str
    SENTRY_DSN: Optional[HttpUrl] = None

    @validator("SENTRY_DSN", pre=True)
    def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:  # noqa
        if len(v) == 0:
            return None
        return v

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:  # noqa
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None

    @validator("EMAILS_FROM_NAME")
    def get_project_name(cls, v: Optional[str], values: Dict[str, Any]) -> str:  # noqa
        if not v:
            return values["PROJECT_NAME"]
        return v

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "/app/app/email-templates/build"
    EMAILS_ENABLED: bool = False

    @validator("EMAILS_ENABLED", pre=True)
    def get_emails_enabled(cls, v: bool, values: Dict[str, Any]) -> bool:  # noqa
        return bool(
            values.get("SMTP_HOST")
            and values.get("SMTP_PORT")
            and values.get("EMAILS_FROM_EMAIL")
        )

    EMAIL_TEST_USER: EmailStr = "test@example.com"  # type: ignore
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    API_GW_ACCESS_KEY_ID: str
    API_GW_ACCESS_KEY_SECRET: str
    API_GW_APP_KEY: str
    API_GW_APP_SECRET: str
    SYNC_SCHOOL_API_ID: str
    SYNC_SCHOOL_PAGE_SIZE: int
    SYNC_SCHOOL_URL: AnyHttpUrl

    MINI_PROGRAM_APP_ID: str
    MINI_PROGRAM_APP_SECRET: str
    CODE2SESSION_URL: HttpUrl
    WX_ACCESS_TOKEN_URL: HttpUrl
    WX_ACCESS_TOKEN_EXPIRES: int
    WX_ACCESS_TOKEN_UPDATE_OFFSET: int
    WXACODE_GET_UNLIMITED_URL: HttpUrl
    WX_GET_URL_LINK_URL: HttpUrl

    LOG_LEVEL: str
    CELERY_BROKER_URL: str

    REDIS_HOST: str
    REDIS_PORT: int

    @validator('LOG_LEVEL', pre=True)
    def get_log_level(cls, v: str) -> str:  # noqa
        v = v.upper()
        if v not in (
                'TRACE', 'DEBUG', 'INFO', 'SUCCESS',
                'WARNING', 'ERROR', 'CRITICAL'
        ):
            raise ValueError(f'Invalid log level {v}')
        return v

    TENCENT_CLOUD_SECRET_ID: str
    TENCENT_CLOUD_SECRET_KEY: str
    TENCENT_CLOUD_SMS_SDK_APPID: str
    TENCENT_CLOUD_SMS_TEMPLATE_ID: str
    TENCENT_CLOUD_SMS_SIGN: str

    class Config:
        case_sensitive = True


settings = Settings()


if __name__ == '__main__':
    print(settings.SQLALCHEMY_DATABASE_URI)
