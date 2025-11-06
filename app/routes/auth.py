from flask import Blueprint, request, jsonify
from app import db, bcrypt 
from app.models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route("/register", methods=['POST'])
def register():
    data = request.get_json()
    user_id = data.get('id')
    username = data.get('username')
    password = data.get('password')

    # 프론트엔드 유효성 검사와 동일하게 백엔드에서도 검증
    if not all([user_id, username, password]):
        return jsonify({"error": "학번, 이름, 비밀번호는 필수입니다."}), 400

    if len(user_id) != 8:
        return jsonify({"error": "학번은 8자리여야 합니다."}), 400

    
    if User.query.filter_by(id=user_id).first():
        return jsonify({"error": "이미 가입된 학번입니다."}), 409 

    
    try:
        
        new_user = User(id=user_id, username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": f"'{username}'님, 회원가입이 완료되었습니다."}), 201 

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

    
    if not user or not user.check_password(password):
        return jsonify({"error": "학번이 존재하지 않거나 비밀번호가 올바르지 않습니다."}), 401

    
    access_token = create_access_token(identity=user.id)

   
    return jsonify({
        "message": f"{user.username}님, 환영합니다!",
        "token": access_token, 
        "user_id": user.id,
        "username": user.username
    }), 200

@auth_bp.route("/my-profile", methods=['GET'])
@jwt_required() 
def my_profile():
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id).first()

    if not user:
        return jsonify({"error": "사용자를 찾을 수 없습니다."}), 404

    
    return jsonify({
        "id": user.id,
        "username": user.username
    }), 200