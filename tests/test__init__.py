import os
import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from flask import Flask, current_app
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import text
from app import create_app, db
from app.models import User

API_PREFIX = '/api/v1'


@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(level=logging.INFO)
    yield
    logging.getLogger().handlers = []

@pytest.fixture
def mock_env_vars(monkeypatch):
    test_vars = {
        'SECRET_KEY': 'test-key',
        'DEBUG': 'True',
        'DATABASE_URL': 'sqlite:///:memory:',
        'TESTING': 'True'
    }
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)
    return test_vars


@pytest.fixture
def app(mock_env_vars):
    _app = create_app('testing')
    with _app.app_context():
        db.create_all()
        yield _app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user(app):
    user = User(
        username='testuser',
        password_hash='hashed_password',
        role='user'
    )
    with app.app_context():
        db.session.add(user)
        db.session.commit()
    return user


class TestConfiguration:
    def test_testing_config(self, monkeypatch):
        """Test testing configuration setup"""
        monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
        monkeypatch.setenv('DEBUG', 'True')

        app = create_app('testing')

        assert app.config['TESTING'] is True
        assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
        assert app.config['SECRET_KEY'] == 'test-secret-key'
        assert app.config['DEBUG'] is True
        assert app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] is False

    def test_production_config(self):
        """Test production configuration setup"""
        app = create_app('production')
        db_path = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'got_api.db'
        ))

        assert app.config['TESTING'] is False
        assert app.config['SQLALCHEMY_DATABASE_URI'] == f'sqlite:///{db_path}'
        assert app.config['SECRET_KEY'] == 'prod-secret-key'
        assert app.config['DEBUG'] is False

    def test_default_config(self):
        """Test default configuration setup"""
        app = create_app()
        db_path = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'got_api.db'
        ))

        assert app.config['TESTING'] is False
        assert app.config['SQLALCHEMY_DATABASE_URI'] == f'sqlite:///{db_path}'
        assert app.config['SECRET_KEY'] == 'dev-secret-key'
        assert app.config['DEBUG'] is False

    def test_invalid_config(self):
        """Test invalid configuration name"""
        with pytest.raises(ValueError, match="Invalid configuration name: invalid"):
            create_app('invalid')


class TestDatabaseInitialization:
    def test_memory_database(self, monkeypatch):
        """Test in-memory database initialization"""
        monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')

        # Patch create_all before creating the app
        with patch('flask_sqlalchemy.SQLAlchemy.create_all') as mock_create_all:
            app = create_app('testing')
            mock_create_all.reset_mock()

            with app.app_context():
                from app import _initialize_database
                _initialize_database(app)
                mock_create_all.assert_called_once()

    def test_database_initialization_error(self):
        """Test database initialization error handling"""
        app = create_app('testing')

        with app.app_context(), \
                patch('flask.current_app.logger.error') as mock_logger, \
                patch('app.db.session.execute', side_effect=OperationalError("statement", {}, "error")), \
                pytest.raises(Exception, match="Database initialization failed"):
            from app import _initialize_database
            _initialize_database(app)
            mock_logger.assert_called_once()

    def test_database_generic_error(self):
        """Test generic database error handling"""
        app = create_app('testing')

        with app.app_context(), \
                patch('flask.current_app.logger.error') as mock_logger, \
                patch('flask_sqlalchemy.SQLAlchemy.create_all'), \
                patch('app.db.session.execute', side_effect=Exception("Database initialization failed")), \
                pytest.raises(Exception, match="Database initialization failed"):
            from app import _initialize_database
            _initialize_database(app)
            mock_logger.assert_called_once()


class TestAPI:
    def test_api_documentation(self, app):
        """Test API documentation setup"""
        api = app.extensions['flask-restx']
        assert api.version == '1.0'
        assert api.title == 'Game of Thrones API'
        assert isinstance(api.authorizations, dict)
        assert 'Bearer Auth' in api.authorizations

    def test_api_prefix(self, app):
        """Test API prefix configuration"""
        api = app.extensions['flask-restx']
        assert api.prefix == '/api/v1'

    def test_api_security(self, app):
        """Test API security configuration"""
        api = app.extensions['flask-restx']
        auth_config = api.authorizations['Bearer Auth']
        assert auth_config['type'] == 'apiKey'
        assert auth_config['in'] == 'header'
        assert auth_config['name'] == 'Authorization'

    def test_api_configuration(self, app):
        """Test API configuration"""
        api = app.extensions['flask-restx']
        assert api.version == '1.0'
        assert api.title == 'Game of Thrones API'
        assert api.prefix == '/api/v1'
        assert 'Bearer Auth' in api.authorizations

class TestRoutes:
    def test_index_redirect(self, client):
        """Test root URL redirect"""
        response = client.get('/')
        assert response.status_code == 302
        assert '/docs' in response.location

    def test_health_check_success(self, client):
        """Test successful health check"""
        response = client.get('/health')
        data = response.get_json()

        assert response.status_code == 200
        assert data['status'] == 'healthy'
        assert data['database']['status'] == 'connected'
        assert data['database']['type'] == 'SQLite'
        assert data['docs_url'] == '/docs'
        assert 'environment' in data

    def test_health_check_with_db_error(self, client):
        """Test health check with database error"""
        with patch('app.db.session.execute', side_effect=SQLAlchemyError("DB error")):
            response = client.get('/health')
            data = response.get_json()

            assert response.status_code == 500
            assert data['status'] == 'unhealthy'
            assert 'Database connection failed' in data['message']

    def test_health_check_with_generic_error(self, client):
        """Test health check with generic error"""
        with patch('app.db.session.execute', side_effect=Exception("Generic error")):
            response = client.get('/health')
            data = response.get_json()

            assert response.status_code == 500
            assert data['status'] == 'unhealthy'
            assert 'error' in data

class TestErrorHandlers:

    def test_500_handler(self, client):
        """Test 500 error handler"""
        with patch('app.db.session.execute', side_effect=Exception("Server error")):
            response = client.get('/health')
            assert response.status_code == 500
            assert 'Internal server error' in response.get_json()['message']


class TestSessionManagement:
    def test_before_request_db_check(self, client):
        """Test database check before request"""
        with patch('app.db.session.execute', side_effect=SQLAlchemyError("DB error")):
            response = client.get('/health')
            assert response.status_code == 500
            assert 'Database connection failed' in response.get_json()['message']

    def test_teardown_session(self, app):
        """Test session cleanup on teardown"""
        with app.app_context():
            with patch('app.db.session.remove') as mock_remove:
                # Only call teardown once
                app.teardown_appcontext_funcs[0](None)
                mock_remove.assert_called_once()

    def test_session_cleanup_on_error(self, app, client):
        """Test session cleanup on database error"""
        with patch('app.db.session.execute', side_effect=SQLAlchemyError("DB error")), \
                patch('app.db.session.remove') as mock_remove:
            client.get('/health')
            mock_remove.assert_called()


class TestLogging:
    def test_logging_configuration(self, app):
        """Test logging setup"""
        assert app.logger.level == logging.INFO

    def test_logging_database_error(self, app):
        """Test logging of database errors"""
        with app.app_context(), \
                patch('flask.current_app.logger.error') as mock_logger, \
                patch('app.db.session.execute', side_effect=OperationalError(
                    "statement",
                    {}, "error")), \
                pytest.raises(Exception):
            from app import _initialize_database
            _initialize_database(app)
            mock_logger.assert_called_with(
                "Database initialization failed: (builtins.OperationalError) error"
            )