from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager # ⭐️ 1. JWT import

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager() # ⭐️ 2. JWT 객체 생성

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # ⭐️ 3. JWT_SECRET_KEY 설정 (config.py의 SECRET_KEY 사용)
    # config.py 파일에 이미 SECRET_KEY가 있으므로 그걸 재사용합니다.
    app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app) # ⭐️ 4. 앱에 JWT 적용

    # 🔹 CORS를 "제일 처음"에 전체에 걸기 (테스트용)
    CORS(app, resources={r"/*": {"origins": "*"}})

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.booking import booking_bp
    app.register_blueprint(booking_bp)

    from . import models
    with app.app_context():
        db.create_all()

    return app