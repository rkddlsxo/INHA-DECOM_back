from app import db # app.py에서 만든 db 객체를 가져옵니다.

class User(db.Model):
    __tablename__ = 'user' # 실제 데이터베이스 테이블 이름
    
    id = db.Column(db.String(8), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # 객체 생성 시 초기화 메서드 (email 제외)
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password