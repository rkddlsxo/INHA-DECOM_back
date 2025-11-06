from flask import Blueprint, jsonify, request
from app import db
from app.models import Booking, Space 
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, time
import pytz
from geopy.distance import geodesic 
from sqlalchemy.sql import and_ 
from sqlalchemy.exc import OperationalError # ⭐️ 1. 락(Lock) 오류 처리를 위해 import 추가

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
                "space_id": booking.space_id,
                "date": booking.date.isoformat(), 
                "startTime": booking.start_time.strftime('%H:%M'),
                "endTime": booking.end_time.strftime('%H:%M'), 
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
                "organizationType": booking.organizationType 
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": "예약 내역 조회 중 오류 발생", "details": str(e)}), 500


# ⭐️ 2. create_booking 함수 전체가 트랜잭션 락을 사용하도록 수정됨
@booking_bp.route("/bookings", methods=['POST'])
@jwt_required()
def create_booking():
    data = request.get_json()
    current_user_id = get_jwt_identity()

    # --- 1. 예약 정보 파싱 (Try-except 블록을 분리) ---
    try:
        room_name = data.get('roomName')
        room_location = data.get('roomLocation')
        date_str = data.get('date')
        start_time_str = data.get('startTime')
        end_time_str = data.get('endTime')

        space = Space.query.filter_by(name=room_name, location=room_location).first()

        if not space:
            return jsonify({"error": f"장소를 찾을 수 없습니다: {room_name} ({room_location})"}), 404
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_obj = datetime.strptime(start_time_str, '%H:%M').time()
            end_obj = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            return jsonify({"error": "잘못된 날짜 또는 시간 형식입니다. (YYYY-MM-DD, HH:MM)"}), 400

    except Exception as e:
        return jsonify({"error": "입력 데이터 파싱 중 오류 발생", "details": str(e)}), 400


    # --- 2. 락(Lock)을 사용한 트랜잭션 처리 (핵심 수정) ---
    try:
        # 2-1. 트랜잭션 시작 및 예약할 'Space' 리소스에 락(Lock)을 겁니다.
        #      (Pessimistic Locking)
        #      이 쿼리가 실행되면, 이 트랜잭션이 commit/rollback 될 때까지
        #      다른 요청은 이 space.id에 대해 with_for_update()를 사용할 수 없습니다.
        locked_space = db.session.query(Space).filter_by(id=space.id).with_for_update().first()
        
        if not locked_space:
            raise Exception("Space 리소스를 찾을 수 없거나 락을 걸 수 없습니다.")

        # 2-2. 락을 획득한 상태에서 중복 예약을 검사합니다. (Check)
        conflicting_booking = db.session.query(Booking).filter(
            Booking.space_id == locked_space.id,
            Booking.date == date_obj, 
            Booking.status != '취소',
            and_(
                Booking.start_time < end_obj,   
                Booking.end_time > start_obj    
            )
        ).first() 

        if conflicting_booking:
            # 중복이 발견되면 롤백하고(락 해제) 에러 반환
            db.session.rollback()
            return jsonify({
                "error": "해당 시간대에 이미 다른 예약이 존재합니다.",
                "details": f"기존 예약: {conflicting_booking.start_time.strftime('%H:%M')}~{conflicting_booking.end_time.strftime('%H:%M')}"
            }), 409
        
        # 2-3. 중복이 없으므로 예약을 생성합니다. (Act)
        new_booking = Booking(
            user_id=current_user_id,
            space_id=locked_space.id,
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
        
        # 2-4. DB에 최종 반영(commit)하고 락을 해제합니다.
        db.session.commit()
        
        return jsonify({"message": "예약이 성공적으로 접수되었습니다.", "bookingId": new_booking.id}), 201

    except OperationalError as e:
        # ⭐️ 3. 락 획득 실패, 데드락 등 DB 동시성 오류 처리
        db.session.rollback()
        return jsonify({"error": "예약 경쟁 실패: 다른 사용자가 동시에 예약 중입니다. 잠시 후 다시 시도해주세요.", "details": str(e)}), 503 # 503 Service Unavailable
    
    except Exception as e:
        # 2-5. 그 외 모든 오류 발생 시 롤백하고 락을 해제합니다.
        db.session.rollback()
        return jsonify({"error": "예약 트랜잭션 중 심각한 오류 발생", "details": str(e)}), 500


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

    
    kst = pytz.timezone('Asia/Seoul')
    current_time_kst = datetime.now(kst)
    current_date_obj = current_time_kst.date() 
    current_time_obj = current_time_kst.time() 
    
   
    allowed_start_time_limit_obj = (current_time_kst + timedelta(minutes=15)).time()
   

    try:
        booking = Booking.query.filter(
            Booking.user_id == current_user_id,
            Booking.space_id == space_id,
            Booking.date == current_date_obj 
        ).first()

        if not booking:
            return jsonify({"error": f"오늘({current_date_obj.isoformat()}) 해당 장소({space_id})에 대한 예약 내역이 없습니다."}), 404

        
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

        
        if booking.status == '이용중' or booking.check_in_time:
            return jsonify({
                "message": "이미 체크인되었습니다.",
                "user_name": booking.user.username,
                "space_name": booking.space.name,
                "start_time": booking.start_time.strftime('%H:%M'), 
                "end_time": booking.end_time.strftime('%H:%M')   
            }), 200

        if booking.status != '확정':
            return jsonify({"error": f"예약 상태가 '확정'이 아닙니다. (현재: {booking.status})"}), 403

        
        if booking.end_time <= current_time_obj:
            return jsonify({"error": f"예약 시간이 종료되었습니다. (종료: {booking.end_time.strftime('%H:%M')})"}), 403
            
        
        if booking.start_time > allowed_start_time_limit_obj:
             return jsonify({"error": f"체크인 시간이 아닙니다. (예약 시작 {booking.start_time.strftime('%H:%M')}부터 가능)"}), 403

        booking.check_in_time = current_time_kst
        booking.status = '이용중'
        db.session.commit()

        return jsonify({
            "message": "체크인 완료",
            "user_name": booking.user.username,
            "space_name": booking.space.name,
            "start_time": booking.start_time.strftime('%H:%M'), 
            "end_time": booking.end_time.strftime('%H:%M')   
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "체크인 처리 중 오류 발생", "details": str(e)}), 500