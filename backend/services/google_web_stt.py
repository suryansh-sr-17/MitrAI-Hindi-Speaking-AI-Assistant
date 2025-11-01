"""
Google Web Speech STT Service
Free alternative to Whisper using SpeechRecognition library
"""

import speech_recognition as sr
import logging
import tempfile
import os
from typing import Dict, Any, Optional
import librosa
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)

class GoogleWebSTTService:
    """
    Speech-to-Text service using Google Web Speech API (free tier)
    Drop-in replacement for Whisper with same interface
    """
    
    def __init__(self):
        """Initialize the Google Web Speech STT service"""
        self.recognizer = sr.Recognizer()
        self.target_sample_rate = 16000
        self.max_duration = 60  # seconds
        
        # Configure recognizer for better Hindi recognition
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.operation_timeout = 10
        
        logger.info("Initializing Google Web Speech STT Service")
    
    def load_model(self) -> bool:
        """
        Load model - compatibility method with Whisper interface
        
        Returns:
            bool: Always True for Google Web Speech (no model to load)
        """
        logger.info("Google Web Speech STT ready (no model loading required)")
        return True
    
    def preprocess_audio(self, audio_path: str) -> Optional[str]:
        """
        Preprocess audio file for optimal recognition
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            str: Path to preprocessed audio file or None if failed
        """
        try:
            # Load audio file
            audio, sample_rate = librosa.load(audio_path, sr=None)
            
            # Log original audio info
            duration = len(audio) / sample_rate
            logger.info(f"Original audio: {duration:.2f}s, {sample_rate}Hz")
            
            # Check duration
            if duration > self.max_duration:
                logger.warning(f"Audio duration ({duration:.2f}s) exceeds maximum ({self.max_duration}s), truncating")
                audio = audio[:int(self.max_duration * sample_rate)]
            
            # Resample to target sample rate if needed
            if sample_rate != self.target_sample_rate:
                logger.info(f"Resampling from {sample_rate}Hz to {self.target_sample_rate}Hz")
                audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=self.target_sample_rate)
            
            # Normalize audio
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio)) * 0.8  # Prevent clipping
            
            # Save preprocessed audio to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav', prefix='google_stt_')
            sf.write(temp_file.name, audio, self.target_sample_rate)
            temp_file.close()
            
            logger.info(f"Preprocessed audio saved: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error preprocessing audio: {str(e)}")
            return None
    
    def transcribe(self, audio_path: str, language: str = "hi") -> Dict[str, Any]:
        """
        Transcribe audio file to text using Google Web Speech
        
        Args:
            audio_path: Path to the audio file
            language: Language code (default: "hi" for Hindi)
            
        Returns:
            dict: Transcription result with same format as Whisper
        """
        preprocessed_file = None
        try:
            # Preprocess audio
            preprocessed_file = self.preprocess_audio(audio_path)
            if preprocessed_file is None:
                return {
                    'success': False,
                    'error': 'Failed to preprocess audio',
                    'text': '',
                    'confidence': 0.0
                }
            
            # Load audio with speech_recognition
            with sr.AudioFile(preprocessed_file) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Record the audio
                audio_data = self.recognizer.record(source)
            
            logger.info(f"Starting Google Web Speech transcription with language: {language}")
            
            # Map language codes
            lang_map = {
                "hi": "hi-IN",  # Hindi (India)
                "en": "en-US",  # English (US)
                "ur": "ur-PK",  # Urdu (Pakistan)
                "bn": "bn-IN",  # Bengali (India)
            }
            
            google_lang = lang_map.get(language, "hi-IN")
            
            # Perform recognition with Google Web Speech
            try:
                transcribed_text = self.recognizer.recognize_google(
                    audio_data, 
                    language=google_lang,
                    show_all=False  # Get only the best result
                )
                
                # Google Web Speech doesn't provide confidence scores
                # Estimate confidence based on text length and content
                confidence = self._estimate_confidence(transcribed_text)
                
                logger.info(f"Google Web Speech completed: '{transcribed_text}' (estimated confidence: {confidence:.2f})")
                
                return {
                    'success': True,
                    'text': transcribed_text,
                    'confidence': confidence,
                    'language': google_lang,
                    'provider': 'google_web_speech',
                    'segments': [],  # Google Web Speech doesn't provide segments
                    'duration': self._get_audio_duration(preprocessed_file)
                }
                
            except sr.UnknownValueError:
                return {
                    'success': False,
                    'error': 'Google Web Speech could not understand the audio',
                    'text': '',
                    'confidence': 0.0
                }
            except sr.RequestError as e:
                return {
                    'success': False,
                    'error': f'Google Web Speech service error: {str(e)}',
                    'text': '',
                    'confidence': 0.0
                }
                
        except Exception as e:
            logger.error(f"Error during Google Web Speech transcription: {str(e)}")
            return {
                'success': False,
                'error': f'Transcription failed: {str(e)}',
                'text': '',
                'confidence': 0.0
            }
        finally:
            # Clean up preprocessed file
            if preprocessed_file and os.path.exists(preprocessed_file):
                try:
                    os.unlink(preprocessed_file)
                except Exception as e:
                    logger.warning(f"Failed to clean up preprocessed file: {str(e)}")
    
    def transcribe_from_bytes(self, audio_bytes: bytes, filename: str = "audio.wav") -> Dict[str, Any]:
        """
        Transcribe audio from bytes data
        
        Args:
            audio_bytes: Audio data as bytes
            filename: Original filename for format detection
            
        Returns:
            dict: Transcription result
        """
        temp_file = None
        try:
            # Create temporary file
            file_ext = os.path.splitext(filename)[1] or '.wav'
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, prefix='google_web_stt_')
            
            # Write audio bytes to temporary file
            temp_file.write(audio_bytes)
            temp_file.flush()
            temp_file.close()
            
            # Transcribe the temporary file
            result = self.transcribe(temp_file.name)
            
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing from bytes: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to process audio bytes: {str(e)}',
                'text': '',
                'confidence': 0.0
            }
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {str(e)}")
    
    def _estimate_confidence(self, text: str) -> float:
        """
        Estimate confidence score based on transcribed text
        
        Args:
            text: Transcribed text
            
        Returns:
            float: Estimated confidence score (0.0 to 1.0)
        """
        if not text or len(text.strip()) == 0:
            return 0.0
        
        # Base confidence
        confidence = 0.7
        
        # Adjust based on text length (longer text usually more reliable)
        text_length = len(text.strip())
        if text_length > 20:
            confidence += 0.2
        elif text_length > 10:
            confidence += 0.1
        
        # Adjust based on Hindi characters (if present, likely more accurate)
        hindi_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
        if hindi_chars > 0:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """
        Get audio duration in seconds
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            float: Duration in seconds
        """
        try:
            audio, sample_rate = librosa.load(audio_path, sr=None)
            return len(audio) / sample_rate
        except Exception:
            return 0.0
    
    def get_supported_languages(self) -> list:
        """
        Get list of supported languages
        
        Returns:
            list: List of supported language codes
        """
        return ["hi", "en", "ur", "bn", "te", "ta", "ml", "kn", "gu", "pa"]
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the service
        
        Returns:
            dict: Service information
        """
        return {
            'provider': 'google_web_speech',
            'model_size': 'cloud',
            'device': 'cloud',
            'loaded': True,
            'target_sample_rate': self.target_sample_rate,
            'max_duration': self.max_duration,
            'free_tier': True,
            'rate_limit': '50 requests per day'
        }

# Global service instance
_google_web_stt_service = None

def get_google_web_stt_service() -> GoogleWebSTTService:
    """
    Get or create the global GoogleWebSTTService instance
    
    Returns:
        GoogleWebSTTService: The service instance
    """
    global _google_web_stt_service
    if _google_web_stt_service is None:
        logger.info("Creating new Google Web STT service")
        _google_web_stt_service = GoogleWebSTTService()
    return _google_web_stt_service