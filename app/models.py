"""
Data models and schemas for the application.
"""
from flask_restx import fields as restx_fields
from marshmallow import Schema, fields as ma_fields, validate

# Marshmallow schema for validation
class CharacterSchema(Schema):
    """Schema for validating character data."""
    id = ma_fields.Int(required=True)
    name = ma_fields.Str(required=True)
    house = ma_fields.Str(required=True)
    age = ma_fields.Int(required=True, validate=validate.Range(min=0))
    role = ma_fields.Str(required=True)

# Function to create Swagger documentation model
def get_character_model(api):
    """Create Flask-RESTX model for Swagger documentation."""
    return api.model('Character', {
        'id': restx_fields.Integer(required=True, description='Character unique identifier'),
        'name': restx_fields.String(required=True, description='Character name'),
        'house': restx_fields.String(required=True, description='House name'),
        'age': restx_fields.Integer(required=True, description='Character age'),
        'role': restx_fields.String(required=True, description='Character role')
    })