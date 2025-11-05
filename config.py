import os # [추가] 환경 변수를 사용하기 위해 import

class Config:
    # [수정] 보안: 하드코딩 대신 환경 변수에서 읽어옵니다.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_very_secret_key'

    # [수정] 보안: 하드코딩 대신 환경 변수에서 읽어옵니다.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'mysql+pymysql://root@localhost/decom'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- [!!! 여기에 추가 !!!] ---
    # Flask-Mail 설정 (Gmail 기준)
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    
    # (주의!) 터미널에서 미리 환경 변수를 설정해야 합니다.
    # export MAIL_USERNAME="내Gmail@gmail.com"
    # export MAIL_PASSWORD="위에서받은16자리앱비밀번호"
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('INHA-DECOM', os.environ.get('MAIL_USERNAME'))
    # --- 추가 끝 ---