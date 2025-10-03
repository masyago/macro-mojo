import os

class Config:
    DEBUG = False
    TESTING = False
    # Default database URL
    DATABASE_URI = os.environ.get('DATABASE_URL')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'postgresql://@localhost:5432/macro_mojo'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'postgresql:/@localhost:5432/test_macro_mojo'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost:5432/production_database_name'