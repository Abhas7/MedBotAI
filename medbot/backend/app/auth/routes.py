from flask import request, jsonify
from app.auth import auth_bp
from app.auth.utils import hash_password, verify_password, create_token, token_required
from app.db.supabase import SupabaseDB

@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"message": "Email and password are required fields."}), 400
        
    try:
        # Check if user already exists
        existing_user = SupabaseDB.get_user_by_email(email)
        if existing_user:
            return jsonify({"message": "User with this email already exists."}), 400
            
        # Hash password and create user
        hashed_password = hash_password(password)
        new_user = SupabaseDB.create_user(email, hashed_password)
        
        if not new_user:
            return jsonify({"message": "Failed to create user. Please try again."}), 500
            
        return jsonify({
            "message": "User registered successfully.",
            "user": {
                "id": new_user["id"],
                "email": new_user["email"]
            }
        }), 201
        
    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return a JWT access token."""
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"message": "Email and password are required fields."}), 400
        
    try:
        user = SupabaseDB.get_user_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            return jsonify({"message": "Invalid email or password."}), 401
            
        # Generate token
        token = create_token(user["id"])
        
        return jsonify({
            "message": "Login successful.",
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"]
            }
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500

@auth_bp.route("/me", methods=["GET"])
@token_required
def get_me(current_user_id):
    """Retrieve logged-in user profile details."""
    try:
        user = SupabaseDB.get_user_by_id(current_user_id)
        if not user:
            return jsonify({"message": "User profile not found."}), 404
            
        return jsonify({
            "id": user["id"],
            "email": user["email"],
            "created_at": user["created_at"]
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500
