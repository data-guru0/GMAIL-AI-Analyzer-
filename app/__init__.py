import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from config import config

db = SQLAlchemy()
sess = Session()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"),
    )
    app.config.from_object(config[config_name])

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs("flask_session", exist_ok=True)

    db.init_app(app)
    sess.init_app(app)

    from .auth import auth_bp
    from .main import main_bp
    from .api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        db.create_all()

    from .scheduler import start_scheduler
    start_scheduler(app)

    return app
