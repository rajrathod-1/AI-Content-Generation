"""
Configuration module for the AI Content Generation Service
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-0125-preview')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', 1000))
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', 0.7))
    
    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))
    
    # Vector Database Configuration
    FAISS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', './data/faiss_index')
    EMBEDDINGS_MODEL = os.getenv('EMBEDDINGS_MODEL', 'all-MiniLM-L6-v2')
    VECTOR_DIMENSION = int(os.getenv('VECTOR_DIMENSION', 384))
    MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', 10))
    USE_LIGHTWEIGHT_MODE = os.getenv('USE_LIGHTWEIGHT_MODE', 'False').lower() == 'true'
    
    # Data Processing Configuration
    DATA_DIRECTORY = os.getenv('DATA_DIRECTORY', './data/raw')
    PROCESSED_DATA_DIRECTORY = os.getenv('PROCESSED_DATA_DIRECTORY', './data/processed')
    CRAWL_DELAY = float(os.getenv('CRAWL_DELAY', 1.0))
    MAX_CRAWL_PAGES = int(os.getenv('MAX_CRAWL_PAGES', 1000))
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 100))
    
    # Performance Configuration
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    RATE_LIMIT = int(os.getenv('RATE_LIMIT', 100))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOG_FILE = os.getenv('LOG_FILE', './logs/app.log')
    
    # Monitoring Configuration
    METRICS_ENABLED = os.getenv('METRICS_ENABLED', 'True').lower() == 'true'
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', 60))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    REDIS_DB = 1  # Use different Redis DB for testing

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}