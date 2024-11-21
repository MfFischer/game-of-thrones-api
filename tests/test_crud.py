"""
Complete test suite for CRUD operations with corrected error message assertions.
"""
import json
from app.routes import normalize_house_name, generate_new_id


class TestCharacterRetrieval:
    """Tests for retrieving character data."""

    def test_get_characters(self, client, mock_characters, mocker):
        """Test getting all characters."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        response = client.get('/api/v1/characters/')
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data['status'] == 'success'
        assert len(data['characters']) == len(mock_characters)
        assert data['metadata']['total_records'] == len(mock_characters)
        assert 'filters_applied' in data
        assert 'sort_applied' in data

    def test_get_character_by_id(self, client, mock_characters, mocker):
        """Test getting a single character by ID."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        # Test existing character
        response = client.get('/api/v1/characters/1')
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['name'] == 'Jon Snow'

        # Test non-existent character
        response = client.get('/api/v1/characters/999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "doesn't exist" in data['message']


class TestCharacterCreation:
    """Tests for character creation."""

    def test_create_character_success(self, client, sample_character):
        """Test successful character creation."""
        response = client.post('/api/v1/characters/', json=sample_character)
        data = json.loads(response.data)

        assert response.status_code == 201
        assert data['name'] == sample_character['name']
        assert 'id' in data
        assert isinstance(data['id'], int)

    def test_create_character_validation(self, client):
        """Test character creation validation."""
        invalid_cases = [
            # Missing age
            {
                "name": "Test Character",
                "house": "Test House",
                "role": "Test Role"
            },
            # Missing name
            {
                "house": "Test House",
                "age": 25,
                "role": "Test Role"
            },
            # Invalid age
            {
                "name": "Test Character",
                "house": "Test House",
                "age": -1,
                "role": "Test Role"
            },
            # Empty name
            {
                "name": "",
                "house": "Test House",
                "age": 25,
                "role": "Test Role"
            }
        ]

        for invalid_data in invalid_cases:
            response = client.post('/api/v1/characters/', json=invalid_data)
            data = json.loads(response.data)
            assert response.status_code == 400
            assert 'errors' in data

    def test_create_character_invalid_format(self, client, sample_character):
        """Test character creation with invalid request formats."""
        # Test invalid content type (line 84)
        response = client.post(
            '/api/v1/characters/',
            data=json.dumps(sample_character),
            content_type=None  # This specifically targets line 84
        )
        assert response.status_code == 415
        data = json.loads(response.data)
        assert data[
                   'message'] == "Did not attempt to load JSON data because the request Content-Type was not 'application/json'."

        # Test malformed JSON (line 145)
        response = client.post(
            '/api/v1/characters/',
            data='{"invalid": json',  # Malformed JSON to trigger parse error
            content_type='application/json'
        )
        assert response.status_code == 400
        assert "could not understand" in response.get_data(as_text=True)

    def test_create_character_empty_payload(self, client):
        """Test character creation with empty payload."""
        response = client.post('/api/v1/characters/', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'errors' in data


class TestCharacterUpdate:
    """Tests for character update operations."""

    def test_update_character_success(self, client, mock_characters, mocker):
        """Test successful character update."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        update_data = {
            "name": "Updated Name",
            "house": "Updated House",
            "age": 30,
            "role": "Updated Role"
        }

        response = client.put('/api/v1/characters/1', json=update_data)
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data['name'] == "Updated Name"
        assert data['id'] == 1
        assert data['age'] == 30

    def test_update_character_validation(self, client, mock_characters, mocker):
        """Test character update validation."""
        mocker.patch('app.routes.CHARACTERS', mock_characters.copy())

        # Test missing required fields
        response = client.put(
            '/api/v1/characters/1',
            json={
                "name": "Test",
                "house": "Test House"
                # Missing age and role
            }
        )
        assert response.status_code == 400
        assert 'errors' in json.loads(response.data)

        # Test invalid age
        response = client.put(
            '/api/v1/characters/1',
            json={
                "name": "Test",
                "house": "Test House",
                "age": -1,
                "role": "Test Role"
            }
        )
        assert response.status_code == 400
        assert 'age' in str(json.loads(response.data)['errors'])

    def test_update_nonexistent_character(self, client, mock_characters, mocker):
        """Test updating a non-existent character."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        update_data = {
            "name": "Test",
            "house": "Test House",
            "age": 25,
            "role": "Test Role"
        }

        response = client.put('/api/v1/characters/999', json=update_data)
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "doesn't exist" in data['message']

    def test_update_character_invalid_format(self, client, mock_characters, mocker):
        """Test character update with invalid request formats."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        # Test without content type header
        response = client.put(
            '/api/v1/characters/1',
            data=json.dumps({"name": "Test"}),
            headers={}  # No Content-Type header
        )
        assert response.status_code == 415
        data = json.loads(response.data)
        assert 'application/json' in data['message']

        # Test malformed JSON specifically
        response = client.put(
            '/api/v1/characters/1',
            data='{"name": "Test", "house": "Test", "age": }',  # Malformed JSON
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['message'] == ("The browser (or proxy) "
                                   "sent a request that this server could not understand.")

    def test_update_character_missing_content_type(self, client, mock_characters, mocker):
        """Additional test for content type validation."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        # Another approach to test content type validation
        response = client.put(
            '/api/v1/characters/1',
            data=json.dumps({"name": "Test"}),
            content_type=None
        )
        assert response.status_code == 415
        data = json.loads(response.data)
        assert 'application/json' in data['message']

class TestCharacterDeletion:
    """Tests for character deletion."""

    def test_delete_character_success(self, client, mock_characters, mocker):
        """Test successful character deletion."""
        characters_copy = mock_characters.copy()
        mocker.patch('app.routes.CHARACTERS', characters_copy)

        response = client.delete('/api/v1/characters/1')
        assert response.status_code == 204

        # Verify character was deleted
        response = client.get('/api/v1/characters/1')
        assert response.status_code == 404

    def test_delete_with_save_error(self, client, mock_characters, mocker):
        """Test deletion with save error handling."""
        mocker.patch('app.routes.CHARACTERS', mock_characters.copy())
        mocker.patch(
            'app.routes.save_characters',
            side_effect=Exception("Save failed")
        )

        response = client.delete('/api/v1/characters/1')
        assert response.status_code == 204  # Should still succeed even if save fails

    def test_delete_nonexistent_character(self, client, mock_characters, mocker):
        """Test deleting a non-existent character."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        response = client.delete('/api/v1/characters/999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "doesn't exist" in data['message']


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_normalize_house_name(self):
        """Test house name normalization."""
        test_cases = [
            ('House Stark', 'stark'),
            ('HOUSE LANNISTER', 'lannister'),
            ('Targaryen', 'targaryen'),
            ('  House  Tyrell  ', 'tyrell'),
            ('', ''),  # Edge case: empty string
            ('   ', '')  # Edge case: whitespace only
        ]
        for input_name, expected in test_cases:
            assert normalize_house_name(input_name) == expected

    def test_id_generation(self, mocker):
        """Test ID generation in different scenarios."""
        # Test with empty list
        mocker.patch('app.routes.CHARACTERS', [])
        assert generate_new_id() == 1

        # Test with existing characters
        mock_chars = [
            {'id': 1, 'name': 'Test1'},
            {'id': 5, 'name': 'Test2'}  # Non-sequential ID
        ]
        mocker.patch('app.routes.CHARACTERS', mock_chars)
        assert generate_new_id() == 6  # Should be max + 1


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_save_error_handling(self, client, mock_characters, mocker):
        """Test error handling during save operations."""
        mocker.patch('app.routes.CHARACTERS', mock_characters.copy())
        mocker.patch(
            'app.routes.save_characters',
            side_effect=Exception('Simulated save error')
        )

        # Create should succeed even if save fails
        response = client.post(
            '/api/v1/characters/',
            json={
                "name": "Test Character",
                "house": "Test House",
                "age": 25,
                "role": "Test Role"
            }
        )
        assert response.status_code == 201