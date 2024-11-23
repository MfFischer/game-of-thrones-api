"""
Application factory module.
"""
from flask import Flask, redirect
from flask_restx import Api
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from pathlib import Path
import os
from .models import db
from .config import Config

migrate = Migrate()

def create_app():
    """Create and configure the Flask application."""
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(Config)

    # Set the database path in the app config
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'got_api.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    print(f"Database path: {db_path}")
    print(f"App initialized with secret key: {app.config.get('SECRET_KEY')[:10]}...")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Define JWT authorization in Swagger
    authorizations = {
        'Bearer Auth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**",
        },
    }

    # Initialize Flask-RESTX with Swagger UI and authorization
    api = Api(
        app,
        version='1.0',
        title='Game of Thrones API',
        description='''A simple API for managing Game of Thrones characters. 
        
        Authentication:
        - Register at /auth/register
        - Get token at /auth/login
        - Use token in Authorize button above
        ''',
        doc='/docs',
        authorizations=authorizations,
        security='Bearer Auth',
        prefix='/api/v1'
    )

    # Redirect root URL to Swagger UI
    @app.route('/')
    def index():
        """Redirect root URL to Swagger UI documentation."""
        return redirect('/docs')

    # Enhanced health check route
    @app.route('/health')
    def health_check():
        """API health check endpoint."""
        try:
            # Test database connection
            db.session.execute(text('SELECT 1'))
            db_status = 'connected'

            return {
                'status': 'healthy',
                'message': 'Game of Thrones API is running',
                'database': {
                    'status': db_status,
                    'type': 'SQLite',
                    'path': db_path,
                    'exists': os.path.exists(db_path)
                },
                'docs_url': '/docs'
            }
        except SQLAlchemyError as e:
            return {
                'status': 'unhealthy',
                'message': 'Database connection failed',
                'error': str(e)
            }, 500
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': 'System error',
                'error': str(e)
            }, 500

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'message': 'Resource not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'message': 'Internal server error'}, 500

    # Import routes
    from .routes import characters_ns, auth_ns
    api.add_namespace(auth_ns, path='/auth')
    api.add_namespace(characters_ns, path='/characters')

    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
            # Verify database is writable
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            print("Database connection verified")
        except Exception as e:
            app.logger.error(f"Database initialization failed: {e}")
            raise

    @app.before_request
    def before_request():
        """Ensure database connection is active."""
        try:
            db.session.execute(text('SELECT 1'))
        except SQLAlchemyError:
            db.session.remove()
            raise

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Clean up database session."""
        db.session.remove()

    return app