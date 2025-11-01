from flask import Blueprint, jsonify, request
from app import db
from app.models import Booking, Space 
from flask_jwt_extended import jwt_required, get_jwt_identity

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