"""
Deepgram STT Service - Fastest option
Real-time speech recognition with excellent accuracy
"""

import logging
import requests
import json
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class DeepgramSTTService:
    """
    Ultra-fast Speech-to-Text using Deepgram API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Deepgram STT service
        
        Args:
            api_key: Deepgram API key
        """
        self.api_key = api_key or os.getenv('DEEPGRAM_API_KEY')
        self.base_url = "https://api.deepgram.com/v1/listen"
        
        # Configuration for Hindi
        self.params = {
            'model': 'nova-2',  # Latest model
            'language': 'hi',   # Hindi
            'smart_format': 'true',
            'punctuate': 'true',
            'diarize': 'false',
            'confidence': 'true'
        }
        
        logger.info("Initializing Deepgram STT Service")
    
    def transcribe_from_bytes(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Transcribe audio from bytes using Deepgram
        
        Args:
            audio_bytes: Audio data as bytes
            
        Returns:
            dict: Transcription result
        """
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Deepgram API key not provided',
                    'text': '',
                    'confidence': 0.0
                }
            
            headers = {
                'Authorization': f'Token {self.api_key}',
                'Content-Type': 'audio/wav'
            }
            
            logger.info("Starting Deepgram STT transcription...")
            
            response = requests.post(
                self.base_url,
                headers=headers,
                params=self.params,
                data=audio_bytes,
                timeout=10  # Fast timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract transcription
                channels = result.get('results', {}).get('channels', [])
                if not channels:
                    return {
                        'success': False,
                        'error': 'No speech detected',
                        'text': '',
                        'confidence': 0.0
                    }
                
                alternatives = channels[0].get('alternatives', [])
                if not alternatives:
                    return {
                        'success': False,
                        'error': 'No transcription alternatives',
                        'text': '',
                        'confidence': 0.0
                    }
                
                transcript = alternatives[0].get('transcript', '')
                confidence = alternatives[0].get('confidence', 0.0)
                
                logger.info(f"Deepgram STT completed: '{transcript}' (confidence: {confidence:.2f})")
                
                return {
                    'success': True,
                    'text': transcript,
                    'confidence': confidence,
                    'language': 'hi',
                    'provider': 'deepgram'
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Deepgram API error: {response.status_code}',
                    'text': '',
                    'confidence': 0.0
                }
                
        except Exception as e:
            logger.error(f"Deepgram STT failed: {str(e)}")
            return {
                'success': False,
                'error': f'Deepgram STT failed: {str(e)}',
                'text': '',
                'confidence': 0.0
            }