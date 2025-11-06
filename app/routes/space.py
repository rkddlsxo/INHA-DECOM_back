from flask import Blueprint, jsonify, request
from app import db
from app.models import Space, Booking 
import calendar 
from sqlalchemy.sql import extract, and_ 
from datetime import datetime, time 

space_bp = Blueprint('space', __name__, url_prefix='/api')

def get_all_10_min_slots():
    """
    07:00 부터 21:50 까지 10분 단위 시간표(총 89개 슬롯)를 생성합니다.
    """
    slots = {}
    for h in range(7, 22): 
        for m in range(0, 60, 10): 
            if h == 21 and m > 50:
                break
            slot_key = f"{str(h).zfill(2)}:{str(m).zfill(2)}"
            slots[slot_key] = True 
    return slots

def _calculate_booked_slots_count(bookings_for_day, all_slots_template):
    """
    특정 날짜의 예약 리스트를 받아, 몇 개의 10분 슬롯이 찼는지 계산합니다.
    (bookings_for_day의 예약은 time 객체를 가지고 있습니다)
    """
    if not bookings_for_day:
        return 0
    
    time_slot_status = dict(all_slots_template) 
    
    # 문자열 슬롯과 time 객체를 비교하기 위해, 슬롯 문자열을 time 객체로 변환하며 비교
    for slot_time_str in time_slot_status:
        try:
            slot_time_obj = datetime.strptime(slot_time_str, '%H:%M').time()
        except ValueError:
            continue 
            
        for booking in bookings_for_day:
            # time 객체끼리 비교
            if slot_time_obj >= booking.start_time and slot_time_obj < booking.end_time:
                time_slot_status[slot_time_str] = False 
                break 

    booked_count = sum(1 for status in time_slot_status.values() if not status)
    return booked_count

# ⭐️ [신규] 시간대별(오전/오후/저녁) 상태 계산 함수
def _calculate_period_status(bookings_for_day, all_slots_template):
    """
    오전(07:00-12:00), 오후(12:00-17:00), 저녁(17:00-22:00)의
    예약 상태(available, partial, booked)를 계산합니다.
    """
    periods = {
        "morning": {"start": time(7, 0), "end": time(12, 0), "total_slots": 0, "booked_slots": 0},
        "afternoon": {"start": time(12, 0), "end": time(17, 0), "total_slots": 0, "booked_slots": 0},
        "evening": {"start": time(17, 0), "end": time(22, 0), "total_slots": 0, "booked_slots": 0}
    }
    
    # 1. 각 시간대별 총 슬롯 수 계산
    for slot_str in all_slots_template:
        slot_time = datetime.strptime(slot_str, '%H:%M').time()
        for period, data in periods.items():
            if data["start"] <= slot_time < data["end"]:
                data["total_slots"] += 1
                break
                
    # 2. 예약된 슬롯 수 계산 (bookings_for_day가 비어있으면 이 루프는 스킵됨)
    if bookings_for_day:
        for slot_str in all_slots_template:
            slot_time = datetime.strptime(slot_str, '%H:%M').time()
            is_booked = False
            for booking in bookings_for_day:
                if booking.start_time <= slot_time < booking.end_time:
                    is_booked = True
                    break
            
            if is_booked:
                for period, data in periods.items():
                    if data["start"] <= slot_time < data["end"]:
                        data["booked_slots"] += 1
                        break

    # 3. 상태 결정
    result = {}
    for period, data in periods.items():
        if data["booked_slots"] == 0:
            result[period] = "available"
        elif data["total_slots"] > 0 and data["booked_slots"] >= data["total_slots"]:
            result[period] = "booked"
        elif data["booked_slots"] > 0:
            result[period] = "partial"
        else: # total_slots == 0 (이론상 발생 안 함)
            result[period] = "available"
            
    return result


#  ⭐️ [수정됨] API 1: 모든 장소 목록 (빠져있던 것을 다시 추가)
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


#  ⭐️ [수정됨] API 2: 월별 현황 (달력) - period_status 추가
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
            date_key = b.date.isoformat()
            if date_key not in bookings_by_day:
                bookings_by_day[date_key] = []
            bookings_by_day[date_key].append(b)

        availability_data = {}
        num_days_in_month = calendar.monthrange(year, month)[1]

        for day in range(1, num_days_in_month + 1):
            date_obj = datetime(year, month, day).date()
            date_key = date_obj.isoformat() 
            
            day_bookings = bookings_by_day.get(date_key, [])
            booked_count = _calculate_booked_slots_count(day_bookings, all_slots_template)
            
            # ⭐️ [신규] 시간대별 상태 계산
            period_status = _calculate_period_status(day_bookings, all_slots_template)
            
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
                "percentage": percentage,
                "period_status": period_status # ⭐️ [신규] 응답에 추가
            }
            
        return jsonify(availability_data), 200

    except Exception as e:
        return jsonify({"error": "월별 현황 조회 중 오류 발생", "details": str(e)}), 500


#  API 3: 일별 현황 (시간표) 
@space_bp.route("/availability/daily", methods=['GET'])
def get_daily_availability():
    try:
        room_id = request.args.get('roomId', type=int)
        date_str = request.args.get('date', type=str) 
        if not all([room_id, date_str]):
            return jsonify({"error": "roomId, date는 필수 파라미터입니다."}), 400
        
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
    except ValueError:
        return jsonify({"error": "잘못된 파라미터 타입 또는 날짜 형식입니다."}), 400

    try:
        time_slot_status = get_all_10_min_slots() 
        
        bookings = Booking.query.filter(
            Booking.space_id == room_id,
            Booking.date == date_obj,
            Booking.status != '취소'
        ).all()

        if bookings:
            for slot_time_str in time_slot_status:
                slot_time_obj = datetime.strptime(slot_time_str, '%H:%M').time()
                for booking in bookings:
                    if slot_time_obj >= booking.start_time and slot_time_obj < booking.end_time:
                        time_slot_status[slot_time_str] = False
                        break 
                        
        return jsonify(time_slot_status), 200
    except Exception as e:
        return jsonify({"error": "일별 현황 조회 중 오류 발생", "details": str(e)}), 500


# API 4: 시간 우선 예약 (사용 가능한 장소 조회) 
@space_bp.route("/spaces/available", methods=['GET'])
def get_available_spaces_for_time():
    try:
        date_str = request.args.get('date', type=str)
        start_time_str = request.args.get('start', type=str)
        end_time_str = request.args.get('end', type=str)

        if not all([date_str, start_time_str, end_time_str]):
            return jsonify({"error": "date, start, end는 필수 파라미터입니다."}), 400

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_obj = datetime.strptime(start_time_str, '%H:%M').time()
            end_obj = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            return jsonify({"error": "잘못된 날짜 또는 시간 형식입니다. (YYYY-MM-DD, HH:MM)"}), 400
        
        if start_obj >= end_obj:
            return jsonify({"error": "시작 시간은 종료 시간보다 빨라야 합니다."}), 400


    except Exception as e:
        return jsonify({"error": "잘못된 파라미터입니다.", "details": str(e)}), 400
    
    try:
        conflicting_bookings_query = db.session.query(Booking.space_id)\
            .filter(
                Booking.date == date_obj, 
                Booking.status != '취소',
                and_(
                    Booking.start_time < end_obj,  
                    Booking.end_time > start_obj   
                )
            )\
            .distinct()

        conflicting_space_ids = [b[0] for b in conflicting_bookings_query.all()]

        available_spaces = Space.query.filter(
            Space.id.notin_(conflicting_space_ids)
        ).all()
        
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