from flask import Blueprint, jsonify
from app import db
from app.models import Booking, Space # ⭐️ Booking과 Space 모델 둘 다 필요
from flask_jwt_extended import jwt_required, get_jwt_identity

# 'booking_bp' (booking blueprint) 라는 이름으로 새 블루프린트 생성
booking_bp = Blueprint('booking', __name__, url_prefix='/api')


# ⭐️ GET /api/bookings/my (내 예약 내역 조회)
@booking_bp.route("/bookings/my", methods=['GET'])
@jwt_required() # ⭐️ 이 API는 반드시 JWT 토큰이 있어야 함
def get_my_bookings():
    # 1. 토큰에서 현재 로그인한 사용자의 ID(학번)를 가져옴
    current_user_id = get_jwt_identity()

    # 2. DB에서 'Booking' 테이블과 'Space' 테이블을 조인(Join)하여 조회
    #    - 조건 1: Booking의 user_id가 현재 로그인한 사용자의 ID와 일치
    #    - 정렬: 최신순 (날짜 내림차순, 시작 시간 내림차순)
    try:
        bookings_query = db.session.query(Booking, Space)\
            .join(Space, Booking.space_id == Space.id)\
            .filter(Booking.user_id == current_user_id)\
            .order_by(Booking.date.desc(), Booking.start_time.desc())\
            .all()

        # 3. 프론트엔드(BookingHistoryPage.jsx)가 원하는 JSON 형식으로 데이터 가공
        results = []
        for booking, space in bookings_query:
            results.append({
                "id": booking.id,
                "date": booking.date,
                "startTime": booking.start_time,
                "endTime": booking.end_time,
                "room": space.name,             # ⭐️ Space 모델에서 이름(name)을 가져옴
                "location": space.location,     # ⭐️ Space 모델에서 위치(location)를 가져옴
                "applicant": booking.organizationName, # ⭐️ 프론트가 'applicant' 키를 사용
                "phone": booking.phone,
                "email": booking.email,
                "eventName": booking.event_name,
                "numPeople": booking.num_people,
                "acUse": booking.ac_use,
                "status": booking.status,
                "cancelReason": booking.cancel_reason
                # (displayStatus는 프론트엔드가 자체적으로 계산하므로 백엔드에서 필요 없음)
            })

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": "예약 내역 조회 중 오류 발생", "details": str(e)}), 500