"""
Test configuration and fixtures.
"""
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from app import create_app

@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    return app

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def sample_character():
    """Return a sample character for testing."""
    return {
        "name": "Test Character",
        "house": "Test House",
        "age": 25,
        "role": "Test Role"
    }

@pytest.fixture
def mock_characters():
    """Return a list of mock characters for testing."""
    return [
        {
            "id": 1,
            "name": "Jon Snow",
            "house": "House Stark",  # Test house name normalization
            "age": 25,
            "role": "Lord Commander"
        },
        {
            "id": 2,
            "name": "Daenerys Targaryen",
            "house": "Targaryen",  # Without 'House' prefix
            "age": 24,
            "role": "Queen"
        }
    ]