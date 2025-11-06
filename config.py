import os # 환경 변수를 사용

class Config:
   
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_very_secret_key'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'mysql+pymysql://root@localhost/decom'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    
    # Flask-Mail 설정 
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True

    # export MAIL_USERNAME="내Gmail@gmail.com"
    # export MAIL_PASSWORD="위에서받은16자리앱비밀번호"
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('INHA-DECOM', os.environ.get('MAIL_USERNAME'))
