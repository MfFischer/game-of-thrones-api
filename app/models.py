"""
Data models and schemas for the application.
"""
from marshmallow import Schema, fields as ma_fields, validate
from flask_restx import fields

# Character Schemas
class CharacterSchema(Schema):
    """Schema for validating complete character data (including ID)."""
    id = ma_fields.Int()  # Not required for creation
    name = ma_fields.Str(required=True, validate=validate.Length(min=1))
    house = ma_fields.Str(required=True)
    age = ma_fields.Int(required=True, validate=validate.Range(min=0))
    role = ma_fields.Str(required=True)

class CharacterCreateSchema(Schema):
    """Schema for validating character creation (without ID)."""
    name = ma_fields.Str(required=True, validate=validate.Length(min=1))
    house = ma_fields.Str(required=True)
    age = ma_fields.Int(required=True, validate=validate.Range(min=0))
    role = ma_fields.Str(required=True)

# Auth Schemas
class LoginSchema(Schema):
    """Schema for validating login credentials."""
    username = ma_fields.Str(required=True, validate=validate.Length(min=1))
    password = ma_fields.Str(required=True, validate=validate.Length(min=1))

def get_character_model(api):
    """Create Flask-RESTX model for Swagger documentation."""
    return api.model('Character', {
        'id': fields.Integer(readonly=True, description='Character unique identifier'),
        'name': fields.String(required=True, description='Character name'),
        'house': fields.String(required=True, description='House name'),
        'age': fields.Integer(required=True, description='Character age'),
        'role': fields.String(required=True, description='Character role')
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
        'role': fields.String(description='User role (optional)', default='user')
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