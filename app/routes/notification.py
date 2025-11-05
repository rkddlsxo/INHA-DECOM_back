from flask import Blueprint
from app import mail, scheduler, db
from app.models import Booking, User, Space
from flask_mail import Message
from datetime import datetime, timedelta, time
import pytz

# 이 블루프린트는 실제 API 라우트를 가지지 않고, 스케줄러 작업을 로드하는 역할만 합니다.
notification_bp = Blueprint('notification', __name__, url_prefix='/api')

# --- 1. 실제 이메일을 발송하는 함수 ---
def send_reminder_email(booking, app):
    """
    백그라운드 스레드에서 실행되므로, app context를 명시적으로 받아야 합니다.
    """
    with app.app_context():
        try:
            # Booking 객체에서 필요한 정보 추출
            recipient_email = booking.email
            user_name = booking.organizationName
            space_name = booking.space.name
            start_time_str = booking.start_time.strftime('%H:%M') # "09:00"

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


# --- 2. 스케줄러가 1분마다 실행할 작업 함수 ---
def check_upcoming_bookings():
    """
    1분마다 실행되며, 정확히 10분 뒤에 시작하는 예약을 찾아 메일을 발송합니다.
    """
    
    # APScheduler는 Flask의 app context 외부에서 실행되므로,
    # app context를 수동으로 생성해줘야 DB 쿼리 등이 가능합니다.
    app = scheduler.app
    with app.app_context():
        
        kst = pytz.timezone('Asia/Seoul')
        now = datetime.now(kst)
        
        # 정확히 10분 뒤의 날짜와 시간 객체를 계산합니다.
        target_datetime = now + timedelta(minutes=10)
        target_date_obj = target_datetime.date()
        # (중요) DB의 Time 타입과 비교하기 위해 초(second)와 마이크로초(microsecond)를 0으로 설정
        target_time_obj = target_datetime.time().replace(second=0, microsecond=0)

        try:
            # DB가 Date/Time 타입이므로 쿼리가 매우 효율적입니다.
            upcoming_bookings = Booking.query.join(Space).filter(
                Booking.date == target_date_obj,
                Booking.start_time == target_time_obj,
                Booking.status.in_(['확정', '확정대기']) # 확정대기는 나중에 제외
                # (개선) 여기에 '알림을 아직 안 보낸 예약' 조건을 추가하면 좋습니다.
                # (예: Booking.notification_sent == False)
            ).all()

            if upcoming_bookings:
                print(f"[{now.strftime('%H:%M')}] {len(upcoming_bookings)}개의 예약 알림 발송 시작... (타겟: {target_date_obj} {target_time_obj})")
                for booking in upcoming_bookings:
                    # (개선) 알림을 보냈다고 DB에 표시 (예: booking.notification_sent = True)
                    # db.session.commit()
                    
                    # 새 스레드에서 메일을 보내는 것이 좋습니다만, 일단은 동기식으로 호출합니다.
                    send_reminder_email(booking, app)
            
            # (디버깅용) 1분마다 로그가 찍히는지 확인
            else:
               print(f"[{now.strftime('%H:%M')}] 알림 대상 예약 없음. (타겟: {target_date_obj} {target_time_obj})")

        except Exception as e:
            print(f"[ERROR] 스케줄러 작업 중 오류 발생: {str(e)}")


# --- 3. 스케줄러에 작업 등록 ---
# 서버가 시작될 때 `app/__init__.py`의 `scheduler.start()`에 의해 이 작업이 자동 등록됩니다.
@scheduler.task('interval', id='check_bookings_job', minutes=1, misfire_grace_time=900)
def scheduled_job():
    """APScheduler가 1분마다 이 함수를 실행합니다."""
    check_upcoming_bookings()