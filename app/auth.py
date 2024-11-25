from functools import wraps
from flask import request, current_app
import jwt
from datetime import datetime, timedelta, timezone
from .models import User


def generate_token(username):
    """Generate a JWT token for a user."""
    try:
        # Get user from database
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User not found: {username}")
            raise ValueError('User not found')

        # Create token with UTC timestamps
        now = datetime.now(timezone.utc)
        payload = {
            'username': username,
            'role': user.role,
            'exp': now + timedelta(hours=1),  # Expiration
            'iat': now,  # Issued at
            'nbf': now  # Not valid before
        }

        # Generate token
        token = jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )

        print(f"Generated token for user {username} at {now}")
        return token

    except Exception as e:
        print(f"Error generating token: {str(e)}")
        raise


def verify_token(token):
    """Verify a JWT token."""
    try:
        print(f"Verifying token: {token[:20]}...")

        # Decode with clock skew tolerance
        payload = jwt.decode(
            token,
            current_app.config.get('SECRET_KEY'),
            algorithms=['HS256'],
            # Allow 30 seconds of clock skew
            leeway=timedelta(seconds=30)
        )

        print(f"Token decoded successfully. Payload: {payload}")

        # Verify user exists
        user = User.query.filter_by(username=payload.get('username')).first()
        if not user:
            print(f"User from token not found: {payload.get('username')}")
            return None

        print(f"Token verified for user: {user.username}")
        return payload

    except jwt.ExpiredSignatureError as e:
        print(f"Token expired: {str(e)}")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token error: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error during token verification: {str(e)}")
        return None


def token_required(f):
    """Decorator to protect routes with JWT authentication."""

    @wraps(f)
    def decorated(*args, **kwargs):
        print("Starting token validation...")

        # Get token from header
        token = None
        auth_header = request.headers.get('Authorization')
        print(f"Authorization header: {auth_header}")

        if not auth_header:
            print("No Authorization header found")
            return {'message': 'Token is missing', 'status': 401}, 401

        if not auth_header.startswith('Bearer '):
            print("Invalid Authorization header format")
            return {'message': 'Invalid token format', 'status': 401}, 401

        try:
            token = auth_header.split(' ')[1]
            print(f"Extracted token: {token[:20]}...")

            # Verify token
            payload = verify_token(token)
            if not payload:
                print("Token verification failed")
                return {'message': 'Invalid token', 'status': 401}, 401

            # Get user from database
            current_user = User.query.filter_by(username=payload['username']).first()
            if not current_user:
                print(f"User not found in database: {payload['username']}")
                return {'message': 'User not found', 'status': 401}, 401

            print(f"Token validated successfully for user: {current_user.username}")
            request.current_user = current_user
            return f(*args, **kwargs)

        except Exception as e:
            print(f"Error in token_required decorator: {str(e)}")
            return {'message': f'Token validation failed: {str(e)}', 'status': 401}, 401

    return decorated


def admin_required(f):
    """Decorator to require admin role."""

    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.current_user.role != 'admin':
            return {'message': 'Admin privileges required', 'status': 403}, 403
        return f(*args, **kwargs)

    return decorated

def init_app(app):
    """Initialize authentication module with app config."""
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'your-secret-key-here'  # Default for development
        print("WARNING: Using default secret key")