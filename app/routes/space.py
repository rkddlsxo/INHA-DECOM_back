from flask import Blueprint, jsonify, request # request 추가
from app import db
from app.models import Space, Booking # Booking 모델 추가
import calendar # 월의 일수를 가져오기 위해 import
from sqlalchemy.sql import extract # DB에서 월, 일을 추출하기 위해 import

# 'space_bp' 라는 이름으로 블루프린트 생성
space_bp = Blueprint('space', __name__, url_prefix='/api')


# ⭐️ GET /api/masters/spaces (모든 장소 마스터 목록)
@space_bp.route("/masters/spaces", methods=['GET'])
def get_master_spaces():
    try:
        spaces = Space.query.all()
        
        # ⭐️ 프론트가 사용하기 편하게 JSON 리스트로 변환
        results = []
        for space in spaces:
            results.append({
                "id": space.id,
                "name": space.name,
                "category": space.category,
                "subCategory": space.subCategory,
                "location": space.location,
                "capacity": space.capacity
            })
        
        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": "장소 목록 조회 중 오류 발생", "details": str(e)}), 500
    

    
    # GET /api/availability/monthly (월별 예약 현황)
@space_bp.route("/availability/monthly", methods=['GET'])
def get_monthly_availability():
    # 1. 프론트엔드에서 보낸 쿼리 파라미터(roomId, year, month)를 받음
    try:
        room_id = request.args.get('roomId', type=int)
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)

        if not all([room_id, year, month]):
            return jsonify({"error": "roomId, year, month는 필수 파라미터입니다."}), 400

    except ValueError:
        return jsonify({"error": "잘못된 파라미터 타입입니다."}), 400

    try:
        # 2. 해당 월(year, month)에 예약이 '있는' 날짜들을 DB에서 조회
        #    - Booking 모델의 date(YYYY-MM-DD) 필드를 기준으로 필터링
        booked_dates_query = db.session.query(Booking.date)\
            .filter(
                Booking.space_id == room_id,
                extract('year', Booking.date) == year,
                extract('month', Booking.date) == month,
                Booking.status != '취소' # 취소된 예약은 제외
            )\
            .distinct()\
            .all()
        
        # 3. DB 조회 결과를 [ '2025-11-20', '2025-11-22' ] 같은 Set으로 변환
        booked_dates_set = {str(date_obj[0]) for date_obj in booked_dates_query}

        # 4. 프론트엔드가 요구하는 JSON 형식으로 가공
        #    PlaceFocusSelectPage.jsx는 'YYYY-MM-DD'를 키로 사용
        availability_data = {}
        
        # 5. 해당 월의 마지막 날짜를 가져옴 (예: 11월은 30일)
        num_days_in_month = calendar.monthrange(year, month)[1]

        # 6. 1일부터 마지막 날까지 루프
        for day in range(1, num_days_in_month + 1):
            # YYYY-MM-DD 형식의 문자열 키 생성
            date_key = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
            
            # 7. 프론트가 요구하는 {"hasBooking": True/False} 형태로 저장
            availability_data[date_key] = {
                "hasBooking": (date_key in booked_dates_set)
            }
            
        return jsonify(availability_data), 200

    except Exception as e:
        return jsonify({"error": "월별 현황 조회 중 오류 발생", "details": str(e)}), 500