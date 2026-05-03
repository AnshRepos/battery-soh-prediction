import os

class Config:
    DEBUG = os.getenv('FLASK_DEBUG', True)
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    TESTING = False
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'battery_model.pkl')
    DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
