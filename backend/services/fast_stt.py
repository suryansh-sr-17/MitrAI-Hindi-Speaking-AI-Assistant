"""
Fast STT Service - Unified interface for multiple STT providers
Automatically falls back to alternatives if one fails
"""

import logging
from typing import Dict, Any, Optional
from .google_stt import get_google_stt_service
from .azure_stt import get_azure_stt_service  
from .deepgram_stt import DeepgramSTTService
from .speech_to_text import get_stt_service  # Whisper fallback

logger = logging.getLogger(__name__)

class FastSTTService:
    """
    Unified STT service with multiple provider support and automatic fallback
    """
    
    def __init__(self, preferred_provider: str = "deepgram"):
        """
        Initialize with preferred provider
        
        Args:
            preferred_provider: 'deepgram', 'google', 'azure', or 'whisper'
        """
        self.preferred_provider = preferred_provider
        self.providers = {}
        
        logger.info(f"Initializing Fast STT Service (preferred: {preferred_provider})")
    
    def _get_provider(self, provider_name: str):
        """Get or create provider instance"""
        if provider_name not in self.providers:
            if provider_name == "deepgram":
                self.providers[provider_name] = DeepgramSTTService()
            elif provider_name == "google":
                self.providers[provider_name] = get_google_stt_service()
            elif provider_name == "azure":
                self.providers[provider_name] = get_azure_stt_service()
            elif provider_name == "whisper":
                self.providers[provider_name] = get_stt_service("tiny")  # Use tiny model for speed
            
        return self.providers.get(provider_name)
    
    def transcribe_from_bytes(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Transcribe audio with automatic provider fallback
        
        Args:
            audio_bytes: Audio data as bytes
            
        Returns:
            dict: Transcription result
        """
        # Try providers in order of preference
        provider_order = [self.preferred_provider]
        
        # Add fallback providers
        if self.preferred_provider != "deepgram":
            provider_order.append("deepgram")
        if self.preferred_provider != "google":
            provider_order.append("google")
        if self.preferred_provider != "azure":
            provider_order.append("azure")
        if self.preferred_provider != "whisper":
            provider_order.append("whisper")
        
        for provider_name in provider_order:
            try:
                logger.info(f"Trying STT provider: {provider_name}")
                provider = self._get_provider(provider_name)
                
                if provider is None:
                    logger.warning(f"Provider {provider_name} not available")
                    continue
                
                result = provider.transcribe_from_bytes(audio_bytes)
                
                if result.get('success', False):
                    logger.info(f"STT successful with provider: {provider_name}")
                    result['provider_used'] = provider_name
                    return result
                else:
                    logger.warning(f"Provider {provider_name} failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Provider {provider_name} exception: {str(e)}")
                continue
        
        # All providers failed
        return {
            'success': False,
            'error': 'All STT providers failed',
            'text': '',
            'confidence': 0.0,
            'provider_used': 'none'
        }
    
    def get_provider_status(self) -> Dict[str, Any]:
        """
        Check status of all providers
        
        Returns:
            dict: Status of each provider
        """
        status = {}
        
        for provider_name in ["deepgram", "google", "azure", "whisper"]:
            try:
                provider = self._get_provider(provider_name)
                status[provider_name] = {
                    'available': provider is not None,
                    'initialized': hasattr(provider, 'client') or hasattr(provider, 'api_key')
                }
            except Exception as e:
                status[provider_name] = {
                    'available': False,
                    'error': str(e)
                }
        
        return status

# Global service instance
_fast_stt_service = None

def get_fast_stt_service(preferred_provider: str = "deepgram") -> FastSTTService:
    """
    Get or create Fast STT service instance
    
    Args:
        preferred_provider: Preferred STT provider
        
    Returns:
        FastSTTService: Service instance
    """
    global _fast_stt_service
    if _fast_stt_service is None:
        _fast_stt_service = FastSTTService(preferred_provider)
    return _fast_stt_service