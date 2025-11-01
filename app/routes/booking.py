from flask import Blueprint, jsonify, request
from app import db
from app.models import Booking, Space # Space 모델 import
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