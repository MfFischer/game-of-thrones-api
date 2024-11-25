"""
Comprehensive test suite for data models and schemas.
"""
import pytest
from datetime import datetime
from flask import Flask
from flask_restx import Api
from marshmallow import ValidationError
from werkzeug.security import check_password_hash

from app.models import (
    db, User, CharacterModel,
    CharacterSchema, CharacterCreateSchema, LoginSchema, UserSchema,
    get_character_model, get_character_create_model, get_auth_models
)

@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True

    with app.app_context():
        db.init_app(app)
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def api(app):
    """Create Flask-RESTX API instance."""
    return Api(app)

# Database Model Tests
def test_user_model(app):
    """Test User model creation and password handling."""
    with app.app_context():
        # Test user creation
        user = User(username='testuser', role='user')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()

        # Test password verification
        assert user.check_password('testpass')
        assert not user.check_password('wrongpass')

        # Test unique username constraint
        duplicate_user = User(username='testuser', role='user')
        duplicate_user.set_password('testpass')
        db.session.add(duplicate_user)
        with pytest.raises(Exception):  # SQLAlchemy will raise an error
            db.session.commit()

def test_user_model_methods(app):
    """Test User model methods and properties."""
    with app.app_context():
        user = User(username='testuser', role='user')
        user.set_password('testpass')

        # Test repr
        assert str(user) == '<User testuser>'

        # Test password handling
        assert user.password_hash != 'testpass'  # Password should be hashed
        assert user.check_password('testpass')

        # Test null password
        user.password_hash = None
        assert not user.check_password('testpass')

def test_character_model(app):
    """Test CharacterModel creation and methods."""
    with app.app_context():
        # Test character creation
        character = CharacterModel(
            name='Test Character',
            house='Test House',
            age=25,
            role='Test Role'
        )
        db.session.add(character)
        db.session.commit()

        # Test to_dict method
        char_dict = character.to_dict()
        assert char_dict['name'] == 'Test Character'
        assert char_dict['house'] == 'Test House'
        assert char_dict['age'] == 25
        assert char_dict['role'] == 'Test Role'
        assert 'id' in char_dict

        # Test automatic timestamps
        assert isinstance(character.created_at, datetime)
        assert isinstance(character.updated_at, datetime)

# Schema Tests
def test_character_schema_validation():
    """Test CharacterSchema validation."""
    schema = CharacterSchema()

    # Valid data
    valid_data = {
        "name": "Test Character",
        "house": "Test House",
        "age": 25,
        "role": "Test Role"
    }
    result = schema.load(valid_data)
    assert result['name'] == valid_data['name']

    # Test required fields
    invalid_data = {"name": "Test Character"}  # Missing required fields
    with pytest.raises(ValidationError) as exc:
        schema.load(invalid_data)
    assert 'house' in exc.value.messages
    assert 'age' in exc.value.messages
    assert 'role' in exc.value.messages

    # Test age validation
    invalid_age = valid_data.copy()
    invalid_age['age'] = -1
    with pytest.raises(ValidationError) as exc:
        schema.load(invalid_age)
    assert 'age' in exc.value.messages

    # Test name validation
    invalid_name = valid_data.copy()
    invalid_name['name'] = ""
    with pytest.raises(ValidationError) as exc:
        schema.load(invalid_name)
    assert 'name' in exc.value.messages


def test_login_schema():
    """Test LoginSchema validation."""
    schema = LoginSchema()

    # Valid data
    valid_data = {
        "username": "testuser",
        "password": "testpass"
    }
    result = schema.load(valid_data)
    assert result == valid_data

    # Test required fields
    invalid_data = {"username": "testuser"}  # Missing password
    with pytest.raises(ValidationError) as exc:
        schema.load(invalid_data)
    assert 'password' in exc.value.messages

def test_user_schema():
    """Test UserSchema validation."""
    schema = UserSchema()

    # Valid data
    valid_data = {
        "username": "testuser",
        "role": "user"
    }
    result = schema.load(valid_data)
    assert result == valid_data

    # Test username validation
    invalid_data = {"username": "ab", "role": "user"}  # Username too short
    with pytest.raises(ValidationError) as exc:
        schema.load(invalid_data)
    assert 'username' in exc.value.messages

# Flask-RESTX Model Tests
def test_get_character_model(api):
    """Test character Swagger model generation."""
    model = get_character_model(api)

    # Verify required fields
    assert all(field in model for field in [
        'id', 'name', 'house', 'age', 'role', 'created_at', 'updated_at'
    ])

    # Verify field properties
    assert model['id'].readonly
    assert model['created_at'].readonly
    assert model['updated_at'].readonly
    assert model['name'].required
    assert model['house'].required
    assert model['age'].required
    assert model['role'].required

def test_get_character_create_model(api):
    """Test character creation Swagger model."""
    model = get_character_create_model(api)

    # Verify field presence
    assert all(field in model for field in ['name', 'house', 'age', 'role'])
    assert 'id' not in model
    assert 'created_at' not in model
    assert 'updated_at' not in model

    # Verify field requirements
    for field in ['name', 'house', 'age', 'role']:
        assert model[field].required
        assert model[field].description

def test_get_auth_models(api):
    """Test authentication Swagger models."""
    auth_models = get_auth_models(api)

    # Verify all models are present
    assert all(model in auth_models for model in [
        'login_input', 'register_input', 'token_response', 'error_response'
    ])

    # Test login input model
    login_model = auth_models['login_input']
    assert 'username' in login_model
    assert 'password' in login_model
    assert login_model['username'].required
    assert login_model['password'].required

    # Test register input model
    register_model = auth_models['register_input']
    assert 'username' in register_model
    assert 'password' in register_model
    assert 'role' in register_model
    assert register_model['role'].enum == ['user', 'admin']
    assert register_model['role'].default == 'user'

    # Test token response model
    token_model = auth_models['token_response']
    assert all(field in token_model for field in ['token', 'type', 'expires_in'])
    assert token_model['type'].default == 'Bearer'

    # Test error response model
    error_model = auth_models['error_response']
    assert 'message' in error_model
    assert 'status' in error_model