"""
Azure Speech Services STT
Another fast alternative to Whisper
"""

import logging
import azure.cognitiveservices.speech as speechsdk
from typing import Dict, Any, Optional
import tempfile
import os

logger = logging.getLogger(__name__)

class AzureSTTService:
    """
    Fast Speech-to-Text using Azure Speech Services
    """
    
    def __init__(self, subscription_key: Optional[str] = None, region: str = "eastus"):
        """
        Initialize Azure STT service
        
        Args:
            subscription_key: Azure Speech subscription key
            region: Azure region
        """
        self.subscription_key = subscription_key or os.getenv('AZURE_SPEECH_KEY')
        self.region = region
        self.speech_config = None
        
        logger.info(f"Initializing Azure STT Service (region: {region})")
    
    def initialize(self) -> bool:
        """
        Initialize Azure Speech configuration
        
        Returns:
            bool: True if initialized successfully
        """
        try:
            if not self.subscription_key:
                logger.error("Azure Speech subscription key not provided")
                return False
            
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key, 
                region=self.region
            )
            
            # Configure for Hindi
            self.speech_config.speech_recognition_language = "hi-IN"
            
            # Enable detailed results
            self.speech_config.request_word_level_timestamps()
            self.speech_config.enable_dictation()
            
            logger.info("Azure STT initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure STT: {str(e)}")
            return False
    
    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file using Azure Speech
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            dict: Transcription result
        """
        try:
            if not self.speech_config and not self.initialize():
                return {
                    'success': False,
                    'error': 'Azure STT not initialized',
                    'text': '',
                    'confidence': 0.0
                }
            
            # Create audio configuration
            audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            logger.info("Starting Azure STT transcription...")
            
            # Perform recognition
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                # Calculate confidence (Azure doesn't provide direct confidence)
                confidence = 0.9 if len(result.text) > 0 else 0.0
                
                logger.info(f"Azure STT completed: '{result.text}' (confidence: {confidence:.2f})")
                
                return {
                    'success': True,
                    'text': result.text,
                    'confidence': confidence,
                    'language': 'hi-IN',
                    'provider': 'azure'
                }
            
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return {
                    'success': False,
                    'error': 'No speech detected',
                    'text': '',
                    'confidence': 0.0
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Recognition failed: {result.reason}',
                    'text': '',
                    'confidence': 0.0
                }
                
        except Exception as e:
            logger.error(f"Azure STT transcription failed: {str(e)}")
            return {
                'success': False,
                'error': f'Azure STT failed: {str(e)}',
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
        temp_file = None
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file.write(audio_bytes)
            temp_file.flush()
            temp_file.close()
            
            # Transcribe temporary file
            result = self.transcribe(temp_file.name)
            return result
            
        except Exception as e:
            logger.error(f"Azure STT transcription from bytes failed: {str(e)}")
            return {
                'success': False,
                'error': f'Azure STT failed: {str(e)}',
                'text': '',
                'confidence': 0.0
            }
        finally:
            # Clean up
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass

# Global service instance
_azure_stt_service = None

def get_azure_stt_service(subscription_key: Optional[str] = None, region: str = "eastus") -> AzureSTTService:
    """
    Get or create Azure STT service instance
    
    Args:
        subscription_key: Azure subscription key
        region: Azure region
        
    Returns:
        AzureSTTService: Service instance
    """
    global _azure_stt_service
    if _azure_stt_service is None:
        _azure_stt_service = AzureSTTService(subscription_key, region)
    return _azure_stt_service