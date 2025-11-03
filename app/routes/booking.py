from flask import Blueprint, jsonify, request
from app import db
from app.models import Booking, Space 
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import pytz

# 'booking_bp' (booking blueprint) 라는 이름으로 새 블루프린트 생성
booking_bp = Blueprint('booking', __name__, url_prefix='/api')


# GET /api/bookings/my (내 예약 내역 조회)
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
                "date": booking.date,
                "startTime": booking.start_time,
                "endTime": booking.end_time,
                "room": space.name,
                "location": space.location,
                "applicant": booking.organizationName,
                "phone": booking.phone,
                "email": booking.email,
                "eventName": booking.event_name,
                "numPeople": booking.num_people,
                "acUse": booking.ac_use,
                "status": booking.status,
                "cancelReason": booking.cancel_reason
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": "예약 내역 조회 중 오류 발생", "details": str(e)}), 500


# POST /api/bookings (신규 예약 생성)
@booking_bp.route("/bookings", methods=['POST'])
@jwt_required()
def create_booking():
    data = request.get_json()
    current_user_id = get_jwt_identity()

    try:
        room_name = data.get('roomName')
        room_location = data.get('roomLocation')
        
        space = Space.query.filter_by(name=room_name, location=room_location).first()

        if not space:
            return jsonify({"error": f"장소를 찾을 수 없습니다: {room_name} ({room_location})"}), 404
        
        new_booking = Booking(
            user_id=current_user_id,
            space_id=space.id,
            date=data.get('date'),
            start_time=data.get('startTime'),
            end_time=data.get('endTime'),
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


# PATCH /api/bookings/<int:booking_id>/cancel (예약 취소)
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


# PATCH /api/bookings/<int:booking_id> (예약 정보 수정)
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
    
@booking_bp.route("/check-in", methods=['POST'])
@jwt_required()
def check_in_booking():
    
    #1. 기본 정보 가져오기
    current_user_id = get_jwt_identity()
    try:
        space_id = request.args.get('space_id', type=int)
        if not space_id:
            return jsonify({"error": "space_id가 필요합니다."}), 400
    except ValueError:
        return jsonify({"error": "잘못된 space_id 형식입니다."}), 400

    # KST (한국 시간) 기준
    kst = pytz.timezone('Asia/Seoul')
    current_time_kst = datetime.now(kst)
    current_date_str = current_time_kst.strftime("%Y-%m-%d")
    current_time_str = current_time_kst.strftime("%H:%M")
    # 예약 시작 15분 전부터 체크인 허용
    allowed_start_time_limit = (current_time_kst + timedelta(minutes=15)).strftime("%H:%M")

    try:
        #2. 사용자 ID와 장소 ID로 예약을 먼저 찾음
        booking = Booking.query.filter(
            Booking.user_id == current_user_id,
            Booking.space_id == space_id
        ).first()

        # [실패 1] 예약 자체가 존재하지 않음
        if not booking:
            return jsonify({"error": f"해당 장소({space_id})에 대한 예약 내역이 없습니다."}), 404

        #3. 예약이 존재하므로, 상태 및 시간 검증

        # [성공 1] 이미 체크인한 경우 (새로고침)
        # 오늘 날짜이고, 상태가 '이용중'이거나 check_in_time이 이미 기록됨
        if booking.date == current_date_str and (booking.status == '이용중' or booking.check_in_time):
            return jsonify({
                "message": "이미 체크인되었습니다.",
                "user_name": booking.user.username,
                "space_name": booking.space.name,
                "start_time": booking.start_time,
                "end_time": booking.end_time
            }), 200

        # [실패 2] 날짜 불일치
        if booking.date != current_date_str:
            return jsonify({"error": f"예약 날짜가 오늘({current_date_str})이 아닙니다. (예약: {booking.date})"}), 403
        
        # [실패 3] '확정' 상태 아님 (예: '확정대기' 또는 '취소')
        if booking.status != '확정':
            return jsonify({"error": f"예약 상태가 '확정'이 아닙니다. (현재: {booking.status})"}), 403

        # [실패 4] 예약 시간 종료
        if booking.end_time <= current_time_str:
            return jsonify({"error": f"예약 시간이 종료되었습니다. (종료: {booking.end_time})"}), 403
            
        # [실패 5] 체크인 시간 미도래
        if booking.start_time > allowed_start_time_limit:
             return jsonify({"error": f"체크인 시간이 아닙니다. (예약 시작 {booking.start_time}부터 가능)"}), 403

        #4. [성공 2] 신규 체크인 (모든 검증 통과)
        booking.check_in_time = current_time_kst
        booking.status = '이용중'
        db.session.commit()

        return jsonify({
            "message": "체크인 완료",
            "user_name": booking.user.username,
            "space_name": booking.space.name,
            "start_time": booking.start_time,
            "end_time": booking.end_time
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "체크인 처리 중 오류 발생", "details": str(e)}), 500