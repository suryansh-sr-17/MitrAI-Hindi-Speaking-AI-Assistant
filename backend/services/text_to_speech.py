"""
Text-to-Speech Service using Google Text-to-Speech (gTTS)
Handles Hindi text-to-speech conversion with high-quality voice synthesis
"""

import os
import tempfile
import logging
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime
import io

try:
    from gtts import gTTS
    from pydub import AudioSegment
    from pydub.effects import normalize
    GTTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"gTTS or pydub not available: {e}")
    GTTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class TextToSpeechService:
    """
    Service for converting Hindi text to speech using Google TTS
    Supports Devanagari input with high-quality voice synthesis
    """
    
    def __init__(self):
        """Initialize the TTS service"""
        self.is_available = GTTS_AVAILABLE
        self.supported_languages = ['hi', 'en'] if GTTS_AVAILABLE else []
        self.default_language = 'hi'  # Hindi
        self.audio_format = 'mp3'
        self.sample_rate = 22050
        
        # Performance tracking
        self.generation_count = 0
        self.total_generation_time = 0.0
        self.last_generation_time = None
        
        logger.info(f"TextToSpeechService initialized - Available: {self.is_available}")
    
    def generate_speech(self, text: str, language: str = 'hi', slow: bool = False) -> Dict[str, Any]:
        """
        Generate speech audio from Hindi text
        
        Args:
            text: Text to convert to speech (supports Devanagari)
            language: Language code ('hi' for Hindi, 'en' for English)
            slow: Whether to speak slowly
            
        Returns:
            dict: Result containing audio data and metadata
        """
        start_time = time.time()
        
        try:
            if not self.is_available:
                return {
                    'success': False,
                    'error': 'TTS service not available - gTTS not installed',
                    'audio_data': None,
                    'metadata': {
                        'generation_time': 0,
                        'text_length': len(text),
                        'language': language
                    }
                }
            
            # Validate input
            if not text or not text.strip():
                return {
                    'success': False,
                    'error': 'Empty text provided',
                    'audio_data': None,
                    'metadata': {
                        'generation_time': 0,
                        'text_length': 0,
                        'language': language
                    }
                }
            
            # Clean and prepare text
            clean_text = self._prepare_text(text)
            
            if len(clean_text) > 1000:
                return {
                    'success': False,
                    'error': 'Text too long (maximum 1000 characters)',
                    'audio_data': None,
                    'metadata': {
                        'generation_time': 0,
                        'text_length': len(text),
                        'language': language
                    }
                }
            
            logger.info(f"Generating speech for text: '{clean_text[:50]}...' (language: {language})")
            
            # Generate speech using gTTS
            tts = gTTS(text=clean_text, lang=language, slow=slow)
            
            # Use BytesIO to avoid file system issues
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_data = audio_buffer.read()
            audio_buffer.close()
            
            generation_time = time.time() - start_time
            
            # Update statistics
            self.generation_count += 1
            self.total_generation_time += generation_time
            self.last_generation_time = datetime.now()
            
            logger.info(f"Speech generated successfully in {generation_time:.2f}s")
            
            return {
                'success': True,
                'audio_data': audio_data,
                'metadata': {
                    'generation_time': round(generation_time, 3),
                    'text_length': len(clean_text),
                    'language': language,
                    'audio_format': 'mp3',
                    'slow_speech': slow,
                    'timestamp': self.last_generation_time.isoformat()
                }
            }
            
        except Exception as e:
            generation_time = time.time() - start_time
            logger.error(f"TTS generation failed: {str(e)}")
            
            return {
                'success': False,
                'error': f'TTS generation failed: {str(e)}',
                'audio_data': None,
                'metadata': {
                    'generation_time': round(generation_time, 3),
                    'text_length': len(text),
                    'language': language,
                    'error_type': type(e).__name__
                }
            }
    
    def generate_speech_file(self, text: str, output_path: str, language: str = 'hi', slow: bool = False) -> Dict[str, Any]:
        """
        Generate speech and save to file
        
        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file
            language: Language code
            slow: Whether to speak slowly
            
        Returns:
            dict: Result with file path and metadata
        """
        result = self.generate_speech(text, language, slow)
        
        if result['success']:
            try:
                # Save audio data to file
                with open(output_path, 'wb') as f:
                    f.write(result['audio_data'])
                
                result['file_path'] = output_path
                result['file_size'] = len(result['audio_data'])
                
                logger.info(f"Audio saved to: {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to save audio file: {str(e)}")
                result['success'] = False
                result['error'] = f'Failed to save audio file: {str(e)}'
        
        return result
    
    def _prepare_text(self, text: str) -> str:
        """
        Prepare text for TTS generation
        
        Args:
            text: Raw input text
            
        Returns:
            str: Cleaned and prepared text
        """
        # Remove extra whitespace
        clean_text = ' '.join(text.split())
        
        # Remove or replace problematic characters
        replacements = {
            '…': '...',
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',
            '—': '-'
        }
        
        for old, new in replacements.items():
            clean_text = clean_text.replace(old, new)
        
        return clean_text.strip()
    
    def test_speech_generation(self) -> Dict[str, Any]:
        """
        Test TTS functionality with sample Hindi text
        
        Returns:
            dict: Test results
        """
        test_cases = [
            {
                'text': 'नमस्ते, मैं एक हिंदी AI असिस्टेंट हूं।',
                'language': 'hi',
                'description': 'Hindi greeting'
            },
            {
                'text': 'आज मौसम बहुत अच्छा है।',
                'language': 'hi',
                'description': 'Weather comment'
            },
            {
                'text': 'धन्यवाद और अलविदा।',
                'language': 'hi',
                'description': 'Thank you and goodbye'
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Testing case {i}: {test_case['description']}")
            
            result = self.generate_speech(
                text=test_case['text'],
                language=test_case['language']
            )
            
            test_result = {
                'case': i,
                'description': test_case['description'],
                'text': test_case['text'],
                'success': result['success'],
                'generation_time': result['metadata']['generation_time'],
                'audio_size': len(result['audio_data']) if result['audio_data'] else 0
            }
            
            if not result['success']:
                test_result['error'] = result['error']
            
            results.append(test_result)
        
        # Summary
        successful_tests = sum(1 for r in results if r['success'])
        total_tests = len(results)
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': successful_tests / total_tests if total_tests > 0 else 0,
            'results': results,
            'service_available': self.is_available
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the TTS service
        
        Returns:
            dict: Service status information
        """
        avg_generation_time = (
            self.total_generation_time / self.generation_count 
            if self.generation_count > 0 else 0
        )
        
        return {
            'available': self.is_available,
            'supported_languages': self.supported_languages,
            'default_language': self.default_language,
            'audio_format': self.audio_format,
            'statistics': {
                'total_generations': self.generation_count,
                'total_generation_time': round(self.total_generation_time, 2),
                'average_generation_time': round(avg_generation_time, 3),
                'last_generation': self.last_generation_time.isoformat() if self.last_generation_time else None
            }
        }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get supported languages for TTS
        
        Returns:
            dict: Language codes and names
        """
        return {
            'hi': 'Hindi (हिंदी)',
            'en': 'English'
        }

# Factory function for creating TTS service
def get_tts_service() -> TextToSpeechService:
    """
    Factory function to create and return TTS service instance
    
    Returns:
        TextToSpeechService: Configured TTS service
    """
    return TextToSpeechService()