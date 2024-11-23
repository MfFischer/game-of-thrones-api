"""Configuration settings."""
import os
from datetime import timedelta


class Config:
    # Basic Flask config
    SECRET_KEY = '123456789secret'
    DEBUG = True

    # Database config
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, '..', 'got_api.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT config
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_LEEWAY = timedelta(seconds=50)  # Allow 50 seconds of clock skew