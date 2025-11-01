from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # 1. CORS 설정에 'Authorization' 헤더가 꼭 포함되어야 합니다.
    CORS(app, resources={r"/*": {
        "origins": "*",
        "allow_headers": ["Content-Type", "Authorization"]
    }})

    # --- 블루프린트 등록 ---
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    # 2. 이 부분이 404 오류를 해결하는 핵심입니다.
    from app.routes.booking import booking_bp
    app.register_blueprint(booking_bp)
    
    # 3. 이 부분은 장소 목록 API를 위한 것입니다.
    from app.routes.space import space_bp
    app.register_blueprint(space_bp)
    # --- 등록 끝 ---

    from . import models
    with app.app_context():
        db.create_all()

    return app