from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS

# 확장 기능들을 앱 생성 전에 초기화
db = SQLAlchemy()
bcrypt = Bcrypt()
cors = CORS()

def create_app():
    """
    애플리케이션 팩토리 함수.
    Flask 앱 인스턴스를 생성하고 초기화합니다.
    """
    app = Flask(__name__)

    # 1. config.py 파일로부터 설정 불러오기
    app.config.from_object('config.Config')

    # 2. 확장 기능들을 앱에 등록 (초기화)
    db.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app)

    # 3. 블루프린트 등록
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    # 4. DB 테이블 생성 (models.py를 인식시키기 위해 import 필요)
    from . import models
    with app.app_context():
        db.create_all()

    return app