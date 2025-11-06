from flask import Blueprint, jsonify, request
from app import db
from app.models import Booking, Space 
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, time # [수정] time 객체 import
import pytz
from geopy.distance import geodesic 
from sqlalchemy.sql import and_ 

booking_bp = Blueprint('booking', __name__, url_prefix='/api')


@booking_bp.route("/bookings/my", methods=['GET'])
@jwt_required()
def get_my_bookings():
    current_user_id = get_jwt_identity()
    try:
        bookings_query = db.session.query(Booking, Space)\
            .join(Space, Booking.space_id == Space.id)\
            .filter(Booking.user_id == current_user_id)\
            .order_by(Booking.date.desc(), Booking.start_time.desc())\
            .all()

        results = []
        for booking, space in bookings_query:
            results.append({
                "id": booking.id,
                # --- ⭐️ [수정] 재예약 기능을 위해 space_id 추가 ---
                "space_id": booking.space_id,
                # --- [!!! 핵심 수정 !!!] ---
                # Date/Time 객체를 JSON으로 보내기 위해 문자열로 포맷팅
                "date": booking.date.isoformat(), # 예: "2025-11-05"
                "startTime": booking.start_time.strftime('%H:%M'), # 예: "09:00"
                "endTime": booking.end_time.strftime('%H:%M'), # 예: "11:00"
                # --- 수정 끝 ---
                "room": space.name,
                "location": space.location,
                "applicant": booking.organizationName,
                "phone": booking.phone,
                "email": booking.email,
                "eventName": booking.event_name,
                "numPeople": booking.num_people,
                "acUse": booking.ac_use,
                "status": booking.status,
                "cancelReason": booking.cancel_reason,
                # ⭐️ [추가] 재예약 폼 자동 완성을 위해 organizationType 추가
                "organizationType": booking.organizationType 
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": "예약 내역 조회 중 오류 발생", "details": str(e)}), 500


@booking_bp.route("/bookings", methods=['POST'])
@jwt_required()
def create_booking():
    data = request.get_json()
    current_user_id = get_jwt_identity()

    try:
        room_name = data.get('roomName')
        room_location = data.get('roomLocation')
        # [수정] 문자열(String) 변수임을 명시하기 위해 _str 접미사 추가
        date_str = data.get('date')
        start_time_str = data.get('startTime')
        end_time_str = data.get('endTime')

        space = Space.query.filter_by(name=room_name, location=room_location).first()

        if not space:
            return jsonify({"error": f"장소를 찾을 수 없습니다: {room_name} ({room_location})"}), 404
        
        # --- [!!! 핵심 수정 !!!] ---
        # 쿼리를 위해 문자열을 date/time 객체로 파싱
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_obj = datetime.strptime(start_time_str, '%H:%M').time()
            end_obj = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            return jsonify({"error": "잘못된 날짜 또는 시간 형식입니다. (YYYY-MM-DD, HH:MM)"}), 400

        # 중복 예약 검사 (DB의 Date/Time 타입과 비교)
        conflicting_booking = Booking.query.filter(
            Booking.space_id == space.id,
            Booking.date == date_obj, # date 객체로 비교
            Booking.status != '취소',
            and_(
                Booking.start_time < end_obj,   # time 객체로 비교
                Booking.end_time > start_obj    # time 객체로 비교
            )
        ).first() 

        if conflicting_booking:
            return jsonify({
                "error": "해당 시간대에 이미 다른 예약이 존재합니다.",
                # 객체를 다시 문자열로 포맷팅
                "details": f"기존 예약: {conflicting_booking.start_time.strftime('%H:%M')}~{conflicting_booking.end_time.strftime('%H:%M')}"
            }), 409
        # --- 수정 끝 ---

        # 모델 생성자에는 파싱을 담당하므로 문자열(String) 그대로 전달
        new_booking = Booking(
            user_id=current_user_id,
            space_id=space.id,
            date=date_str, 
            start_time=start_time_str, 
            end_time=end_time_str, 
            organizationType=data.get('organizationType'),
            organizationName=data.get('applicant'),
            phone=data.get('phone'),
            email=data.get('email'),
            event_name=data.get('eventName'),
            num_people=data.get('numPeople'),
            ac_use=data.get('acUse'),
            status=data.get('status', '확정대기')
        )

        db.session.add(new_booking)
        db.session.commit()
        
        return jsonify({"message": "예약이 성공적으로 접수되었습니다.", "bookingId": new_booking.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "예약 처리 중 오류 발생", "details": str(e)}), 500


@booking_bp.route("/bookings/<int:booking_id>/cancel", methods=['PATCH'])
@jwt_required()
def cancel_booking(booking_id):
    current_user_id = get_jwt_identity()
    
    try:
        booking = Booking.query.filter_by(id=booking_id, user_id=current_user_id).first()
        
        if not booking:
            return jsonify({"error": "해당 예약을 찾을 수 없거나 권한이 없습니다."}), 404
            
        if booking.status not in ['확정대기', '확정']:
             return jsonify({"error": f"'{booking.status}' 상태의 예약은 취소할 수 없습니다."}), 400

        booking.status = '취소'
        booking.cancel_reason = '사용자 요청' 
        
        db.session.commit()
        
        return jsonify({"message": "예약이 성공적으로 취소되었습니다."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "예약 취소 중 오류 발생", "details": str(e)}), 500


@booking_bp.route("/bookings/<int:booking_id>", methods=['PATCH'])
@jwt_required()
def update_booking(booking_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        booking = Booking.query.filter_by(id=booking_id, user_id=current_user_id).first()
        
        if not booking:
            return jsonify({"error": "해당 예약을 찾을 수 없거나 권한이 없습니다."}), 404
            
        if booking.status not in ['확정대기', '확정']:
             return jsonify({"error": f"'{booking.status}' 상태의 예약은 수정할 수 없습니다."}), 400

        booking.organizationName = data.get('applicant', booking.organizationName)
        booking.phone = data.get('phone', booking.phone)
        booking.email = data.get('email', booking.email)
        booking.event_name = data.get('eventName', booking.event_name)
        booking.num_people = data.get('numPeople', booking.num_people)
        booking.ac_use = data.get('acUse', booking.ac_use)
        booking.status = '확정대기'
        
        db.session.commit()
        
        return jsonify({"message": "예약 정보가 수정되었습니다. (상태: 확정대기)"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "예약 수정 중 오류 발생", "details": str(e)}), 500

GPS_THRESHOLD_METERS = 50 

@booking_bp.route("/check-in", methods=['POST'])
@jwt_required()
def check_in_booking():
    
    #1. 기본 정보 가져오기
    current_user_id = get_jwt_identity()
    try:
        space_id = request.args.get('space_id', type=int)
        if not space_id:
            return jsonify({"error": "space_id가 필요합니다."}), 400
        
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float)
        if user_lat is None or user_lng is None:
            return jsonify({"error": "GPS 위치 정보(lat, lng)가 필요합니다."}), 400
        
    except ValueError:
        return jsonify({"error": "잘못된 space_id 형식입니다."}), 400

    # --- [!!! 핵심 수정 !!!] ---
    # KST 기준, 문자열(str)이 아닌 date 및 time 객체를 생성
    kst = pytz.timezone('Asia/Seoul')
    current_time_kst = datetime.now(kst)
    current_date_obj = current_time_kst.date() # date 객체
    current_time_obj = current_time_kst.time() # time 객체
    
    # 15분 뒤의 time 객체
    allowed_start_time_limit_obj = (current_time_kst + timedelta(minutes=15)).time()
    # --- 수정 끝 ---

    try:
        # 2. 사용자 ID, 장소 ID, *그리고 오늘 date 객체*로 예약을 찾음
        booking = Booking.query.filter(
            Booking.user_id == current_user_id,
            Booking.space_id == space_id,
            Booking.date == current_date_obj  # date 객체로 비교
        ).first()

        if not booking:
            return jsonify({"error": f"오늘({current_date_obj.isoformat()}) 해당 장소({space_id})에 대한 예약 내역이 없습니다."}), 404

        #3. 예약이 존재하므로, 위치, 상태 및 시간 검증
        space = booking.space 
        
        if space.latitude and space.longitude:
            user_location = (user_lat, user_lng)
            space_location = (space.latitude, space.longitude)
            distance = geodesic(user_location, space_location).meters
            
            if distance > GPS_THRESHOLD_METERS:
                return jsonify({
                    "error": "체크인 실패: 현재 위치가 예약 장소와 너무 멉니다.",
                    "details": f"현재 거리: {int(distance)}m (허용 반경: {GPS_THRESHOLD_METERS}m)"
                }), 403 

        # [성공 1] 이미 체크인한 경우
        if booking.status == '이용중' or booking.check_in_time:
            return jsonify({
                "message": "이미 체크인되었습니다.",
                "user_name": booking.user.username,
                "space_name": booking.space.name,
                "start_time": booking.start_time.strftime('%H:%M'), # 포맷팅
                "end_time": booking.end_time.strftime('%H:%M')   # 포맷팅
            }), 200

        # [실패 3] '확정' 상태 아님
        if booking.status != '확정':
            return jsonify({"error": f"예약 상태가 '확정'이 아닙니다. (현재: {booking.status})"}), 403

        # --- [!!! 핵심 수정 !!!] ---
        # [실패 4] 예약 시간 종료 (time 객체로 비교)
        if booking.end_time <= current_time_obj:
            return jsonify({"error": f"예약 시간이 종료되었습니다. (종료: {booking.end_time.strftime('%H:%M')})"}), 403
            
        # [실패 5] 체크인 시간 미도래 (time 객체로 비교)
        if booking.start_time > allowed_start_time_limit_obj:
             return jsonify({"error": f"체크인 시간이 아닙니다. (예약 시작 {booking.start_time.strftime('%H:%M')}부터 가능)"}), 403
        # --- 수정 끝 ---

        #4. [성공 2] 신규 체크인 (모든 검증 통과)
        booking.check_in_time = current_time_kst
        booking.status = '이용중'
        db.session.commit()

        return jsonify({
            "message": "체크인 완료",
            "user_name": booking.user.username,
            "space_name": booking.space.name,
            "start_time": booking.start_time.strftime('%H:%M'), # 포맷팅
            "end_time": booking.end_time.strftime('%H:%M')   # 포맷팅
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "체크인 처리 중 오류 발생", "details": str(e)}), 500
