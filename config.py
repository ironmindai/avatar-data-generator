"""
Configuration settings for Avatar Data Generator Flask application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class with all settings."""

    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'avatar_data_generator')
    DB_USER = os.getenv('DB_USER', 'avatar_data_gen')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Build SQLAlchemy Database URI
    # Use DATABASE_URL if provided, otherwise build from components
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )

    # SQLAlchemy Settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = FLASK_ENV == 'development'

    # Session Configuration
    SESSION_COOKIE_SECURE = FLASK_ENV == 'production'  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = 3600 * 24 * 7  # 7 days in seconds

    # WTForms/CSRF Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No timeout for CSRF tokens

    # Application Port
    APP_PORT = int(os.getenv('APP_PORT', '7001'))

    # Security Headers
    SECURITY_HEADERS = {
        'X-Frame-Options': 'SAMEORIGIN',
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    TESTING = False

    # Disable caching for development
    SEND_FILE_MAX_AGE_DEFAULT = 0  # Don't cache static files
    TEMPLATES_AUTO_RELOAD = True  # Auto-reload templates when changed


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Force HTTPS


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    Get the appropriate configuration based on FLASK_ENV.

    Returns:
        Configuration class instance
    """
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
