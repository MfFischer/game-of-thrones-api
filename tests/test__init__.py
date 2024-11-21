"""
Test application initialization.
"""
from app import create_app


def test_create_app(app, client):
    """Test application factory."""
    app = create_app()
    assert app.config['TESTING'] is False

    # Test health check endpoint
    with app.test_client() as client:
        response = client.get('/')
        # Should redirect to /docs
        assert response.status_code == 302

        response = client.get('/health')
        assert response.status_code == 200
        assert response.json['status'] == 'healthy'


def test_create_app_testing(app, client):
    """Test application factory with testing configuration."""
    app = create_app()
    app.config['TESTING'] = True

    assert app.config['TESTING'] is True

    with app.test_client() as client:
        response = client.get('/health')
        assert response.status_code == 200