import datetime
import jwt
import bcrypt
from functools import wraps
from flask import request, jsonify
from app.config import Config

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password by checking against hashed value."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def create_token(user_id: str) -> str:
    """Generate JWT access token for user_id with 24 hours expiry."""
    try:
        payload = {
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
            'iat': datetime.datetime.now(datetime.timezone.utc),
            'sub': user_id
        }
        return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')
    except Exception as e:
        raise ValueError(f"Token generation failed: {str(e)}")

def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        return {"user_id": payload["sub"]}
    except jwt.ExpiredSignatureError:
        raise ValueError("Token signature has expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid authentication token. Please log in again.")

def token_required(f):
    """Decorator to require JWT authentication on endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                
        if not token:
            return jsonify({"message": "Authorization token is missing."}), 401
            
        try:
            data = decode_token(token)
            current_user_id = data["user_id"]
        except Exception as e:
            return jsonify({"message": str(e)}), 401
            
        return f(current_user_id, *args, **kwargs)
        
    return decorated
