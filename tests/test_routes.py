import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import patch
from app.models import db, CharacterModel, User
from app.auth import generate_token, token_required
from app.routes import generate_new_id
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from flask import current_app
import jwt
from sqlalchemy import text

# API prefix constant
API_PREFIX = '/api/v1'

def _raise(exception):
    raise exception

###################
# Test Fixtures
###################

@pytest.fixture(scope='function')
def app():
    """Create and configure test Flask application."""
    from app import create_app
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create test user."""
    with app.app_context():
        user = User(username='testuser', role='user')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture
def admin_user(app):
    """Create admin user."""
    with app.app_context():
        admin = User(username='admin', role='admin')
        admin.set_password('adminpass')
        db.session.add(admin)
        db.session.commit()
        db.session.refresh(admin)
        return admin


@pytest.fixture
def auth_headers(test_user):
    """Generate auth headers for test user."""
    token = generate_token(test_user.username)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user):
    """Generate auth headers for admin user."""
    token = generate_token(admin_user.username)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_characters(app):
    """Create test characters."""
    with app.app_context():
        characters = [
            CharacterModel(
                name="Jon Snow",
                house="Stark",
                age=25,
                role="King in the North",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            ),
            CharacterModel(
                name="Daenerys Targaryen",
                house="Targaryen",
                age=23,
                role="Queen",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
        ]
        for char in characters:
            db.session.add(char)
        db.session.commit()
        for char in characters:
            db.session.refresh(char)
        return characters


###################
# Authentication Tests
###################

class TestAuth:
    """Test authentication endpoints."""

    def test_register_success(self, client):
        """Test successful user registration."""
        data = {
            "username": "newuser",
            "password": "testpass",
            "role": "user"
        }
        response = client.post(f'{API_PREFIX}/auth/register', json=data)
        assert response.status_code == 201
        assert "User registered successfully" in response.json["message"]

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with existing username."""
        data = {
            "username": "testuser",
            "password": "testpass"
        }
        response = client.post(f'{API_PREFIX}/auth/register', json=data)
        assert response.status_code == 400
        assert "Username already exists" in response.json["message"]


    def test_register_missing_data(self, client):
        """Test registration with missing data."""
        data = {"username": "testuser"}
        response = client.post(f'{API_PREFIX}/auth/register', json=data)
        assert response.status_code == 400

    def test_register_empty_password(self, client):
        """Test registration with empty password."""
        data = {
            "username": "testuser",
            "password": "",
            "role": "user"
        }
        response = client.post(f'{API_PREFIX}/auth/register', json=data)
        assert response.status_code == 400

    def test_login_success(self, client, test_user):
        """Test successful login."""
        data = {
            "username": "testuser",
            "password": "testpass"
        }
        response = client.post(f'{API_PREFIX}/auth/login', json=data)
        assert response.status_code == 200
        assert "token" in response.json
        assert response.json["username"] == "testuser"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        data = {"username": "wrong", "password": "wrong"}
        response = client.post(f'{API_PREFIX}/auth/login', json=data)
        # Unauthorized for invalid credentials
        assert response.status_code == 401
        assert 'Invalid credentials' in response.json['message']

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials"""
        response = client.post(
            f'{API_PREFIX}/auth/login',
            json={},  # Empty JSON
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400
        assert 'Username and password are required' in response.json['message']

    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        data = {"username": "testuser"}  # Missing password
        response = client.post(f'{API_PREFIX}/auth/login', json=data)
        assert response.status_code == 400
        assert 'Username and password are required' in response.json['message']


###################
# Character List Tests
###################

class TestCharacterList:
    """Test character list endpoints."""

    def test_get_characters_no_params(self, client, test_characters):
        """Test getting characters without parameters."""
        response = client.get(f'{API_PREFIX}/characters/')
        assert response.status_code == 200
        data = response.json
        assert len(data["characters"]) == len(test_characters)
        assert data["metadata"]["total_records"] == len(test_characters)

    def test_get_characters_with_pagination(self, client, test_characters):
        """Test character pagination."""
        response = client.get(f'{API_PREFIX}/characters/?skip=1&limit=1')
        assert response.status_code == 200
        data = response.json
        assert len(data["characters"]) == 1
        assert data["metadata"]["skip"] == 1
        assert data["metadata"]["limit"] == 1

    def test_get_characters_with_filters(self, client, test_characters):
        """Test character filtering."""
        response = client.get(
            f'{API_PREFIX}/characters/?house=stark&age_more_than=20&role=king'
        )
        assert response.status_code == 200
        data = response.json
        assert all(char["house"].lower() == "stark"
                  and char["age"] > 20
                  and "king" in char["role"].lower()
                  for char in data["characters"])

    def test_get_characters_with_name_filter(self, client, test_characters):
        """Test filtering by character name."""
        response = client.get(f'{API_PREFIX}/characters/?name=jon')
        assert response.status_code == 200
        data = response.json
        assert all("jon" in char["name"].lower() for char in data["characters"])

    def test_get_characters_with_age_range(self, client, test_characters):
        """Test filtering by age range."""
        response = client.get(
            f'{API_PREFIX}/characters/?age_more_than=20&age_less_than=30'
        )
        assert response.status_code == 200
        data = response.json
        assert all(20 < char["age"] < 30 for char in data["characters"])

    def test_get_characters_with_sorting(self, client, test_characters):
        """Test character sorting."""
        response = client.get(
            f'{API_PREFIX}/characters/?sort_by=age&sort_order=desc'
        )
        assert response.status_code == 200
        data = response.json
        ages = [char["age"] for char in data["characters"]]
        assert ages == sorted(ages, reverse=True)

    def test_get_characters_invalid_sort_field(self, client):
        """Test invalid sort field."""
        response = client.get(f'{API_PREFIX}/characters/?sort_by=invalid')
        assert response.status_code == 400
        assert "Invalid sort_by value" in response.json["message"]

    def test_get_characters_invalid_sort_order(self, client):
        """Test invalid sort order."""
        response = client.get(
            f'{API_PREFIX}/characters/?sort_by=name&sort_order=invalid'
        )
        assert response.status_code == 400
        assert "Invalid sort_order value" in response.json["message"]

    def test_create_character_success(self, client, auth_headers):
        """Test successful character creation."""
        data = {
            "name": "Arya Stark",
            "house": "Stark",
            "age": 18,
            "role": "Assassin"
        }
        response = client.post(
            f'{API_PREFIX}/characters/',
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json["name"] == "Arya Stark"

    def test_create_character_no_auth(self, client):
        """Test character creation without authentication."""
        data = {
            "name": "Arya Stark",
            "house": "Stark",
            "age": 18,
            "role": "Assassin"
        }
        response = client.post(f'{API_PREFIX}/characters/', json=data)
        assert response.status_code == 401

    def test_create_character_invalid_data(self, client, auth_headers):
        """Test character creation with invalid data."""
        data = {
            "name": "",
            "house": "",
            "age": -1,
            "role": ""
        }
        response = client.post(
            f'{API_PREFIX}/characters/',
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 400


    def test_create_character_missing_fields(self, client, auth_headers):
        """Test character creation with missing fields."""
        data = {"name": "Test Character"}
        response = client.post(
            f'{API_PREFIX}/characters/',
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Validation failed" in response.json["message"]


###################
# Individual Character Tests
###################

class TestCharacter:
    """Test individual character endpoints."""

    def test_get_character_by_id(self, client, app, test_characters):
        """Test getting character by ID."""
        with app.app_context():
            char_id = test_characters[0].id
            response = client.get(f'{API_PREFIX}/characters/{char_id}')
            assert response.status_code == 200
            assert response.json["name"] == test_characters[0].name

    def test_get_character_by_name(self, client, test_characters):
        """Test getting character by name."""
        response = client.get(f'{API_PREFIX}/characters/Jon Snow')
        assert response.status_code == 200
        assert response.json["name"] == "Jon Snow"

    def test_get_character_not_found(self, client):
        """Test getting non-existent character."""
        response = client.get(f'{API_PREFIX}/characters/999')
        assert response.status_code == 404
        assert "Character not found" in response.json["message"]

    def test_update_character_success(self, client, app, test_characters, auth_headers):
        """Test successful character update."""
        with app.app_context():
            char_id = test_characters[0].id
            data = {
                "name": "Updated Name",
                "house": "Updated House",
                "age": 30,
                "role": "Updated Role"
            }
            response = client.put(
                f'{API_PREFIX}/characters/{char_id}',
                json=data,
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.json["name"] == "Updated Name"

    def test_update_character_not_found(self, client, auth_headers):
        """Test updating non-existent character."""
        data = {
            "name": "Test",
            "house": "Test",
            "age": 20,
            "role": "Test"
        }
        response = client.put(
            f'{API_PREFIX}/characters/999',
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_character_no_auth(self, client, test_characters):
        """Test updating character without authentication."""
        char_id = test_characters[0].id
        data = {
            "name": "Updated Name",
            "house": "Updated House",
            "age": 30,
            "role": "Updated Role"
        }
        response = client.put(f'{API_PREFIX}/characters/{char_id}', json=data)
        assert response.status_code == 401

    def test_update_character_invalid_data(self, client, test_characters, auth_headers):
        """Test updating character with invalid data."""
        char_id = test_characters[0].id
        data = {
            "name": "",
            "house": "",
            "age": -1,
            "role": ""
        }
        response = client.put(
            f'{API_PREFIX}/characters/{char_id}',
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_delete_character_admin(self, client, test_characters, admin_headers):
        """Test character deletion by admin."""
        char_id = test_characters[0].id
        response = client.delete(
            f'{API_PREFIX}/characters/{char_id}',
            headers=admin_headers
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json["message"]

    def test_delete_character_no_auth(self, client, test_characters):
        """Test character deletion without authentication."""
        char_id = test_characters[0].id
        response = client.delete(f'{API_PREFIX}/characters/{char_id}')
        assert response.status_code == 401

    def test_delete_character_non_admin(self, client, test_characters, auth_headers):
        """Test character deletion by non-admin user."""
        char_id = test_characters[0].id
        response = client.delete(
            f'{API_PREFIX}/characters/{char_id}',
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "Admin privileges required" in response.json["message"]

    def test_delete_character_not_found(self, client, admin_headers):
        """Test deleting non-existent character."""
        response = client.delete(
            f'{API_PREFIX}/characters/999',
            headers=admin_headers
        )
        assert response.status_code == 404
        assert "Character not found" in response.json["message"]

###################
# Statistics Tests
###################

class TestStatistics:
    """Test character statistics endpoints."""

    def test_get_statistics_complete(self, client, test_characters):
        """Test getting complete character statistics."""
        response = client.get(f'{API_PREFIX}/characters/statistics')
        assert response.status_code == 200
        data = response.json["statistics"]

        # Verify all required statistics are present
        assert "house_statistics" in data
        assert "age_distribution" in data
        assert "role_distribution" in data

        # Count the test characters by house
        house_counts = {}
        for char in test_characters:
            house_counts[char.house] = house_counts.get(char.house, 0) + 1

        # Verify house statistics match test data
        houses = data["house_statistics"]
        for house_stat in houses:
            house_name = house_stat["house"]
            if house_name in house_counts:
                assert house_stat["member_count"] == house_counts[house_name]

        # Verify age ranges are present
        age_dist = data["age_distribution"]
        expected_ranges = ["Under 20", "21-40", "41-60", "Over 60"]
        actual_ranges = [d["range"] for d in age_dist]
        assert all(r in actual_ranges for r in expected_ranges)

        # Verify role distribution
        role_dist = data["role_distribution"]
        test_roles = {(char.house, char.role) for char in test_characters}
        for role_stat in role_dist:
            if (role_stat["house"], role_stat["role"]) in test_roles:
                assert role_stat["count"] > 0


    def test_get_statistics_empty_db(self, client, app):
        """Test statistics with empty database."""
        with app.app_context():
            # Clear the database
            CharacterModel.query.delete()
            db.session.commit()

            response = client.get(f'{API_PREFIX}/characters/statistics')
            assert response.status_code == 200
            data = response.json["statistics"]

            # Verify empty statistics
            assert len(data["house_statistics"]) == 0
            assert all(range_data["count"] == 0
                        for range_data in data["age_distribution"])
            assert len(data["role_distribution"]) == 0

    def test_statistics_house_calculations(self, client, test_characters):
        """Test house statistics calculations."""
        response = client.get(f'{API_PREFIX}/characters/statistics')
        assert response.status_code == 200
        house_stats = response.json["statistics"]["house_statistics"]

        stark_stats = next(stat for stat in house_stats if stat["house"] == "Stark")
        assert stark_stats["member_count"] > 0
        assert stark_stats["average_age"] > 0
        assert stark_stats["youngest"] <= stark_stats["oldest"]

    def test_statistics_age_ranges(self, client, test_characters):
        """Test age distribution ranges."""
        response = client.get(f'{API_PREFIX}/characters/statistics')
        assert response.status_code == 200
        age_dist = response.json["statistics"]["age_distribution"]

        # Verify all age ranges are present
        ranges = [dist["range"] for dist in age_dist]
        assert "Under 20" in ranges
        assert "21-40" in ranges
        assert "41-60" in ranges
        assert "Over 60" in ranges

    def test_statistics_database_error(self, client):
        """Test statistics endpoint with database error."""
        with patch('app.models.db.session') as mock_session:
            # Mock the query method to raise SQLAlchemyError
            mock_session.query.side_effect = SQLAlchemyError("Database error")

            response = client.get(f'{API_PREFIX}/characters/statistics')
            assert response.status_code == 500
            assert "error" in response.json["status"]

###################
# Error Handling Tests
###################
class TestErrorHandling:
    """Test error handling."""

    def test_invalid_json_format(self, client, auth_headers):
        """Test handling of invalid JSON format."""
        response = client.post(
            f'{API_PREFIX}/characters/',
            data='this is not json',
            headers={'Content-Type': 'application/json', **auth_headers}
        )
        # Implementation returns 500 for JSON decode errors
        assert response.status_code == 500
        assert "could not understand" in response.json["message"].lower()

    def test_operational_error_handling(self, app, monkeypatch):
        def mock_execute():
            raise OperationalError(statement='SELECT 1', params={}, orig='Operational error')

        monkeypatch.setattr(db.session, 'execute', mock_execute)

        with app.app_context():
            with pytest.raises(OperationalError) as exc_info:
                db.session.execute(text('SELECT 1'))
            assert "Operational error" in str(exc_info.value)


    def test_method_not_allowed(self, client):
        """Test handling of invalid HTTP method."""
        response = client.patch(f'{API_PREFIX}/characters/1')
        assert response.status_code == 405

    def test_invalid_token(self, client):
        """Test handling of invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post(
            f'{API_PREFIX}/characters/',
            json={"name": "test"},
            headers=headers
        )
        assert response.status_code == 401
        assert "Invalid token" in response.json["message"]

    def test_expired_token(self, client):
        """Test handling of expired token."""

        # Manually create an expired token
        payload = {
            'username': 'testuser',
            'role': 'user',
            'exp': datetime.now(UTC) - timedelta(hours=1),  # Expired 1 hour ago
            'iat': datetime.now(UTC),
            'nbf': datetime.now(UTC)
        }
        expired_token = jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = client.post(
            f'{API_PREFIX}/characters/',
            json={"name": "test"},
            headers=headers
        )
        assert response.status_code == 401
        # Verify_token returns None for expired tokens
        assert "Invalid token" in response.json["message"]

    def test_missing_token(self, client):
        """Test request without token."""
        response = client.post(
            f'{API_PREFIX}/characters/',
            json={"name": "test"}
        )
        assert response.status_code == 401
        assert "Token is missing" in response.json["message"]

    def test_malformed_token_header(self, client):
        """Test malformed Authorization header."""
        headers = {"Authorization": "NotBearer token"}
        response = client.post(
            f'{API_PREFIX}/characters/',
            json={"name": "test"},
            headers=headers
        )
        assert response.status_code == 401
        assert "Invalid token format" in response.json["message"]

    def test_database_error_handling(self, client, auth_headers, app):
        """Test handling of database errors."""
        with patch('app.models.db.session') as mock_session:
            mock_session.commit.side_effect = SQLAlchemyError("Database error")

            data = {
                "name": "Test Character",
                "house": "Test House",
                "age": 25,
                "role": "Test Role"
            }
            response = client.post(
                f'{API_PREFIX}/characters/',
                json=data,
                headers=auth_headers
            )
            assert response.status_code == 500
            assert "database error" in response.json["message"].lower()


    def test_validation_error(self, client, auth_headers):
        """Test validation error handling."""
        data = {
            "name": "",  # Empty name should fail validation
            "house": "Test House",
            "age": -1,  # Negative age should fail validation
            "role": None  # None role should fail validation
        }
        response = client.post(
            f'{API_PREFIX}/characters/',
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "validation" in response.json["message"].lower()

    def test_register_database_error(self, client, monkeypatch):
        """Test database error during registration"""
        data = {
            "username": "newuser",
            "password": "testpass",
            "role": "user"
        }

        def mock_add():
            raise SQLAlchemyError("Database error")

        monkeypatch.setattr(db.session, 'add', mock_add)

        response = client.post(
            f'{API_PREFIX}/auth/register',
            json=data,
            headers={'Content-Type': 'application/json'}
        )

        assert response.status_code == 500
        assert 'Database error occurred' in response.json['message']

    def test_login_incorrect_password(self, client, test_user):
        data = {
            "username": "testuser",
            "password": "wrongpass"
        }
        response = client.post(f'{API_PREFIX}/auth/login', json=data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json["message"]

    def test_create_character_invalid_age_type(self, client, auth_headers):
        data = {
            "name": "Test Character",
            "house": "Test House",
            "age": "invalid_age",
            "role": "Test Role"
        }
        response = client.post(
            f'{API_PREFIX}/characters/',
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Validation failed" in response.json["message"]

    def test_generate_new_id(self, app, test_characters):
        with app.app_context():
            new_id = generate_new_id()
            assert new_id == len(test_characters) + 1

    def test_statistics_average_age(self, client, test_characters):
        response = client.get(f'{API_PREFIX}/characters/statistics')
        assert response.status_code == 200
        house_stats = response.json["statistics"]["house_statistics"]
        for stat in house_stats:
            if stat["house"] == "Stark":
                assert stat["average_age"] == 25.0

    def test_generate_new_id_database_error(self, app, monkeypatch):
        with app.app_context():
            monkeypatch.setattr(db.session, 'query', lambda *args, **kwargs: _raise(SQLAlchemyError))
            with pytest.raises(Exception):
                generate_new_id()

    def test_token_required_decorator(self, client, auth_headers):
        @token_required
        def dummy_endpoint():
            return "Success"

        # Register the endpoint temporarily
        with current_app.test_request_context():
            current_app.add_url_rule('/dummy', view_func=dummy_endpoint)

        # Test without token
        response = client.get('/dummy')
        assert response.status_code == 401
        assert "Token is missing" in response.json["message"]

        # Test with valid token
        response = client.get('/dummy', headers=auth_headers)
        assert response.status_code == 200
        assert response.data.decode() == "Success"

class TestGenerateNewId:
    def test_generate_new_id_empty_db(self, app, client):
        with app.app_context():
            db.session.query(CharacterModel).delete()
            db.session.commit()
            new_id = generate_new_id()
            assert new_id == 1

    def test_generate_new_id_with_characters(self, app, test_characters):
        with app.app_context():
            new_id = generate_new_id()
            assert new_id == len(test_characters) + 1

    def test_generate_new_id_database_error(self, app, monkeypatch):
        with app.app_context():
            monkeypatch.setattr(db.session, 'query', lambda *args, **kwargs: _raise(SQLAlchemyError))
            with pytest.raises(Exception):
                generate_new_id()

class TestGetCharacterByIdentifier:
    def test_get_character_by_identifier_invalid_id(self, client, test_characters):
        response = client.get(f'{API_PREFIX}/characters/999999')
        assert response.status_code == 404
        assert "Character not found" in response.json["message"]

    def test_get_character_by_identifier_invalid_name(self, client, test_characters):
        response = client.get(f'{API_PREFIX}/characters/NonExistentCharacter')
        assert response.status_code == 404
        assert "Character not found" in response.json["message"]

class TestCharacterStatistics:
    def test_character_statistics_empty_db(self, app, client):
        with app.app_context():
            db.session.query(CharacterModel).delete()
            db.session.commit()
            response = client.get(f'{API_PREFIX}/characters/statistics')
            assert response.status_code == 200
            assert "statistics" in response.json
            assert response.json["statistics"]["house_statistics"] == []
            assert all(dist["count"] == 0 for dist in response.json["statistics"]["age_distribution"])
            assert response.json["statistics"]["role_distribution"] == []

    def test_character_statistics_edge_cases(self, app, client, test_characters):
        response = client.get(f'{API_PREFIX}/characters/statistics')
        assert response.status_code == 200
        # Add assertions for specific edge cases in statistics

class TestCharacterDeleteMethod:
    def test_delete_character_invalid_id(self, client, admin_headers):
        response = client.delete(
            f'{API_PREFIX}/characters/999999',
            headers=admin_headers
        )
        assert response.status_code == 404
        assert "Character not found" in response.json["message"]

    def test_delete_character_without_admin_privileges(self, client, auth_headers, test_characters):
        char_id = test_characters[0].id
        response = client.delete(
            f'{API_PREFIX}/characters/{char_id}',
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "Admin privileges required" in response.json["message"]


if __name__ == '__main__':
    pytest.main(['-v'])