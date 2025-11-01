from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS

db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    bcrypt.init_app(app)

    # 🔹 CORS를 "제일 처음"에 전체에 걸기 (테스트용)
    CORS(app, resources={r"/*": {"origins": "*"}})

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from . import models
    with app.app_context():
        db.create_all()

    return app
