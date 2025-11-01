from app import create_app, db
from app.models import Space

# 1. Flask 앱 컨텍스트를 로드합니다.
#    이렇게 해야 db 객체를 스크립트에서 사용할 수 있습니다.
app = create_app()

with app.app_context():
    # 2. 중복 방지: '해동 스터디룸 A'가 이미 있는지 확인
    existing_space = Space.query.filter_by(name='해동 스터디룸 A').first()
    
    if existing_space:
        print("INFO: '해동 스터디룸 A'가 이미 존재합니다. 데이터를 추가하지 않습니다.")
    else:
        print("INFO: 테스트 장소 데이터를 추가합니다...")
        
        # 3. 요청하신 5개의 스터디룸 데이터 생성
        #    (category, subCategory 등은 PlaceFocusSelectPage.jsx 등을 참고하여 설정)
        spaces_to_add = [
            Space(
                name='해동 스터디룸 A',
                category='스터디룸',
                subCategory='해동 스터디룸',
                location='해동B 101호',
                capacity=4
            ),
            Space(
                name='해동 스터디룸 B',
                category='스터디룸',
                subCategory='해동 스터디룸',
                location='해동B 102호',
                capacity=4
            ),
            Space(
                name='해동 스터디룸 C',
                category='스터디룸',
                subCategory='해동 스터디룸',
                location='해동B 103호',
                capacity=6
            ),
            Space(
                name='해동 스터디룸 D',
                category='스터디룸',
                subCategory='해동 스터디룸',
                location='해동B 104호',
                capacity=6
            ),
            Space(
                name='해동 스터디룸 E',
                category='스터디룸',
                subCategory='해동 스터디룸',
                location='해동B 105호',
                capacity=2
            )
        ]
        
        # 4. 세션에 추가하고 DB에 커밋(저장)
        try:
            db.session.add_all(spaces_to_add)
            db.session.commit()
            print("SUCCESS: 5개의 해동 스터디룸이 성공적으로 추가되었습니다.")
        except Exception as e:
            db.session.rollback()
            print(f"ERROR: 데이터 추가 중 오류 발생 - {e}")

print("INFO: 스크립트가 종료되었습니다.")