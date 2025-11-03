class Config:
    # Bcrypt 같은 확장 기능을 쓸 때 필요한 시크릿 키
    SECRET_KEY = 'a_very_very_secret_key'


    # DB 설정
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://decom_user:i12jjmmq@localhost/decom'
    SQLALCHEMY_TRACK_MODIFICATIONS = False