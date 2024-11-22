# auth.py
from functools import wraps
from flask import request
import jwt
from datetime import datetime, timedelta

# In-memory user storage (in production, this would be a database)
USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",  # In production, this should be hashed
        "role": "admin"
    }
}

# Configuration
JWT_SECRET_KEY = 'your-secret-key'  # In production, use a secure secret key
JWT_EXPIRATION_DELTA = timedelta(hours=1)


def register_user(username, password, role='user'):
    """Register a new user."""
    if username in USERS:
        return False, "Username already exists"

    USERS[username] = {
        "username": username,
        "password": password,  # In production, this should be hashed
        "role": role
    }
    return True, "User registered successfully"


def generate_token(username):
    """Generate a JWT token for a user."""
    payload = {
        'username': username,
        'role': USERS[username]['role'],
        'exp': datetime.now() + JWT_EXPIRATION_DELTA
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')


def verify_token(token):
    """Verify a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """Decorator to protect routes with JWT authentication."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return {'message': 'Invalid token format'}, 401

        if not token:
            return {'message': 'Token is missing'}, 401

        payload = verify_token(token)
        if not payload:
            return {'message': 'Invalid or expired token'}, 401

        # Add user info to request context
        request.current_user = payload
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Decorator to restrict routes to admin users only."""

    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.current_user['role'] != 'admin':
            return {'message': 'Admin privileges required'}, 403
        return f(*args, **kwargs)

    return decorated