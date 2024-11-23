"""
Data models and schemas for the application.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields as ma_fields, validate
from flask_restx import fields
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy
db = SQLAlchemy()

# Database Models
class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Check if the provided password matches the hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class CharacterModel(db.Model):
    """Database model for storing character data"""
    __tablename__ = 'characters'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    house = db.Column(db.String(100), nullable=False, index=True)
    age = db.Column(db.Integer, nullable=False, index=True)
    role = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'house': self.house,
            'age': self.age,
            'role': self.role
        }

# Marshmallow Schemas
class CharacterSchema(Schema):
    """Schema for validating complete character data (including ID)."""
    id = ma_fields.Int(dump_only=True)  # Read-only field
    name = ma_fields.Str(required=True, validate=validate.Length(min=1))
    house = ma_fields.Str(required=True)
    age = ma_fields.Int(required=True, validate=validate.Range(min=0))
    role = ma_fields.Str(required=True)
    created_at = ma_fields.DateTime(dump_only=True)
    updated_at = ma_fields.DateTime(dump_only=True)

class CharacterCreateSchema(Schema):
    """Schema for validating character creation (without ID)."""
    name = ma_fields.Str(required=True, validate=validate.Length(min=1))
    house = ma_fields.Str(required=True)
    age = ma_fields.Int(required=True, validate=validate.Range(min=0))
    role = ma_fields.Str(required=True)

class LoginSchema(Schema):
    """Schema for validating login credentials."""
    username = ma_fields.Str(required=True, validate=validate.Length(min=1))
    password = ma_fields.Str(required=True, validate=validate.Length(min=1))

class UserSchema(Schema):
    """Schema for user data"""
    id = ma_fields.Int(dump_only=True)
    username = ma_fields.Str(required=True, validate=validate.Length(min=3))
    role = ma_fields.Str()
    created_at = ma_fields.DateTime(dump_only=True)

# Flask-RESTX Models
def get_character_model(api):
    """Create Flask-RESTX model for Swagger documentation."""
    return api.model('Character', {
        'id': fields.Integer(readonly=True, description='Character unique identifier'),
        'name': fields.String(required=True, description='Character name'),
        'house': fields.String(required=True, description='House name'),
        'age': fields.Integer(required=True, description='Character age'),
        'role': fields.String(required=True, description='Character role'),
        'created_at': fields.DateTime(readonly=True, description='Creation timestamp'),
        'updated_at': fields.DateTime(readonly=True, description='Last update timestamp')
    })

def get_character_create_model(api):
    """Create Flask-RESTX model for character creation."""
    return api.model('CharacterCreate', {
        'name': fields.String(required=True, description='Character name'),
        'house': fields.String(required=True, description='House name'),
        'age': fields.Integer(required=True, description='Character age'),
        'role': fields.String(required=True, description='Character role')
    })

def get_auth_models(api):
    """Create Flask-RESTX models for authentication."""
    login_input = api.model('LoginInput', {
        'username': fields.String(required=True, description='Username'),
        'password': fields.String(required=True, description='Password')
    })

    register_input = api.model('RegisterInput', {
        'username': fields.String(required=True, description='Username'),
        'password': fields.String(required=True, description='Password'),
        'role': fields.String(description='User role (optional)', default='user',
                            enum=['user', 'admin'])
    })

    token_response = api.model('TokenResponse', {
        'token': fields.String(description='JWT access token'),
        'type': fields.String(description='Token type', default='Bearer'),
        'expires_in': fields.Integer(description='Token expiration time in seconds')
    })

    error_response = api.model('ErrorResponse', {
        'message': fields.String(description='Error message'),
        'status': fields.Integer(description='HTTP status code')
    })

    return {
        'login_input': login_input,
        'register_input': register_input,
        'token_response': token_response,
        'error_response': error_response
    }