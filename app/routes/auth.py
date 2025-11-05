from flask import Blueprint, request, jsonify
from app import db, bcrypt # bcrypt는 login 로직에서 사용되지 않지만, 만약을 위해 유지 (혹은 제거)
from app.models import User
# [수정] flask_jwt_extended import는 유지
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route("/register", methods=['POST'])
def register():
    data = request.get_json()
    user_id = data.get('id')
    username = data.get('username')
    password = data.get('password')

    # 1. 프론트엔드 유효성 검사와 동일하게 백엔드에서도 검증
    if not all([user_id, username, password]):
        return jsonify({"error": "학번, 이름, 비밀번호는 필수입니다."}), 400

    if len(user_id) != 8:
        return jsonify({"error": "학번은 8자리여야 합니다."}), 400

    # 2. 이미 존재하는 사용자인지 확인 (id 또는 username)
    if User.query.filter_by(id=user_id).first():
        return jsonify({"error": "이미 가입된 학번입니다."}), 409 # 409: Conflict

    # [수정] 이름(username) 중복 검사 로직 삭제
    # if User.query.filter_by(username=username).first():
    #     return jsonify({"error": "이미 사용 중인 이름입니다."}), 409

    # [수정] 비밀번호 암호화 로직 삭제 (모델의 __init__이 담당)
    # hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # 4. 새 사용자 객체를 생성하여 DB에 저장
    try:
        # [수정] 평문 password를 전달
        new_user = User(id=user_id, username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": f"'{username}'님, 회원가입이 완료되었습니다."}), 201 # 201: Created

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "DB 저장 중 오류가 발생했습니다.", "details": str(e)}), 500
    
    
@auth_bp.route("/login", methods=['POST'])
def login():
    """User login route."""
    data = request.get_json()
    user_id = data.get('id')
    password = data.get('password')

    if not all([user_id, password]):
        return jsonify({"error": "학번과 비밀번호를 모두 입력해주세요."}), 400

    user = User.query.filter_by(id=user_id).first()

    # [수정] bcrypt.check_password_hash 대신 user.check_password 메서드 사용
    if not user or not user.check_password(password):
        return jsonify({"error": "학번이 존재하지 않거나 비밀번호가 올바르지 않습니다."}), 401

    # 2. 로그인 성공 시, user.id(학번)를 기준으로 토큰 생성
    access_token = create_access_token(identity=user.id)

    # 3. 프론트엔드로 토큰을 "token"이라는 키에 담아 전달
    return jsonify({
        "message": f"{user.username}님, 환영합니다!",
        "token": access_token, # "token" 키 추가
        "user_id": user.id,
        "username": user.username
    }), 200

@auth_bp.route("/my-profile", methods=['GET'])
@jwt_required() #  1. 이 API는 JWT 토큰(출입증)이 '필수'임을 선언
def my_profile():
    #  2. 토큰에서 신분(identity)을 가져옴 (3단계에서 넣었던 user.id)
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id).first()

    if not user:
        return jsonify({"error": "사용자를 찾을 수 없습니다."}), 404

    #  3. 토큰 주인의 정보를 반환
    return jsonify({
        "id": user.id,
        "username": user.username
    }), 200