from flask import Blueprint, jsonify, request
from app import db
from app.models import Space, Booking 
import calendar 
from sqlalchemy.sql import extract 

# 'space_bp' 라는 이름으로 블루프린트 생성
space_bp = Blueprint('space', __name__, url_prefix='/api')

# --- 헬퍼 함수 1 ---
def get_all_10_min_slots():
    """
    07:00 부터 21:50 까지 10분 단위 시간표(총 89개 슬롯)를 생성합니다.
   
    """
    slots = {}
    for h in range(7, 22): # 7시부터 21시
        for m in range(0, 60, 10): # 0분부터 50분까지 10분 간격
            if h == 21 and m > 50:
                break
            slot_key = f"{str(h).zfill(2)}:{str(m).zfill(2)}"
            slots[slot_key] = True # 기본값: 예약 가능 (True)
    return slots

# --- 헬퍼 함수 2 ---
def _calculate_booked_slots_count(bookings_for_day, all_slots_template):
    """
    특정 날짜의 예약 리스트를 받아, 몇 개의 10분 슬롯이 찼는지 계산합니다.
    """
    if not bookings_for_day:
        return 0
    
    time_slot_status = dict(all_slots_template) # 템플릿 복사
    
    for slot_time in time_slot_status:
        for booking in bookings_for_day:
            # 10분 단위 슬롯(slot_time)이 예약 범위(start_time ~ end_time) 안에 있는지 확인
            # (end_time은 포함하지 않음. 10:59 종료는 10:50 슬롯까지만 포함)
            if slot_time >= booking.start_time and slot_time < booking.end_time:
                time_slot_status[slot_time] = False # 예약됨으로 표시
                break # 이 슬롯은 False로 확정, 다음 슬롯 검사
    
    # False (예약됨)로 표시된 슬롯의 개수를 셈
    booked_count = sum(1 for status in time_slot_status.values() if not status)
    return booked_count


# --- API 1: 모든 장소 목록 ---
@space_bp.route("/masters/spaces", methods=['GET'])
def get_master_spaces():
    try:
        spaces = Space.query.all()
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


# --- API 2: 월별 현황 (심화 방안 적용) ---
@space_bp.route("/availability/monthly", methods=['GET'])
def get_monthly_availability():
    try:
        room_id = request.args.get('roomId', type=int)
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        if not all([room_id, year, month]):
            return jsonify({"error": "roomId, year, month는 필수 파라미터입니다."}), 400
    except ValueError:
        return jsonify({"error": "잘못된 파라미터 타입입니다."}), 400

    try:
        # 1. 10분 슬롯 템플릿과 총 슬롯 개수를 미리 계산 (총 89개)
        all_slots_template = get_all_10_min_slots()
        total_slots_count = len(all_slots_template)
        if total_slots_count == 0: # 0으로 나누기 방지
             return jsonify({"error": "슬롯 계산 오류"}), 500

        # 2. DB에서 해당 월의 모든 예약을 '한 번에' 가져옴
        bookings_in_month = Booking.query.filter(
            Booking.space_id == room_id,
            extract('year', Booking.date) == year,
            extract('month', Booking.date) == month,
            Booking.status != '취소'
        ).all()

        # 3. 날짜별로 예약 목록을 재그룹화 (Python Dictionary 사용)
        bookings_by_day = {}
        for b in bookings_in_month:
            date_key = str(b.date)
            if date_key not in bookings_by_day:
                bookings_by_day[date_key] = []
            bookings_by_day[date_key].append(b)

        # 4. 프론트엔드에 보낼 데이터 가공
        availability_data = {}
        num_days_in_month = calendar.monthrange(year, month)[1]

        for day in range(1, num_days_in_month + 1):
            date_key = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
            
            # 5. 해당 날짜의 예약 목록으로 예약된 슬롯 수 계산
            day_bookings = bookings_by_day.get(date_key, [])
            booked_count = _calculate_booked_slots_count(day_bookings, all_slots_template)

            # 6. 상태와 비율(Percentage) 계산
            percentage = 0.0
            status = "available"
            
            if booked_count > 0:
                percentage = round(booked_count / total_slots_count, 2)
                if booked_count >= total_slots_count:
                    status = "booked"
                    percentage = 1.0
                else:
                    status = "partial"
            
            # 7. 'status'와 'percentage'를 함께 반환
            availability_data[date_key] = {
                "status": status,
                "percentage": percentage 
            }
            
        return jsonify(availability_data), 200

    except Exception as e:
        return jsonify({"error": "월별 현황 조회 중 오류 발생", "details": str(e)}), 500


# --- API 3: 일별 현황 ---
@space_bp.route("/availability/daily", methods=['GET'])
def get_daily_availability():
    try:
        room_id = request.args.get('roomId', type=int)
        date = request.args.get('date', type=str)
        if not all([room_id, date]):
            return jsonify({"error": "roomId, date는 필수 파라미터입니다."}), 400
    except ValueError:
        return jsonify({"error": "잘못된 파라미터 타입입니다."}), 400

    try:
        time_slot_status = get_all_10_min_slots()
        bookings = Booking.query.filter(
            Booking.space_id == room_id,
            Booking.date == date,
            Booking.status != '취소'
        ).all()

        if bookings:
            for slot_time in time_slot_status:
                for booking in bookings:
                    if slot_time >= booking.start_time and slot_time < booking.end_time:
                        time_slot_status[slot_time] = False
                        break 
                        
        return jsonify(time_slot_status), 200
    except Exception as e:
        return jsonify({"error": "일별 현황 조회 중 오류 발생", "details": str(e)}), 500