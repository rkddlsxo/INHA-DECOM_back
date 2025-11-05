from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_mail import Mail # [추가]
from flask_apscheduler import APScheduler # [추가]

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
migrate = Migrate()
mail = Mail() # [추가]
scheduler = APScheduler() # [추가]

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app) # [추가]
    
    # [추가] 스케줄러 초기화 및 시작
    # (주의: debug=True일 때 서버가 재시작될 때마다 작업이 중복 등록될 수 있으나,
    #  id='check_bookings_job'를 고정하여 중복을 방지합니다.)
    scheduler.init_app(app)
    scheduler.start()

    # 1. CORS 설정에 'Authorization' 헤더가 꼭 포함되어야 합니다.
    CORS(app, resources={r"/*": {
        "origins": "*", # (주의) 실제 배포 시에는 보안을 위해 프론트 주소로 변경하세요.
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

    # --- [!!! 여기에 추가 !!!] ---
    # 4. 알림 스케줄러 작업을 로드하기 위해 새 블루프린트를 등록합니다.
    from app.routes.notification import notification_bp
    app.register_blueprint(notification_bp)
    # --- 추가 끝 ---

    from . import models
    with app.app_context():
        db.create_all()

    return app