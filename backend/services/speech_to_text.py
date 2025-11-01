"""
Speech-to-Text Service using OpenAI Whisper
Handles Hindi audio transcription with Devanagari script support
"""

import whisper
import torch
import logging
import os
import tempfile
from typing import Optional, Dict, Any
import librosa
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)

class SpeechToTextService:
    """
    Service for converting Hindi speech to Devanagari text using OpenAI Whisper
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize the speech-to-text service
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
        """
        self.model_size = model_size
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Audio preprocessing settings
        self.target_sample_rate = 16000
        self.max_duration = 60  # seconds
        
        logger.info(f"Initializing SpeechToTextService with model: {model_size}, device: {self.device}")
    
    def load_model(self) -> bool:
        """
        Load the Whisper model
        
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            if self.model is None:
                logger.info(f"Loading Whisper model: {self.model_size}")
                self.model = whisper.load_model(self.model_size, device=self.device)
                logger.info("Whisper model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            return False
    
    def preprocess_audio(self, audio_path: str) -> Optional[np.ndarray]:
        """
        Preprocess audio file for optimal Whisper performance
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            numpy.ndarray: Preprocessed audio data or None if failed
        """
        try:
            # Load audio file
            audio, sample_rate = librosa.load(audio_path, sr=None)
            
            # Log original audio info
            duration = len(audio) / sample_rate
            logger.info(f"Original audio: {duration:.2f}s, {sample_rate}Hz, {len(audio)} samples")
            
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
                audio = audio / np.max(np.abs(audio))
            
            # Apply basic noise reduction (simple high-pass filter)
            audio = self._apply_noise_reduction(audio)
            
            logger.info(f"Preprocessed audio: {len(audio) / self.target_sample_rate:.2f}s, {self.target_sample_rate}Hz")
            return audio
            
        except Exception as e:
            logger.error(f"Error preprocessing audio: {str(e)}")
            return None
    
    def _apply_noise_reduction(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply basic noise reduction to audio
        
        Args:
            audio: Input audio array
            
        Returns:
            numpy.ndarray: Noise-reduced audio
        """
        try:
            # Simple high-pass filter to remove low-frequency noise
            from scipy import signal
            
            # Design high-pass filter (cutoff at 80 Hz)
            nyquist = self.target_sample_rate / 2
            cutoff = 80 / nyquist
            b, a = signal.butter(4, cutoff, btype='high')
            
            # Apply filter
            filtered_audio = signal.filtfilt(b, a, audio)
            return filtered_audio
            
        except ImportError:
            # If scipy is not available, return original audio
            logger.warning("scipy not available, skipping noise reduction")
            return audio
        except Exception as e:
            logger.warning(f"Error applying noise reduction: {str(e)}")
            return audio
    
    def transcribe(self, audio_path: str, language: str = "hi") -> Dict[str, Any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to the audio file
            language: Language code (default: "hi" for Hindi)
            
        Returns:
            dict: Transcription result with text, confidence, and metadata
        """
        try:
            # Load model if not already loaded
            if not self.load_model():
                return {
                    'success': False,
                    'error': 'Failed to load Whisper model',
                    'text': '',
                    'confidence': 0.0
                }
            
            # Preprocess audio
            audio_data = self.preprocess_audio(audio_path)
            if audio_data is None:
                return {
                    'success': False,
                    'error': 'Failed to preprocess audio',
                    'text': '',
                    'confidence': 0.0
                }
            
            # Transcribe with Whisper
            logger.info(f"Starting transcription with language: {language}")
            
            # Ensure audio data is contiguous and has correct dtype
            if not audio_data.flags['C_CONTIGUOUS']:
                audio_data = np.ascontiguousarray(audio_data)
            
            # Ensure float32 dtype for Whisper compatibility
            audio_data = audio_data.astype(np.float32)
            
            # Use Whisper's transcribe method with enhanced Hindi language specification
            result = self.model.transcribe(
                audio_data,
                language=language if language == "hi" else None,  # Force Hindi or auto-detect
                task="transcribe",
                fp16=False,  # Use fp32 for better accuracy
                verbose=True,  # Enable verbose for debugging
                temperature=0.0,  # Use deterministic decoding
                beam_size=5,  # Use beam search for better accuracy
                best_of=5,  # Generate multiple candidates
                patience=1.0,  # Patience for beam search
                length_penalty=1.0,  # Length penalty
                suppress_tokens=[-1],  # Suppress specific tokens
                initial_prompt="नमस्ते, मैं हिंदी में बोल रहा हूं।"  # Hindi prompt to help recognition
            )
            
            # Extract transcription text
            transcribed_text = result.get("text", "").strip()
            
            # Calculate average confidence from segments
            segments = result.get("segments", [])
            if segments:
                avg_confidence = sum(segment.get("avg_logprob", 0) for segment in segments) / len(segments)
                # Convert log probability to confidence score (0-1)
                confidence = max(0.0, min(1.0, (avg_confidence + 1.0) / 2.0))
            else:
                confidence = 0.5  # Default confidence if no segments
            
            # Log results
            logger.info(f"Transcription completed: '{transcribed_text}' (confidence: {confidence:.2f})")
            
            # Validate transcription
            if not transcribed_text or len(transcribed_text.strip()) == 0:
                return {
                    'success': False,
                    'error': 'No speech detected in audio',
                    'text': '',
                    'confidence': 0.0
                }
            
            return {
                'success': True,
                'text': transcribed_text,
                'confidence': confidence,
                'language': result.get("language", language),
                'segments': segments,
                'duration': len(audio_data) / self.target_sample_rate
            }
            
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return {
                'success': False,
                'error': f'Transcription failed: {str(e)}',
                'text': '',
                'confidence': 0.0
            }
        finally:
            # Ensure any file handles are closed
            import gc
            gc.collect()
    
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
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, prefix='whisper_')
            
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
    
    def get_supported_languages(self) -> list:
        """
        Get list of supported languages
        
        Returns:
            list: List of supported language codes
        """
        # Whisper supports many languages, but we focus on Hindi
        return ["hi", "en", "ur", "bn", "te", "ta", "ml", "kn", "gu", "pa"]
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model
        
        Returns:
            dict: Model information
        """
        return {
            'model_size': self.model_size,
            'device': self.device,
            'loaded': self.model is not None,
            'target_sample_rate': self.target_sample_rate,
            'max_duration': self.max_duration
        }

# Global service instance
_stt_service = None

def get_stt_service(model_size: str = "base") -> SpeechToTextService:
    """
    Get or create the global SpeechToTextService instance
    
    Args:
        model_size: Whisper model size
        
    Returns:
        SpeechToTextService: The service instance
    """
    global _stt_service
    if _stt_service is None or _stt_service.model_size != model_size:
        logger.info(f"Creating new STT service with model: {model_size}")
        _stt_service = SpeechToTextService(model_size)
    return _stt_service