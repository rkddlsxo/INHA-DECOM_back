from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_mail import Mail 
from flask_apscheduler import APScheduler 

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
migrate = Migrate()
mail = Mail() 
scheduler = APScheduler() 
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app) 
    
    
    scheduler.init_app(app)
    scheduler.start()

    
    CORS(app, resources={r"/*": {
        "origins": "*", 
        "allow_headers": ["Content-Type", "Authorization"]
    }})

    
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.booking import booking_bp
    app.register_blueprint(booking_bp)
 
    from app.routes.space import space_bp
    app.register_blueprint(space_bp)

    from app.routes.notification import notification_bp
    app.register_blueprint(notification_bp)

    from . import models
    with app.app_context():
        db.create_all()

    return app