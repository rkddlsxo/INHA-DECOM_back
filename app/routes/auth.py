from flask import Blueprint, request, jsonify
from app import db, bcrypt
from app.models import User
# ⭐️ 1. flask_jwt_extended에서 필요한 함수 2개 import
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

# ... (회원가입 /register 코드는 그대로 둡니다) ...

#로그인
@auth_bp.route("/login", methods=['POST'])
def login():
    """User login route."""
    data = request.get_json()
    user_id = data.get('id')
    password = data.get('password')

    if not all([user_id, password]):
        return jsonify({"error": "학번과 비밀번호를 모두 입력해주세요."}), 400

    user = User.query.filter_by(id=user_id).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "학번이 존재하지 않거나 비밀번호가 올바르지 않습니다."}), 401

    # ⭐️ 2. 로그인 성공 시, user.id(학번)를 기준으로 토큰 생성
    access_token = create_access_token(identity=user.id)

    # ⭐️ 3. 프론트엔드로 토큰을 "token"이라는 키에 담아 전달
    return jsonify({
        "message": f"{user.username}님, 환영합니다!",
        "token": access_token, # ⭐️ "token" 키 추가
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