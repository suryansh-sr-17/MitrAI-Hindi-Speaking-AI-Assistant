"""
Configuration settings for the Hindi AI Assistant
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Audio Processing Configuration
    MAX_AUDIO_DURATION = int(os.environ.get('MAX_AUDIO_DURATION', 60))
    AUDIO_SAMPLE_RATE = int(os.environ.get('AUDIO_SAMPLE_RATE', 16000))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    
    # STT Configuration
    STT_PROVIDER = os.environ.get('STT_PROVIDER', 'google_web_speech')  # 'whisper' or 'google_web_speech'
    WHISPER_MODEL_SIZE = os.environ.get('WHISPER_MODEL_SIZE', 'tiny')
    
    # TTS Configuration
    TTS_MODEL_NAME = os.environ.get('TTS_MODEL_NAME', 'tts_models/hi/male/tacotron2-DDC')
    
    # Face Detection Configuration
    FACE_DETECTION_CONFIDENCE = float(os.environ.get('FACE_DETECTION_CONFIDENCE', 0.5))
    FACE_DETECTION_SCALE_FACTOR = float(os.environ.get('FACE_DETECTION_SCALE_FACTOR', 1.1))
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Temporary file storage
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER', '/tmp')
    
    @staticmethod
    def validate_config():
        """Validate required configuration"""
        errors = []
        
        if not Config.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}