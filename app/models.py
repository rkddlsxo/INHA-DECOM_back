from app import db # app.py에서 만든 db 객체를 가져옵니다.
from datetime import datetime
# ❗️ 비밀번호 해싱을 위해 import (회원가입/로그인 로직에서 사용)
# from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.String(8), primary_key=True) # 학번
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False) # ⭐️ 해시된 비밀번호를 저장해야 합니다.

    # ⭐️ 관계 설정: User가 삭제되어도 예약 내역은 남길 수 있습니다 (cascade="all, delete-orphan"은 제외)
    # 'user'는 Booking 모델에서 User 객체를 .user로 접근할 때 사용됩니다.
    bookings = db.relationship('Booking', backref='user', lazy=True)
    complaints = db.relationship('Complaint', backref='user', lazy=True)

    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        # ⭐️ 실제로는 해시된 비밀번호를 저장해야 합니다.
        # self.password = generate_password_hash(password) 
        self.password = password # (임시로 평문 저장, 보안에 취약)

    # ⭐️ 로그인 시 비밀번호 검증 메서드 (예시)
    # def check_password(self, password):
    #    return check_password_hash(self.password, password)


class Space(db.Model):
    """
    시설/장소 마스터 테이블 (PlaceFocusSelectPage, TimeFocusSelectPage에서 사용)
    """
    __tablename__ = 'space'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)        # 예: "인문 스터디룸 1"
    category = db.Column(db.String(50), nullable=False)     # 예: "스터디룸"
    subCategory = db.Column(db.String(100))                 # 예: "인문 스터디룸"
    location = db.Column(db.String(100))                    # 예: "60주년 501호"
    capacity = db.Column(db.Integer, nullable=False, default=1) # 수용 인원
    
    # ⭐️ Space가 삭제되면 관련 예약 내역도 삭제 (필요에 따라 정책 변경)
    bookings = db.relationship('Booking', backref='space', lazy=True, cascade="all, delete-orphan")
    complaints = db.relationship('Complaint', backref='space', lazy=True)

    def __init__(self, name, category, subCategory, location, capacity):
        self.name = name
        self.category = category
        self.subCategory = subCategory
        self.location = location
        self.capacity = capacity


class Booking(db.Model):
    """
    예약 정보 테이블 (ReservationDetailsPage, BookingHistoryPage에서 사용)
    """
    __tablename__ = 'booking'
    
    id = db.Column(db.Integer, primary_key=True) # 예약 고유 ID

    # ⭐️ 외래 키: User, Space 테이블과 연결
    user_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    space_id = db.Column(db.Integer, db.ForeignKey('space.id'), nullable=False)

    # 1. 예약 시간 정보 (Front-end의 tempBookingData)
    # ⭐️ 날짜는 YYYY-MM-DD, 시간은 HH:MM 형식으로 저장 (정렬 및 쿼리 용이)
    date = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    
    # 2. 예약자 상세 정보 (Front-end의 formData)
    organizationType = db.Column(db.String(50))
    organizationName = db.Column(db.String(100), nullable=False) # BookingHistory의 '신청자'
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    event_name = db.Column(db.String(200), nullable=False)
    num_people = db.Column(db.Integer, nullable=False)
    ac_use = db.Column(db.String(3), default='no') # 'yes' or 'no'
    
    # 3. 예약 상태 정보
    status = db.Column(db.String(20), nullable=False, default='확정대기') # 예: '확정대기', '확정', '취소'
    cancel_reason = db.Column(db.Text, nullable=True) # 취소 사유

    # 체크인한 시간을 기록 (체크인 안 했으면 NULL로 체크인 여부 관리)
    check_in_time = db.Column(db.DateTime, nullable=True, default=None)

    def __init__(self, user_id, space_id, date, start_time, end_time, organizationType, organizationName, phone, email, event_name, num_people, ac_use, status='확정대기'):
        self.user_id = user_id
        self.space_id = space_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.organizationType = organizationType
        self.organizationName = organizationName
        self.phone = phone
        self.email = email
        self.event_name = event_name
        self.num_people = num_people
        self.ac_use = ac_use
        self.status = status


class Complaint(db.Model):
    """
    민원/시설 제보 테이블
    """
    __tablename__ = 'complaint'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False) # 제보 내용
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # 작성 시간
    status = db.Column(db.String(20), default='접수') # '접수', '처리중', '완료'

    # ⭐️ 외래 키: 누가, 어느 장소를 제보했는지 (선택적)
    user_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=True) # 익명 제보 가능
    space_id = db.Column(db.Integer, db.ForeignKey('space.id'), nullable=True) # 특정 장소 지정

    def __init__(self, content, user_id=None, space_id=None):
        self.content = content
        self.user_id = user_id
        self.space_id = space_id
