from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import config_map

db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__, static_folder="../static", template_folder="..")
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate = Migrate(app, db)

    from v1 import api
    app.register_blueprint(api.api, url_prefix="/api/v1_0")

    return app
