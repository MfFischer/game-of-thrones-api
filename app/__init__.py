"""
Application factory module.
"""
from flask import Flask, redirect
from flask_restx import Api

def create_app():
    """Create and configure the Flask application."""
    # Initialize Flask app
    app = Flask(__name__)

    # Initialize Flask-RESTX with Swagger UI as default
    api = Api(
        app,
        version='1.0',
        title='Game of Thrones API',
        description='A simple API for managing Game of Thrones characters',
        doc='/docs',  # Swagger UI route
        prefix='/api/v1'
    )

    # Redirect root URL to Swagger UI
    @app.route('/')
    def index():
        """Redirect root URL to Swagger UI documentation."""
        return redirect('/docs')

    # Health check route
    @app.route('/health')
    def health_check():
        """API health check endpoint."""
        return {
            'status': 'healthy',
            'message': 'Game of Thrones API is running',
            'docs_url': '/docs'
        }

    # Import routes here to avoid circular imports
    from .routes import characters_ns
    api.add_namespace(characters_ns, path='/characters')

    return app