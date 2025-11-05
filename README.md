
**INHA NEXT CAMPUS CHALLENGE_INHA:DECOM_BACK**

> 인하대학교 캠퍼스 시설 (스터디룸, 체육시설 등) 예약을 위한 백엔드 API 서버

---

## 응용 프로그램에 대한 설명

INHA-DECOM_back은 인하대학교 학생들을 위한 캠퍼스 시설 예약 시스템의 백엔드 서버입니다. Flask 프레임워크를 기반으로 개발되었으며, 사용자 인증, 시설 목록 조회, 예약 생성 및 관리, GPS 기반 체크인, 자동 이메일 알림 등의 기능을 REST API로 제공합니다.

### 주요 기능

| 기능                         | 설명                                      |
| ---------------------------- | ----------------------------------------- |
| 사용자 인증  | 학번 기반 회원가입, 로그인, 프로필 조회를 제공합니다. (JWT 토큰 사용)    |
| 시설 및 예약 조회           | 전체 시설 목록, 특정 시설의 월별/일별 예약 현황, 특정 시간대 사용 가능 시설 조회를 지원합니다.|
| 예약 관리         | 신규 예약 생성, 나의 예약 내역 조회, 기존 예약 수정 및 취소 기능을 제공합니다. |
| GPS 기반 체크인          |사용자의 현재 GPS 위치와 예약한 시설의 좌표를 비교하여 일정 거리(50m) 이내일 경우에만 체크인을 허용합니다. (Geopy 라이브러리 사용)    |
| 자동 알림          | 스케줄러(APScheduler)가 1분마다 실행되며, 예약 시간 10분 전인 사용자에게 알림 이메일을 자동으로 발송합니다.       |
| 데이터베이스 관리          | seed.py 스크립트를 통해 초기 시설 데이터(이름, 위치, 카테고리, 좌표 등)를 일괄 등록할 수 있습니다.  |

---


## 팀 구성원

| 이름   | 이메일                     |                      
|--------|---------------------------|
| 강인태 | rkddlsxo12345@naver.com        
| 김동현 | seaweedtreepot@inha.edu   |
| 김태용 | ktyong1225@inha.edu  | 
| 오정우 | shfnskdl@naver.com  | 
| 이소현 | dlthgus15780@gmail.com  | 

---

## 기술 스택

Framework: Flask

Database: Flask-SQLAlchemy, Flask-Migrate 

Authentication: Flask-Bcrypt (비밀번호 해싱), Flask-JWT-Extended (토큰 인증)

API / CORS: Flask-CORS

Async & Scheduling: Flask-APScheduler (예약 알림 등 스케줄 작업)

Notifications: Flask-Mail (이메일 발송)

Utilities: Geopy (GPS 좌표 거리 계산)

### Backend
- **Flask**: 백엔드 서버

## 응용 프로그램 설치 및 실행 방법

### 1. 프로젝트 클론
```bash
git clone https://github.com/rkddlsxo/INHA-DECOM_back
cd INHA-DECOM_back
```

### 2. 가상환경 설정 및 실행
```bash
# Windows

python -m venv venv
venv\Scripts\activate

# macOS / Linux

python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 패키지 다운로드
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정 

```bash
# Windows (CMD)
set SECRET_KEY="<비밀키>"
set DATABASE_URI="mysql+pymysql://<유저>:<비밀번호>@<호스트>/<DB이름>"
set MAIL_USERNAME="<내Gmail@gmail.com>"
set MAIL_PASSWORD="<Gmail_16자리_앱_비밀번호>"

# macOS / Linux
export SECRET_KEY="<비밀키>"
export DATABASE_URI="mysql+pymysql://<유저>:<비밀번호>@<호스트>/<DB이름>"
export MAIL_USERNAME="<내Gmail@gmail.com>"
export MAIL_PASSWORD="<Gmail_16자리_앱_비밀번호>"
```

### 5. 데이터베이스 초기화

```bash
python seed.py
```


### 6. 실행
```bash
python run.py
```

서버는 기본적으로 http://localhost:5050 에서 실행됩니다.

### 5. 프론트엔드 설치 및 실행
프론트엔드 설치 및 실행 방법은 다음 저장소에서 확인하세요:

**🔗 [INHA:DECOM 프론트엔드 저장소](https://github.com/rkddlsxo/INHA-DECOM_front)**

---
**API 엔드포인트 주요 기능**

인증 (Auth)
POST /api/register: 회원가입

POST /api/login: 로그인 (JWT 토큰 발급)

GET /api/my-profile: 내 정보 조회 (토큰 필요)

시설 (Space)
GET /api/masters/spaces: 전체 시설 마스터 목록 조회

GET /api/availability/monthly: 특정 시설의 월별 예약 현황 (달력용)

GET /api/availability/daily: 특정 시설의 일별 예약 현황 (시간표용)

GET /api/spaces/available: 특정 날짜/시간에 예약 가능한 모든 시설 조회

예약 (Booking)
POST /api/bookings: 신규 예약 생성 (토큰 필요)

GET /api/bookings/my: 내 예약 목록 조회 (토큰 필요)

PATCH /api/bookings/<int:booking_id>/cancel: 예약 취소 (토큰 필요)

PATCH /api/bookings/<int:booking_id>: 예약 정보 수정 (토큰 필요)

POST /api/check-in: GPS 기반 체크인 (토큰, space_id, lat, lng 필요)

---
## 주의 사항
### 보안
환경 변수: config.py에서 SECRET_KEY, DATABASE_URI, MAIL_USERNAME, MAIL_PASSWORD는 하드코딩 대신 반드시 환경 변수로 관리해야 합니다.
Gmail 앱 비밀번호: MAIL_PASSWORD는 실제 Gmail 비밀번호가 아닌, 'Google 계정 관리'에서 발급받은 16자리 앱 비밀번호를 사용해야 합니다.

### 시스템 요구사항
백엔드 API 서버가 먼저 실행되어 있어야 프론트엔드에서 정상적으로 통신할 수 있습니다.
데이터베이스 (예: MySQL)가 실행 중이어야 합니다.
이메일 알림 및 체크인 기능을 위해 인터넷 연결이 필요합니다.

---

## 라이선스

### MIT 라이선스

```
MIT License

Copyright (c) 2024 MailPilot AI Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 기타 오픈소스 라이선스

이 프로젝트는 다음 오픈소스 라이브러리들을 사용합니다:

**Backend**

- **Flask**: BSD License

**Frontend**

자세한 프론트엔드 라이선스 정보는 [프론트엔드 저장소](https://github.com/rkddlsxo/INHA-DECOM_front)를 참조하세요:



각 라이브러리의 전체 라이선스 텍스트는 해당 프로젝트의 공식 저장소에서 확인할 수 있습니다.
