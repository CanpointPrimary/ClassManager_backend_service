from dotenv import load_dotenv
import os

load_dotenv(verbose=True)
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = True
    SECRET_KEY = os.getenv('SECRET_KEY')

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_URL = os.getenv('REDIS_URL')

    AppId = os.getenv('APPID')
    AppSecret = os.getenv('APP_SECRET')


class DevelopConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URL')
    pass


class ProductConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URL')
    DEBUG = False


config_map = {
    "develop": DevelopConfig,
    "product": ProductConfig,
    "default": DevelopConfig
}
