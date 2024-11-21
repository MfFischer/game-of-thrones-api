"""
Data models and schemas for the application.
"""
from marshmallow import Schema, fields as ma_fields, validate
from flask_restx import fields

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