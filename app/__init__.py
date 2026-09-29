from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from flasgger import Swagger
import logging
import os

db = SQLAlchemy()
jwt = JWTManager()


def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET")

    if test_config:
        app.config.update(test_config)

    Swagger(app)

    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log"),
            logging.StreamHandler()
        ]
    )

    db.init_app(app)
    jwt.init_app(app)

    from app.routes import routes
    app.register_blueprint(routes)

    return app