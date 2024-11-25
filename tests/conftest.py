"""
Test configuration and fixtures.
"""
import sys
from pathlib import Path
from datetime import datetime, UTC

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from app import create_app
from app.models import db, User, CharacterModel
from app.auth import generate_token

@pytest.fixture(scope='session')
def app():
    """Create and configure a test application instance."""
    app = create_app('testing')  # Use testing configuration
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "test-secret-key"
    })

    # Create application context
    with app.app_context():
        # Create database tables
        db.create_all()
        yield app
        # Cleanup
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def session(app):
    """Create a new database session for a test."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        options = dict(bind=connection, binds={})
        session = db.create_scoped_session(options=options)

        db.session = session

        yield session

        transaction.rollback()
        connection.close()
        session.remove()

@pytest.fixture
def test_user(session):
    """Create a test user."""
    user = User(
        username='testuser',
        role='user'
    )
    user.set_password('testpass')
    session.add(user)
    session.commit()
    return user

@pytest.fixture
def admin_user(session):
    """Create an admin user."""
    user = User(
        username='admin',
        role='admin'
    )
    user.set_password('adminpass')
    session.add(user)
    session.commit()
    return user

@pytest.fixture
def auth_token(test_user):
    """Generate authentication token for test user."""
    return generate_token(test_user.username)

@pytest.fixture
def admin_token(admin_user):
    """Generate authentication token for admin user."""
    return generate_token(admin_user.username)

@pytest.fixture
def auth_headers(auth_token):
    """Create headers with authentication token."""
    return {'Authorization': f'Bearer {auth_token}'}

@pytest.fixture
def admin_headers(admin_token):
    """Create headers with admin authentication token."""
    return {
        'Authorization': f'Bearer {admin_token}',
        'Role': 'admin'
    }

@pytest.fixture
def sample_character():
    """Return a sample character for testing."""
    return {
        "name": "Test Character",
        "house": "Test House",
        "age": 25,
        "role": "Test Role",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }

@pytest.fixture
def db_character(session, sample_character):
    """Create a test character in the database."""
    character = CharacterModel(**sample_character)
    session.add(character)
    session.commit()
    return character

@pytest.fixture
def mock_characters(session):
    """Create a list of test characters in the database."""
    characters = [
        CharacterModel(
            name="Jon Snow",
            house="House Stark",
            age=25,
            role="Lord Commander",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        ),
        CharacterModel(
            name="Daenerys Targaryen",
            house="Targaryen",
            age=24,
            role="Queen",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
    ]

    for char in characters:
        session.add(char)
    session.commit()

    return characters