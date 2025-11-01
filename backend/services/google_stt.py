"""
Google Cloud Speech-to-Text Service
Fast and accurate alternative to Whisper for Hindi transcription
"""

import logging
import io
import json
from typing import Dict, Any, Optional
from google.cloud import speech
import tempfile
import os

logger = logging.getLogger(__name__)

class GoogleSTTService:
    """
    Fast Speech-to-Text service using Google Cloud Speech API
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google STT service
        
        Args:
            credentials_path: Path to Google Cloud credentials JSON file
        """
        self.client = None
        self.credentials_path = credentials_path
        
        # Audio configuration
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=16000,
            language_code="hi-IN",  # Hindi (India)
            alternative_language_codes=["en-IN"],  # Fallback to English
            enable_automatic_punctuation=True,
            enable_word_confidence=True,
            model="latest_long",  # Use latest model for better accuracy
        )
        
        logger.info("Initializing Google STT Service")
    
    def initialize(self) -> bool:
        """
        Initialize the Google Speech client
        
        Returns:
            bool: True if initialized successfully
        """
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
            
            self.client = speech.SpeechClient()
            logger.info("Google STT client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Google STT: {str(e)}")
            return False
    
    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file using Google Speech API
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            dict: Transcription result
        """
        try:
            if not self.client and not self.initialize():
                return {
                    'success': False,
                    'error': 'Google STT client not initialized',
                    'text': '',
                    'confidence': 0.0
                }
            
            # Read audio file
            with io.open(audio_path, "rb") as audio_file:
                content = audio_file.read()
            
            audio = speech.RecognitionAudio(content=content)
            
            # Perform transcription
            logger.info("Starting Google STT transcription...")
            response = self.client.recognize(config=self.config, audio=audio)
            
            if not response.results:
                return {
                    'success': False,
                    'error': 'No speech detected',
                    'text': '',
                    'confidence': 0.0
                }
            
            # Get best result
            result = response.results[0]
            alternative = result.alternatives[0]
            
            transcribed_text = alternative.transcript
            confidence = alternative.confidence
            
            logger.info(f"Google STT completed: '{transcribed_text}' (confidence: {confidence:.2f})")
            
            return {
                'success': True,
                'text': transcribed_text,
                'confidence': confidence,
                'language': 'hi-IN',
                'provider': 'google'
            }
            
        except Exception as e:
            logger.error(f"Google STT transcription failed: {str(e)}")
            return {
                'success': False,
                'error': f'Google STT failed: {str(e)}',
                'text': '',
                'confidence': 0.0
            }
    
    def transcribe_from_bytes(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Transcribe audio from bytes
        
        Args:
            audio_bytes: Audio data as bytes
            
        Returns:
            dict: Transcription result
        """
        try:
            if not self.client and not self.initialize():
                return {
                    'success': False,
                    'error': 'Google STT client not initialized',
                    'text': '',
                    'confidence': 0.0
                }
            
            audio = speech.RecognitionAudio(content=audio_bytes)
            
            logger.info("Starting Google STT transcription from bytes...")
            response = self.client.recognize(config=self.config, audio=audio)
            
            if not response.results:
                return {
                    'success': False,
                    'error': 'No speech detected',
                    'text': '',
                    'confidence': 0.0
                }
            
            result = response.results[0]
            alternative = result.alternatives[0]
            
            return {
                'success': True,
                'text': alternative.transcript,
                'confidence': alternative.confidence,
                'language': 'hi-IN',
                'provider': 'google'
            }
            
        except Exception as e:
            logger.error(f"Google STT transcription failed: {str(e)}")
            return {
                'success': False,
                'error': f'Google STT failed: {str(e)}',
                'text': '',
                'confidence': 0.0
            }

# Global service instance
_google_stt_service = None

def get_google_stt_service(credentials_path: Optional[str] = None) -> GoogleSTTService:
    """
    Get or create Google STT service instance
    
    Args:
        credentials_path: Path to credentials file
        
    Returns:
        GoogleSTTService: Service instance
    """
    global _google_stt_service
    if _google_stt_service is None:
        _google_stt_service = GoogleSTTService(credentials_path)
    return _google_stt_service