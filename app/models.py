from app import db, bcrypt
from datetime import datetime

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.String(8), primary_key=True) 
    username = db.Column(db.String(80), unique=False, nullable=False)
    password = db.Column(db.String(200), nullable=False) 

    bookings = db.relationship('Booking', backref='user', lazy=True)
    complaints = db.relationship('Complaint', backref='user', lazy=True)

    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = bcrypt.generate_password_hash(password).decode('utf-8') 

    def check_password(self, password):
       return bcrypt.check_password_hash(self.password, password)


class Space(db.Model):
    """
    시설/장소 마스터 테이블
    """
    __tablename__ = 'space'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subCategory = db.Column(db.String(100))
    location = db.Column(db.String(100))
    capacity = db.Column(db.Integer, nullable=False, default=1)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    bookings = db.relationship('Booking', backref='space', lazy=True, cascade="all, delete-orphan")
    complaints = db.relationship('Complaint', backref='space', lazy=True)

    def __init__(self, name, category, subCategory, location, capacity, latitude=None, longitude=None):
        self.name = name
        self.category = category
        self.subCategory = subCategory
        self.location = location
        self.capacity = capacity
        self.latitude = latitude
        self.longitude = longitude


class Booking(db.Model):
    """
    예약 정보 테이블
    """
    __tablename__ = 'booking'
    
    id = db.Column(db.Integer, primary_key=True) 

    user_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    space_id = db.Column(db.Integer, db.ForeignKey('space.id'), nullable=False)

    
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
   
    # 예약자 상세정보
    organizationType = db.Column(db.String(50))
    organizationName = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    event_name = db.Column(db.String(200), nullable=False)
    num_people = db.Column(db.Integer, nullable=False)
    ac_use = db.Column(db.String(3), default='no')
    
   
    status = db.Column(db.String(20), nullable=False, default='확정대기')
    cancel_reason = db.Column(db.Text, nullable=True)
    check_in_time = db.Column(db.DateTime, nullable=True, default=None)

    def __init__(self, user_id, space_id, date, start_time, end_time, organizationType, organizationName, phone, email, event_name, num_people, ac_use, status='확정대기'):
        self.user_id = user_id
        self.space_id = space_id
        
        # 문자열로 들어온 파라미터를 Date 및 Time 객체로 변환하여 저장
        try:
            self.date = datetime.strptime(date, '%Y-%m-%d').date()
            self.start_time = datetime.strptime(start_time, '%H:%M').time()
            self.end_time = datetime.strptime(end_time, '%H:%M').time()
        except ValueError as e:
            
            raise ValueError(f"날짜 또는 시간 형식이 잘못되었습니다: {e}")
        
            
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
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='접수')

    user_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=True)
    space_id = db.Column(db.Integer, db.ForeignKey('space.id'), nullable=True)

    def __init__(self, content, user_id=None, space_id=None):
        self.content = content
        self.user_id = user_id
        self.space_id = space_id