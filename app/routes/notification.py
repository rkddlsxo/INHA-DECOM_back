from flask import Blueprint
from app import mail, scheduler, db
from app.models import Booking, User, Space
from flask_mail import Message
from datetime import datetime, timedelta, time
import pytz

notification_bp = Blueprint('notification', __name__, url_prefix='/api')

# 실제 이메일을 발송하는 함수
def send_reminder_email(booking, app):
    """
    백그라운드 스레드에서 실행되므로, app context를 명시적으로 받아야 합니다.
    """
    with app.app_context():
        try:
            
            recipient_email = booking.email
            user_name = booking.organizationName
            space_name = booking.space.name
            start_time_str = booking.start_time.strftime('%H:%M') 

            msg = Message(
                subject=f"[INHA-DECOM] 예약 알림: {space_name} ({start_time_str})",
                recipients=[recipient_email]
            )
            
            msg.body = f"""
            안녕하세요, {user_name}님.
            INHA-DECOM 예약 시스템입니다.

            잠시 후 {start_time_str}에 예약하신 '{space_name}' 이용 시간이 시작됩니다.
            (10분 전 알림)

            예약 장소의 QR 코드를 스캔하여 체크인해주시기 바랍니다.

            - 예약 날짜: {booking.date.isoformat()}
            - 예약 시간: {booking.start_time.strftime('%H:%M')} ~ {booking.end_time.strftime('%H:%M')}
            - 예약자: {booking.organizationName}
            
            감사합니다.
            """
            
            mail.send(msg)
            print(f"[SUCCESS] 알림 메일 발송 성공: {recipient_email} (예약 ID: {booking.id})")

        except Exception as e:
            print(f"[ERROR] 알림 메일 발송 실패: {str(e)} (예약 ID: {booking.id})")


# 스케줄러가 1분마다 실행할 작업 함수 
def check_upcoming_bookings():
    """
    1분마다 실행되며, 정확히 10분 뒤에 시작하는 예약을 찾아 메일을 발송합니다.
    """
    
    
    app = scheduler.app
    with app.app_context():
        
        kst = pytz.timezone('Asia/Seoul')
        now = datetime.now(kst)
        
        
        target_datetime = now + timedelta(minutes=10)
        target_date_obj = target_datetime.date()
        
        target_time_obj = target_datetime.time().replace(second=0, microsecond=0)

        try:
            
            upcoming_bookings = Booking.query.join(Space).filter(
                Booking.date == target_date_obj,
                Booking.start_time == target_time_obj,
                Booking.status.in_(['확정', '확정대기']) # 확정대기는 나중에 제외
                
            ).all()

            if upcoming_bookings:
                print(f"[{now.strftime('%H:%M')}] {len(upcoming_bookings)}개의 예약 알림 발송 시작... (타겟: {target_date_obj} {target_time_obj})")
                for booking in upcoming_bookings:
                    
                    send_reminder_email(booking, app)
            
            # 디버깅용
            else:
               print(f"[{now.strftime('%H:%M')}] 알림 대상 예약 없음. (타겟: {target_date_obj} {target_time_obj})")

        except Exception as e:
            print(f"[ERROR] 스케줄러 작업 중 오류 발생: {str(e)}")


@scheduler.task('interval', id='check_bookings_job', minutes=1, misfire_grace_time=900)
def scheduled_job():
    """APScheduler가 1분마다 이 함수를 실행합니다."""
    check_upcoming_bookings()