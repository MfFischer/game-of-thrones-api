"""
Test utility functions for the application.
"""
import pytest
from app.utils import get_default_characters, seed_default_characters
from app.models import db, CharacterModel

@pytest.fixture
def db_setup(app):
    """Setup database for testing."""
    with app.app_context():
        db.create_all()
        yield
        db.drop_all()

@pytest.fixture
def empty_database(app, db_setup):
    """Ensure database is empty before each test."""
    with app.app_context():
        CharacterModel.query.delete()
        db.session.commit()
        yield

def test_get_default_characters():
    """Test getting default character data."""
    characters = get_default_characters()

    # Test return type and length
    assert isinstance(characters, list)
    assert len(characters) == 2
    assert all(isinstance(char, dict) for char in characters)

    # Test data structure
    expected_fields = {'name', 'house', 'age', 'role'}
    for char in characters:
        assert set(char.keys()) == expected_fields

    # Test specific character data
    jon = next(char for char in characters if char['name'] == 'Jon Snow')
    assert jon == {
        'name': 'Jon Snow',
        'house': 'Stark',
        'age': 25,
        'role': "Lord Commander of the Night's Watch"
    }

    dany = next(char for char in characters if char['name'] == 'Daenerys Targaryen')
    assert dany == {
        'name': 'Daenerys Targaryen',
        'house': 'Targaryen',
        'age': 24,
        'role': "Queen of the Seven Kingdoms"
    }

def test_seed_default_characters_empty_db(app, empty_database):
    """Test seeding default characters into empty database."""
    with app.app_context():
        # Verify database is empty initially
        assert CharacterModel.query.count() == 0

        # Perform seeding
        seed_default_characters()

        # Verify correct number of characters
        characters = CharacterModel.query.all()
        assert len(characters) == 2

        # Verify Jon Snow's data
        jon = CharacterModel.query.filter_by(name='Jon Snow').first()
        assert jon is not None
        assert jon.house == 'Stark'
        assert jon.age == 25
        assert jon.role == "Lord Commander of the Night's Watch"

        # Verify Daenerys's data
        dany = CharacterModel.query.filter_by(name='Daenerys Targaryen').first()
        assert dany is not None
        assert dany.house == 'Targaryen'
        assert dany.age == 24
        assert dany.role == "Queen of the Seven Kingdoms"

def test_seed_default_characters_with_existing_data(app, empty_database, sample_character):
    """Test seeding when database already contains data."""
    with app.app_context():
        # Add a test character
        char = CharacterModel(**sample_character)
        db.session.add(char)
        db.session.commit()

        # Attempt seeding
        seed_default_characters()

        # Verify only original character exists
        characters = CharacterModel.query.all()
        assert len(characters) == 1
        assert characters[0].name == sample_character['name']
        assert characters[0].house == sample_character['house']
        assert characters[0].age == sample_character['age']
        assert characters[0].role == sample_character['role']

def test_seed_default_characters_error_handling(app, empty_database, mocker):
    """Test error handling during database seeding."""
    with app.app_context():
        # Mock db.session.commit to raise an exception
        mocker.patch.object(db.session, 'commit', side_effect=Exception("Database error"))

        # Attempt seeding
        seed_default_characters()

        # Verify database remains empty due to rollback
        assert CharacterModel.query.count() == 0

def test_seed_default_characters_duplicate_prevention(app, empty_database):
    """Test that seeding twice doesn't create duplicates."""
    with app.app_context():
        # Seed once
        seed_default_characters()
        first_count = CharacterModel.query.count()

        # Seed again
        seed_default_characters()
        second_count = CharacterModel.query.count()

        # Verify counts are the same
        assert first_count == second_count == 2

def test_default_characters_data_integrity():
    """Test that default character data meets all requirements."""
    characters = get_default_characters()

    for char in characters:
        # Verify all required fields are present and of correct type
        assert isinstance(char['name'], str)
        assert isinstance(char['house'], str)
        assert isinstance(char['age'], int)
        assert isinstance(char['role'], str)

        # Verify age is reasonable
        assert 0 < char['age'] < 150

        # Verify strings are not empty
        assert char['name'].strip()
        assert char['house'].strip()
        assert char['role'].strip()