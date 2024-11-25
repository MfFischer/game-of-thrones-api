"""
Game of Thrones API Application Factory Module.

This module initializes and configures the Flask application, including:
- Database configuration and initialization
- API documentation with Swagger UI
- Route registration
- Error handlers
- Health check endpoint
"""

import os
import logging
from flask import Flask, redirect, jsonify
from flask_restx import Api
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import text

from .models import db
from .config import Config

# Initialize Flask-Migrate extension
migrate = Migrate()

def create_app(config_name=None):
    """
    Create and configure the Flask application.

    Args:
        config_name: The configuration type ('testing', 'production', or None for default)

    Returns:
        Flask application instance

    Raises:
        ValueError: If an invalid configuration name is provided
    """
    app = Flask(__name__)

    # Set up logging
    app.logger.setLevel(logging.INFO)

    # Configure application based on environment
    if config_name == 'testing':
        _configure_testing(app)
    elif config_name == 'production':
        _configure_production(app)
    elif config_name is None:
        _configure_default(app)
    else:
        raise ValueError(f"Invalid configuration name: {config_name}")

    # Initialize Flask extensions
    _initialize_extensions(app)

    # Setup API documentation
    api = _setup_api(app)

    # Register routes and error handlers
    _register_routes(app, api)
    _register_error_handlers(app)

    # Initialize database
    _initialize_database(app)

    return app

def _configure_testing(app):
    """Configure application for testing environment."""
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': os.getenv('DATABASE_URL', 'sqlite:///:memory:'),
        'SECRET_KEY': os.getenv('SECRET_KEY', 'test-secret-key'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'DEBUG': os.getenv('DEBUG', 'False').lower() == 'true'
    })
    app.logger.info("Configured application for testing")

def _configure_production(app):
    """Configure application for production environment."""
    # Get absolute path for database
    db_path = os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'got_api.db'
    ))

    app.config.update({
        'TESTING': False,
        'SQLALCHEMY_DATABASE_URI': os.getenv('DATABASE_URL', f'sqlite:///{db_path}'),
        'SECRET_KEY': os.getenv('SECRET_KEY', 'prod-secret-key'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'DEBUG': os.getenv('DEBUG', 'False').lower() == 'true'
    })

    app.logger.info(f"Configured application for production with database at: {db_path}")

def _configure_default(app):
    """Configure default application settings."""
    # Get absolute path for database
    db_path = os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'got_api.db'
    ))

    app.config.update({
        'TESTING': False,
        'SQLALCHEMY_DATABASE_URI': os.getenv('DATABASE_URL', f'sqlite:///{db_path}'),
        'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-secret-key'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'DEBUG': os.getenv('DEBUG', 'False').lower() == 'true'
    })

    app.logger.info(f"Configured application with default settings and database at: {db_path}")

def _initialize_extensions(app):
    """Initialize Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)

def _setup_api(app):
    """
    Set up Flask-RESTX API with Swagger documentation.

    Returns:
        Api: Configured Flask-RESTX API instance
    """
    authorizations = {
        'Bearer Auth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**",
        },
    }

    api = Api(
        app,
        version='1.0',
        title='Game of Thrones API',
        description='A simple API for managing Game of Thrones characters.',
        doc='/docs',
        authorizations=authorizations,
        security='Bearer Auth',
        prefix='/api/v1'
    )

    # Store API in both extensions for compatibility
    app.extensions['api'] = api
    app.extensions['flask-restx'] = api

    return api

def _register_routes(app, api):
    """Register application routes and namespaces."""
    from .routes import characters_ns, auth_ns

    api.add_namespace(auth_ns, path='/auth')
    api.add_namespace(characters_ns, path='/characters')


    @app.route('/')
    def index():
        """Redirect root URL to Swagger UI documentation."""
        return redirect('/docs')

    @app.route('/health')
    def health_check():
        """API health check endpoint."""
        try:
            db.session.execute(text('SELECT 1'))
            db_status = 'connected'
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            db_exists = os.path.exists(db_path) if not db_path == ':memory:' else True

            return jsonify({
                'status': 'healthy',
                'message': 'Game of Thrones API is running',
                'database': {
                    'status': db_status,
                    'type': 'SQLite',
                    'path': db_path,
                    'exists': db_exists
                },
                'docs_url': '/docs',
                'environment': 'testing' if app.config['TESTING'] else 'production'
            })
        except SQLAlchemyError as e:
            return jsonify({
                'status': 'unhealthy',
                'message': 'Database connection failed',
                'error': str(e)
            }), 500
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500

def _register_error_handlers(app):
    """Register application error handlers."""
    @app.errorhandler(404)
    def not_found():
        return jsonify({'message': 'Resource not found'}), 404

    @app.errorhandler(400)
    def bad_request():
        return jsonify({'error': 'Bad request'}), 400

    @app.errorhandler(500)
    def internal_server_error():
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(500)
    def internal_error():
        return jsonify({'message': 'Internal server error'}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {str(error)}")
        return jsonify({
            'status': 'unhealthy',
            'message': 'Internal server error',
            'error': str(error)
        }), 500

    @app.before_request
    def before_request():
        try:
            db.session.execute(text('SELECT 1'))
        except SQLAlchemyError as e:
            db.session.remove()
            return jsonify({
                'status': 'unhealthy',
                'message': 'Database connection failed',
                'error': str(e)
            }), 500

    @app.teardown_appcontext
    def shutdown_session():
        db.session.remove()

def _initialize_database(app):
    """
    Initialize database and verify connection.
    """
    with app.app_context():
        try:
            # Get database path
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

            # For memory database or testing, always create tables
            if db_path == ':memory:' or app.config['TESTING']:
                db.create_all()
                app.logger.info("Created database tables for testing")
            else:
                # For file-based database, only create if it doesn't exist
                db_exists = os.path.exists(db_path)
                if not db_exists:
                    # Create the database directory if it doesn't exist
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    db.create_all()
                    app.logger.info("Created new database and tables")
                else:
                    app.logger.info("Using existing database")

            # Verify database connection
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            app.logger.info("Database connection verified")

        except OperationalError as e:
            app.logger.error(f"Database initialization failed: {e}")
            raise Exception("Database initialization failed") from e
        except Exception as e:
            app.logger.error(f"Database initialization failed: {e}")
            raise