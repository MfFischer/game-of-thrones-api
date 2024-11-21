"""
Test data models and schemas.
"""
from app.models import (
    CharacterSchema,
    CharacterCreateSchema,
    get_character_model,
    get_character_create_model
)
from flask_restx import Api
from flask import Flask


def test_character_schema_validation():
    """Test character schema validation."""
    schema = CharacterSchema()

    # Valid data
    data = {
        "id": 1,
        "name": "Test Character",
        "house": "Test House",
        "age": 25,
        "role": "Test Role"
    }
    errors = schema.validate(data)
    assert not errors

    # Invalid data (negative age)
    data["age"] = -1
    errors = schema.validate(data)
    assert errors
    assert "age" in errors


def test_character_create_schema_validation():
    """Test character creation schema validation."""
    schema = CharacterCreateSchema()

    # Valid data
    data = {
        "name": "Test Character",
        "house": "Test House",
        "age": 25,
        "role": "Test Role"
    }
    errors = schema.validate(data)
    assert not errors

def test_get_character_model():
    """Test Swagger model generation."""
    app = Flask(__name__)
    api = Api(app)

    model = get_character_model(api)

    assert "id" in model
    assert "name" in model
    assert "house" in model
    assert "age" in model
    assert "role" in model

    # Check field types
    assert model["id"].readonly
    assert model["name"].required
    assert model["age"].required


def test_get_character_create_model():
    """Test character creation model generation."""
    app = Flask(__name__)
    api = Api(app)

    model = get_character_create_model(api)

    # Verify model structure
    assert 'name' in model
    assert 'house' in model
    assert 'age' in model
    assert 'role' in model

    # Verify 'id' is not in create model
    assert 'id' not in model

    # Verify field requirements
    assert model['name'].required
    assert model['house'].required
    assert model['age'].required
    assert model['role'].required

    # Verify descriptions
    assert model['name'].description == 'Character name'
    assert model['house'].description == 'House name'
    assert model['age'].description == 'Character age'
    assert model['role'].description == 'Character role'




