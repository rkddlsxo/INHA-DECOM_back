from flask import Blueprint, jsonify, request
from app import db
from app.models import Space, Booking 
import calendar 
from sqlalchemy.sql import extract, and_ 

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
            if slot_time >= booking.start_time and slot_time < booking.end_time:
                time_slot_status[slot_time] = False 
                break 
    
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


# --- API 2: 월별 현황 (달력) ---
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
        all_slots_template = get_all_10_min_slots()
        total_slots_count = len(all_slots_template)
        if total_slots_count == 0:
             return jsonify({"error": "슬롯 계산 오류"}), 500

        bookings_in_month = Booking.query.filter(
            Booking.space_id == room_id,
            extract('year', Booking.date) == year,
            extract('month', Booking.date) == month,
            Booking.status != '취소'
        ).all()

        bookings_by_day = {}
        for b in bookings_in_month:
            date_key = str(b.date)
            if date_key not in bookings_by_day:
                bookings_by_day[date_key] = []
            bookings_by_day[date_key].append(b)

        availability_data = {}
        num_days_in_month = calendar.monthrange(year, month)[1]

        for day in range(1, num_days_in_month + 1):
            date_key = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
            day_bookings = bookings_by_day.get(date_key, [])
            booked_count = _calculate_booked_slots_count(day_bookings, all_slots_template)
            
            percentage = 0.0
            status = "available"
            
            if booked_count > 0:
                percentage = round(booked_count / total_slots_count, 2)
                if booked_count >= total_slots_count:
                    status = "booked"
                    percentage = 1.0
                else:
                    status = "partial"
            
            availability_data[date_key] = {
                "status": status,
                "percentage": percentage 
            }
            
        return jsonify(availability_data), 200

    except Exception as e:
        return jsonify({"error": "월별 현황 조회 중 오류 발생", "details": str(e)}), 500


# --- API 3: 일별 현황 (시간표) ---
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


# --- API 4: 시간 우선 예약 (사용 가능한 장소 조회) ---
@space_bp.route("/spaces/available", methods=['GET'])
def get_available_spaces_for_time():
    try:
        date = request.args.get('date', type=str)
        start_time = request.args.get('start', type=str)
        end_time = request.args.get('end', type=str)

        if not all([date, start_time, end_time]):
            return jsonify({"error": "date, start, end는 필수 파라미터입니다."}), 400
        
        if start_time >= end_time:
            return jsonify({"error": "시작 시간은 종료 시간보다 빨라야 합니다."}), 400

    except Exception as e:
        return jsonify({"error": "잘못된 파라미터입니다.", "details": str(e)}), 400
    
    try:
        # 1. 해당 시간에 겹치는 예약이 있는 space_id 목록을 찾음
        conflicting_bookings_query = db.session.query(Booking.space_id)\
            .filter(
                Booking.date == date,
                Booking.status != '취소',
                and_(
                    Booking.start_time < end_time,   # 요청 시작 < 예약 끝
                    Booking.end_time > start_time    # 요청 끝 > 예약 시작
                )
            )\
            .distinct()

        conflicting_space_ids = [b[0] for b in conflicting_bookings_query.all()]

        # 2. 이 목록에 '포함되지 않은' 모든 장소를 조회
        available_spaces = Space.query.filter(
            Space.id.notin_(conflicting_space_ids)
        ).all()
        
        # 3. JSON으로 가공
        results = []
        for space in available_spaces:
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
        return jsonify({"error": "사용 가능한 장소 조회 중 오류 발생", "details": str(e)}), 500