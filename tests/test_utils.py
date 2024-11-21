"""
Test utility functions.
"""
import json
import app.utils
from pathlib import Path
from app.utils import (
    load_characters,
    save_characters,
    get_data_file_path,
    get_default_characters
)

def test_get_data_file_path():
    """Test getting data file path."""
    path = get_data_file_path()
    assert isinstance(path, Path)
    assert path.name == 'characters.json'
    assert 'data' in str(path)

def test_get_default_characters():
    """Test getting default character data."""
    characters = get_default_characters()
    assert isinstance(characters, list)
    assert len(characters) > 0
    assert all(isinstance(char, dict) for char in characters)
    assert all(required in char for char in characters
              for required in ['id', 'name', 'house', 'age', 'role'])

def test_load_characters_file_not_exists(tmp_path):
    """Test loading characters when file doesn't exist."""
    # Temporarily change data file path
    original_path = app.utils.get_data_file_path
    app.utils.get_data_file_path = lambda: tmp_path / 'characters.json'

    try:
        characters = load_characters()
        assert isinstance(characters, list)
        assert len(characters) > 0
        assert all(isinstance(char, dict) for char in characters)

        # Check if file was created
        assert (tmp_path / 'characters.json').exists()
    finally:
        # Restore original path function
        app.utils.get_data_file_path = original_path

def test_save_characters(tmp_path):
    """Test saving characters to file."""
    # Test data
    characters = get_default_characters()

    # Temporarily change data file path
    original_path = app.utils.get_data_file_path
    test_file = tmp_path / 'test_characters.json'
    app.utils.get_data_file_path = lambda: test_file

    try:
        # Save characters
        save_characters(characters)

        # Verify file exists and content is correct
        assert test_file.exists()
        with open(test_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            assert saved_data == characters
    finally:
        # Restore original path function
        app.utils.get_data_file_path = original_path

def test_load_characters_invalid_json(tmp_path):
    """Test loading characters with invalid JSON."""
    # Create invalid JSON file
    test_file = tmp_path / 'invalid_characters.json'
    test_file.write_text('invalid json')

    # Temporarily change data file path
    original_path = app.utils.get_data_file_path
    app.utils.get_data_file_path = lambda: test_file

    try:
        characters = load_characters()
        assert isinstance(characters, list)
        assert len(characters) == len(get_default_characters())
        assert characters == get_default_characters()  # Should return default data
    finally:
        # Restore original path function
        app.utils.get_data_file_path = original_path

def test_load_characters_permission_error(tmp_path, mocker):
    """Test loading characters with permission error."""
    mocker.patch('builtins.open', side_effect=PermissionError("Permission denied"))

    characters = load_characters()
    assert isinstance(characters, list)
    assert len(characters) == len(get_default_characters())
    assert characters == get_default_characters()


def test_save_characters_error_handling(tmp_path, mocker):
    """Test error handling in save_characters function."""
    # Mock open to raise an error
    mocker.patch('builtins.open', side_effect=PermissionError("Permission denied"))

    # Should not raise an exception, just print error
    save_characters([{"id": 1, "name": "Test"}])


def test_save_characters_directory_creation(tmp_path):
    """Test directory creation when saving characters."""
    # Create a deep nested path
    deep_path = tmp_path / 'deep' / 'nested' / 'path'
    test_file = deep_path / 'characters.json'

    # Mock the get_data_file_path function
    import app.utils
    original_path = app.utils.get_data_file_path
    app.utils.get_data_file_path = lambda: test_file

    try:
        # Test data
        test_data = [{"id": 1, "name": "Test", "house": "Test", "age": 25, "role": "Test"}]

        # Save characters
        save_characters(test_data)

        # Verify file and directories were created
        assert deep_path.exists(), "Deep directory structure was not created"
        assert test_file.exists(), "JSON file was not created"

        # Verify file contents
        with open(test_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            assert saved_data == test_data, "Saved data doesn't match test data"

    finally:
        # Restore original function
        app.utils.get_data_file_path = original_path