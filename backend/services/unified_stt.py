"""
Unified STT Service
Provides a single interface that can switch between different STT providers
while maintaining the same API for backward compatibility
"""

import logging
import os
from typing import Dict, Any, Optional

# Import services and config
try:
    # Try relative imports first (when imported as module)
    from .speech_to_text import get_stt_service as get_whisper_service
    from .google_web_stt import get_google_web_stt_service
    from ..config import Config
except ImportError:
    # Fallback for direct execution or different import context
    try:
        from speech_to_text import get_stt_service as get_whisper_service
        from google_web_stt import get_google_web_stt_service
        from config import Config
    except ImportError:
        # Last resort - set defaults
        Config = type('Config', (), {
            'STT_PROVIDER': os.getenv('STT_PROVIDER', 'google_web_speech'),
            'WHISPER_MODEL_SIZE': os.getenv('WHISPER_MODEL_SIZE', 'tiny')
        })

logger = logging.getLogger(__name__)

class UnifiedSTTService:
    """
    Unified STT service that can switch between providers
    Maintains same interface as original Whisper service
    """
    
    def __init__(self, provider: str = None):
        """
        Initialize unified STT service
        
        Args:
            provider: STT provider ('whisper' or 'google_web_speech')
        """
        self.provider = provider or Config.STT_PROVIDER
        self.service = None
        
        logger.info(f"Initializing Unified STT Service with provider: {self.provider}")
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the appropriate STT service based on provider"""
        try:
            if self.provider == 'google_web_speech':
                self.service = get_google_web_stt_service()
                logger.info("Using Google Web Speech STT service")
            elif self.provider == 'whisper':
                self.service = get_whisper_service(Config.WHISPER_MODEL_SIZE)
                logger.info(f"Using Whisper STT service (model: {Config.WHISPER_MODEL_SIZE})")
            else:
                logger.warning(f"Unknown STT provider: {self.provider}, falling back to Google Web Speech")
                self.provider = 'google_web_speech'
                self.service = get_google_web_stt_service()
                
        except Exception as e:
            logger.error(f"Failed to initialize STT provider {self.provider}: {str(e)}")
            # Fallback to the other provider
            try:
                if self.provider == 'google_web_speech':
                    logger.info("Falling back to Whisper")
                    self.provider = 'whisper'
                    self.service = get_whisper_service('tiny')
                else:
                    logger.info("Falling back to Google Web Speech")
                    self.provider = 'google_web_speech'
                    self.service = get_google_web_stt_service()
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
                raise Exception("Failed to initialize any STT provider")
    
    def load_model(self) -> bool:
        """
        Load the STT model
        
        Returns:
            bool: True if model loaded successfully
        """
        if not self.service:
            self._initialize_service()
        
        if hasattr(self.service, 'load_model'):
            return self.service.load_model()
        return True
    
    def transcribe(self, audio_path: str, language: str = "hi") -> Dict[str, Any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to the audio file
            language: Language code (default: "hi" for Hindi)
            
        Returns:
            dict: Transcription result
        """
        if not self.service:
            return {
                'success': False,
                'error': 'STT service not initialized',
                'text': '',
                'confidence': 0.0
            }
        
        try:
            result = self.service.transcribe(audio_path, language)
            # Add provider info to result
            if isinstance(result, dict):
                result['stt_provider'] = self.provider
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed with {self.provider}: {str(e)}")
            return {
                'success': False,
                'error': f'Transcription failed: {str(e)}',
                'text': '',
                'confidence': 0.0,
                'stt_provider': self.provider
            }
    
    def transcribe_from_bytes(self, audio_bytes: bytes, filename: str = "audio.wav") -> Dict[str, Any]:
        """
        Transcribe audio from bytes data
        
        Args:
            audio_bytes: Audio data as bytes
            filename: Original filename for format detection
            
        Returns:
            dict: Transcription result
        """
        if not self.service:
            return {
                'success': False,
                'error': 'STT service not initialized',
                'text': '',
                'confidence': 0.0
            }
        
        try:
            result = self.service.transcribe_from_bytes(audio_bytes, filename)
            # Add provider info to result
            if isinstance(result, dict):
                result['stt_provider'] = self.provider
            return result
            
        except Exception as e:
            logger.error(f"Transcription from bytes failed with {self.provider}: {str(e)}")
            return {
                'success': False,
                'error': f'Transcription failed: {str(e)}',
                'text': '',
                'confidence': 0.0,
                'stt_provider': self.provider
            }
    
    def get_supported_languages(self) -> list:
        """
        Get list of supported languages
        
        Returns:
            list: List of supported language codes
        """
        if self.service and hasattr(self.service, 'get_supported_languages'):
            return self.service.get_supported_languages()
        return ["hi", "en"]
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current STT service
        
        Returns:
            dict: Service information
        """
        base_info = {
            'current_provider': self.provider,
            'available_providers': ['whisper', 'google_web_speech']
        }
        
        if self.service and hasattr(self.service, 'get_model_info'):
            service_info = self.service.get_model_info()
            base_info.update(service_info)
        
        return base_info
    
    def switch_provider(self, new_provider: str) -> bool:
        """
        Switch to a different STT provider
        
        Args:
            new_provider: New provider name ('whisper' or 'google_web_speech')
            
        Returns:
            bool: True if switch was successful
        """
        if new_provider == self.provider:
            logger.info(f"Already using provider: {new_provider}")
            return True
        
        try:
            old_provider = self.provider
            self.provider = new_provider
            self._initialize_service()
            logger.info(f"Successfully switched from {old_provider} to {new_provider}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to provider {new_provider}: {str(e)}")
            # Revert to old provider
            self.provider = old_provider
            return False

# Global service instance
_unified_stt_service = None

def get_unified_stt_service(provider: str = None) -> UnifiedSTTService:
    """
    Get or create the global UnifiedSTTService instance
    
    Args:
        provider: STT provider to use
        
    Returns:
        UnifiedSTTService: The service instance
    """
    global _unified_stt_service
    if _unified_stt_service is None or (provider and _unified_stt_service.provider != provider):
        logger.info(f"Creating new Unified STT service with provider: {provider or Config.STT_PROVIDER}")
        _unified_stt_service = UnifiedSTTService(provider)
    return _unified_stt_service

# Backward compatibility - maintain the same interface as the original STT service
def get_stt_service(model_size: str = "base") -> UnifiedSTTService:
    """
    Get STT service with backward compatibility
    
    Args:
        model_size: Whisper model size (only used if provider is 'whisper')
        
    Returns:
        UnifiedSTTService: The service instance
    """
    # If using Whisper, update the config with the model size
    if Config.STT_PROVIDER == 'whisper':
        Config.WHISPER_MODEL_SIZE = model_size
    
    return get_unified_stt_service()