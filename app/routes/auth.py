from flask import Blueprint, request, jsonify
from app import db, bcrypt  
from app.models import User 


auth_bp = Blueprint('auth', __name__, url_prefix='/api')

#회원가입
@auth_bp.route("/register", methods=['POST'])
def register():
    data = request.get_json()
    user_id = data.get('id')
    username = data.get('username')
    password = data.get('password')

    if not all([user_id, username, password]):
        return jsonify({"error": "학번, 이름, 비밀번호는 필수입니다."}), 400

    if len(user_id) != 8:
        return jsonify({"error": "학번은 8자리여야 합니다."}), 400

    if User.query.filter_by(id=user_id).first() or User.query.filter_by(username=username).first():
        return jsonify({"error": "이미 가입된 학번 또는 사용 중인 이름입니다."}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    new_user = User(id=user_id, username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": f"'{username}'님, 회원가입이 완료되었습니다."}), 201


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
        return jsonify({"error": "학번이 존재하지 않거나 비밀번호가 올바르지 않습니다."}), 401 # Unauthorized

    return jsonify({
        "message": f"{user.username}님, 환영합니다!",
        "user_id": user.id,
        "username": user.username
    }), 200 