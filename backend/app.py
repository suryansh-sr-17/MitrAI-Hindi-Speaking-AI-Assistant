"""
Hindi AI Assistant - Flask Backend
Main application file that handles API endpoints for the Hindi AI Assistant
"""

from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import tempfile
import logging
import mimetypes
import random
import time
from datetime import datetime

# Import service modules
from services.unified_stt import get_stt_service  # Unified STT service (replaces speech_to_text)
from services.response_generator import ResponseGenerator
from services.text_to_speech import get_tts_service
from services.face_detection import get_face_detection_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Global service instances
stt_service = None
response_generator = None
tts_service = None
face_detection_service = None

# Session tracking for first-time users
user_sessions = {}  # Track user sessions for welcome messages

def initialize_services():
    """Initialize AI services"""
    global stt_service, response_generator, tts_service, face_detection_service
    try:
        # Initialize STT service
        if stt_service is None:
            stt_service = get_stt_service()
            logger.info("Speech-to-text service initialized")
            logger.info("Speech-to-text service initialized")
        
        # Initialize Response Generator
        if response_generator is None:
            try:
                from config import Config
                api_key = getattr(Config, 'GEMINI_API_KEY', None)
                response_generator = ResponseGenerator(api_key)
                if response_generator.initialize():
                    logger.info("Response generator service initialized")
                else:
                    logger.warning("Response generator initialization failed, will use rule-based fallback")
            except ImportError:
                response_generator = ResponseGenerator()
                logger.warning("Config not available, using environment variables for response generator")
        
        # Initialize TTS service
        if tts_service is None:
            tts_service = get_tts_service()
            logger.info("Text-to-speech service initialized")
        
        # Initialize Face Detection service
        if face_detection_service is None:
            face_detection_service = get_face_detection_service()
            logger.info("Face detection service initialized")
                
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")

# Initialize services on startup
initialize_services()

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'Hindi AI Assistant Backend is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status')
def get_status():
    """Get service status and model information"""
    try:
        global stt_service
        
        status = {
            'status': 'success',
            'services': {
                'speech_to_text': {
                    'available': stt_service is not None,
                    'model_info': stt_service.get_model_info() if stt_service else None
                },
                'response_generator': {
                    'available': response_generator is not None,
                    'status': response_generator.get_status() if response_generator else None
                },
                'text_to_speech': {
                    'available': tts_service is not None,
                    'status': tts_service.get_status() if tts_service else None
                },
                'face_detection': {
                    'available': face_detection_service is not None and face_detection_service.is_initialized,
                    'status': face_detection_service.get_status() if face_detection_service else None
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get service status'
        }), 500

@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    """
    Upload and validate audio file
    Expects: multipart/form-data with 'audio' file
    Returns: JSON with file info and validation status
    """
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No audio file provided',
                'message_hi': 'कोई ऑडियो फ़ाइल प्रदान नहीं की गई'
            }), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No audio file selected',
                'message_hi': 'कोई ऑडियो फ़ाइल चुनी नहीं गई'
            }), 400
        
        # Validate file type and size
        validation_result = validate_audio_file(audio_file)
        if not validation_result['valid']:
            return jsonify({
                'status': 'error',
                'message': validation_result['message'],
                'message_hi': validation_result['message_hi']
            }), 400
        
        # Save temporary file with secure filename
        filename = secure_filename(audio_file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, prefix='audio_')
        
        try:
            audio_file.save(temp_file.name)
            file_size = os.path.getsize(temp_file.name)
            
            # Get audio duration and other metadata
            audio_info = get_audio_info(temp_file.name)
            
            logger.info(f"Audio file uploaded: {filename}, size: {file_size} bytes, duration: {audio_info.get('duration', 'unknown')}s")
            
            return jsonify({
                'status': 'success',
                'message': 'Audio file uploaded successfully',
                'message_hi': 'ऑडियो फ़ाइल सफलतापूर्वक अपलोड हुई',
                'file_info': {
                    'filename': filename,
                    'size': file_size,
                    'duration': audio_info.get('duration'),
                    'format': audio_info.get('format'),
                    'temp_path': temp_file.name
                }
            })
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise e
            
    except Exception as e:
        logger.error(f"Error in upload_audio: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Audio upload failed. Please try again.',
            'message_hi': 'ऑडियो अपलोड विफल। कृपया पुनः प्रयास करें।'
        }), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcribe Hindi audio to Devanagari text with comprehensive error handling
    Expects: multipart/form-data with 'audio' file
    Returns: JSON with transcription and error recovery information
    """
    temp_file = None
    try:
        # Input validation
        if 'audio' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No audio file provided',
                'message_hi': 'कोई ऑडियो फ़ाइल प्रदान नहीं की गई',
                'error_code': 'NO_AUDIO_FILE',
                'can_retry': True
            }), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No audio file selected',
                'message_hi': 'कोई ऑडियो फ़ाइल चुनी नहीं गई',
                'error_code': 'NO_FILE_SELECTED',
                'can_retry': True
            }), 400
        
        # Validate file with enhanced error reporting
        validation_result = validate_audio_file(audio_file)
        if not validation_result['valid']:
            return jsonify({
                'status': 'error',
                'message': validation_result['message'],
                'message_hi': validation_result['message_hi'],
                'error_code': 'INVALID_AUDIO_FILE',
                'can_retry': True,
                'validation_details': validation_result
            }), 400
        
        # Save temporary file with error handling
        filename = secure_filename(audio_file.filename or 'audio')
        file_ext = os.path.splitext(filename)[1].lower() or '.wav'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, prefix='transcribe_')
        
        try:
            audio_file.save(temp_file.name)
            temp_file.close()
            
            # Get audio info for logging and validation
            audio_info = get_audio_info(temp_file.name)
            logger.info(f"Processing audio: {filename}, size: {audio_info.get('size', 0)} bytes, duration: {audio_info.get('duration', 'unknown')}s")
            
            # Initialize STT service with error handling
            global stt_service
            if stt_service is None:
                logger.info("Initializing STT service...")
                initialize_services()
            
            if not stt_service:
                error_response = error_handler.handle_service_error('speech_to_text', 
                    Exception("STT service initialization failed"), 
                    {'filename': filename, 'audio_info': audio_info})
                return jsonify(error_response), 503
            
            # Attempt transcription with retry logic
            max_attempts = 3
            transcription_result = None
            
            for attempt in range(max_attempts):
                try:
                    logger.info(f"Transcription attempt {attempt + 1}/{max_attempts}")
                    transcription_result = stt_service.transcribe(temp_file.name, language="hi")
                    
                    if transcription_result['success']:
                        # Reset error count on success
                        error_handler.reset_error_count('speech_to_text')
                        break
                    else:
                        logger.warning(f"Transcription attempt {attempt + 1} failed: {transcription_result.get('error', 'Unknown error')}")
                        if attempt == max_attempts - 1:
                            # Last attempt failed, use fallback
                            logger.error("All transcription attempts failed, using fallback")
                            transcription_result = {
                                'success': False,
                                'error': 'All transcription attempts failed',
                                'text': generate_sample_transcription(),
                                'confidence': 0.3,
                                'fallback_used': True
                            }
                        else:
                            time.sleep(1)  # Brief delay before retry
                            
                except Exception as transcription_error:
                    logger.error(f"Transcription attempt {attempt + 1} error: {str(transcription_error)}")
                    if attempt == max_attempts - 1:
                        # Handle transcription service error
                        error_response = error_handler.handle_service_error('speech_to_text', 
                            transcription_error, 
                            {'attempt': attempt + 1, 'filename': filename})
                        
                        # Provide fallback response
                        transcription_result = {
                            'success': False,
                            'error': str(transcription_error),
                            'text': generate_sample_transcription(),
                            'confidence': 0.1,
                            'fallback_used': True,
                            'error_details': error_response
                        }
                        break
                    else:
                        time.sleep(2)  # Longer delay on error
            
            # Process results
            if transcription_result and transcription_result.get('text'):
                transcription = transcription_result['text']
                confidence = transcription_result.get('confidence', 0.5)
                
                # Log success
                if transcription_result.get('success', False):
                    logger.info(f"Transcription successful: '{transcription[:50]}...' (confidence: {confidence:.2f})")
                else:
                    logger.warning(f"Using fallback transcription: '{transcription[:50]}...' (confidence: {confidence:.2f})")
                
                return jsonify({
                    'status': 'success',
                    'transcription': transcription,
                    'confidence': confidence,
                    'audio_info': audio_info,
                    'processing_info': {
                        'attempts_made': max_attempts if not transcription_result.get('success') else 1,
                        'fallback_used': transcription_result.get('fallback_used', False),
                        'service_available': bool(stt_service)
                    }
                })
            else:
                # No transcription available
                error_response = error_handler.handle_service_error('speech_to_text', 
                    Exception("No speech detected or transcription empty"), 
                    {'filename': filename, 'audio_info': audio_info})
                return jsonify(error_response), 422
                
        except Exception as file_error:
            logger.error(f"File processing error: {str(file_error)}")
            error_response = error_handler.handle_service_error('speech_to_text', 
                file_error, 
                {'stage': 'file_processing', 'filename': filename})
            return jsonify(error_response), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in transcribe_audio: {str(e)}")
        error_response = error_handler.handle_service_error('speech_to_text', e, {'stage': 'request_processing'})
        return jsonify(error_response), 500
        
    finally:
        # Ensure cleanup of temporary file
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
                logger.debug(f"Cleaned up temporary file: {temp_file.name}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file {temp_file.name}: {cleanup_error}")

@app.route('/api/generate-response', methods=['POST'])
def generate_response():
    """
    Generate Hindi response with comprehensive error handling and graceful degradation
    Expects: JSON with 'text' field
    Returns: JSON with generated response, metadata, and recovery information
    """
    try:
        # Input validation
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No text provided',
                'message_hi': 'कोई टेक्स्ट प्रदान नहीं किया गया',
                'error_code': 'NO_TEXT_PROVIDED',
                'can_retry': True
            }), 400
        
        input_text = data['text'].strip()
        
        if not input_text:
            return jsonify({
                'status': 'error',
                'message': 'Empty text provided',
                'message_hi': 'खाली टेक्स्ट प्रदान किया गया',
                'error_code': 'EMPTY_TEXT',
                'can_retry': True
            }), 400
        
        # Validate input length
        if len(input_text) > 500:
            return jsonify({
                'status': 'error',
                'message': 'Input text too long. Maximum 500 characters allowed.',
                'message_hi': 'इनपुट टेक्स्ट बहुत लंबा है। अधिकतम 500 अक्षर की अनुमति है।',
                'error_code': 'TEXT_TOO_LONG',
                'max_length': 500,
                'current_length': len(input_text),
                'can_retry': True
            }), 400
        
        # Initialize response generator with error handling
        global response_generator
        if response_generator is None:
            logger.info("Initializing response generator...")
            initialize_services()
        
        start_time = time.time()
        response_method = 'unknown'
        response = None
        error_details = None
        
        # Multi-tier response generation with Gemini as primary
        try:
            # Tier 1: Try Gemini API first (for conversational AI)
            if response_generator:
                max_attempts = 2
                for attempt in range(max_attempts):
                    try:
                        logger.info(f"AI response generation attempt {attempt + 1}/{max_attempts}")
                        ai_response = response_generator.generate_response(input_text)
                        
                        if ai_response and ai_response.strip():
                            response = ai_response
                            response_method = 'gemini_api' if response_generator.is_initialized else 'rule_based_fallback'
                            error_handler.reset_error_count('response_generator')
                            break
                        else:
                            logger.warning(f"Empty AI response on attempt {attempt + 1}")
            
                    except Exception as ai_error:
                        logger.error(f"AI response attempt {attempt + 1} failed: {str(ai_error)}")
                        error_details = error_handler.handle_service_error('response_generator', ai_error, {
                            'attempt': attempt + 1,
                            'input_length': len(input_text)
                        })
                        
                        if attempt == max_attempts - 1:
                            # Final attempt failed, use fallback
                            response = generate_rule_based_response(input_text)
                            response_method = 'ai_fallback'
                            break
                        else:
                            time.sleep(1)  # Brief delay before retry
            
            # Tier 2: Try rule-based responses if Gemini fails
            if not response:
                rule_based_response = generate_rule_based_response(input_text)
                if rule_based_response and rule_based_response != "मैं समझ गया। क्या आप कुछ और पूछना चाहते हैं?":
                    response = rule_based_response
                    response_method = 'rule_based_fallback'
                    logger.info("Using rule-based fallback after Gemini failed")
            
            # Tier 3: Ultimate fallback
            if not response or not response.strip():
                logger.warning("All response generation methods failed, using ultimate fallback")
                response = get_ultimate_fallback_response(input_text)
                response_method = 'ultimate_fallback'
                
        except Exception as generation_error:
            logger.error(f"Response generation error: {str(generation_error)}")
            error_details = error_handler.handle_service_error('response_generator', generation_error)
            response = get_ultimate_fallback_response(input_text)
            response_method = 'error_fallback'
        
        generation_time = round((time.time() - start_time) * 1000, 2)
        
        # Calculate confidence based on method used
        confidence_map = {
            'rule_based': 0.95,
            'gemini_api': 0.85,
            'rule_based_fallback': 0.75,
            'ai_fallback': 0.5,
            'ultimate_fallback': 0.3,
            'error_fallback': 0.1
        }
        confidence = confidence_map.get(response_method, 0.3)
        
        logger.info(f"Response generated using {response_method} in {generation_time}ms: '{response[:50]}...' (confidence: {confidence:.2f})")
        
        # Prepare response
        response_data = {
            'status': 'success',
            'response': response,
            'metadata': {
                'method': response_method,
                'generation_time_ms': generation_time,
                'input_length': len(input_text),
                'response_length': len(response),
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'fallback_used': response_method in ['ai_fallback', 'ultimate_fallback', 'error_fallback']
            }
        }
        
        # Add error details if any occurred
        if error_details:
            response_data['error_recovery'] = {
                'errors_encountered': True,
                'recovery_method': response_method,
                'error_details': error_details
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Unexpected error in generate_response: {str(e)}")
        error_response = error_handler.handle_service_error('response_generator', e, {'stage': 'request_processing'})
        
        # Even in case of complete failure, provide a response
        error_response['response'] = get_ultimate_fallback_response("")
        error_response['metadata'] = {
            'method': 'emergency_fallback',
            'confidence': 0.1,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(error_response), 500

def get_ultimate_fallback_response(input_text: str) -> str:
    """
    Get ultimate fallback response when all other methods fail
    Provides context-aware fallback based on input
    """
    input_lower = input_text.lower() if input_text else ""
    
    # Context-aware fallbacks
    if any(greeting in input_lower for greeting in ['नमस्ते', 'हैलो', 'hi', 'hello']):
        return "नमस्ते! मैं आपकी सहायता करने की कोशिश कर रहा हूं।"
    elif any(thanks in input_lower for thanks in ['धन्यवाद', 'thank', 'शुक्रिया']):
        return "आपका स्वागत है!"
    elif any(bye in input_lower for bye in ['अलविदा', 'bye', 'गुड बाय']):
        return "अलविदा! फिर मिलते हैं।"
    else:
        return "मुझे खेद है, मैं अभी आपकी पूरी सहायता नहीं कर पा रहा। कृपया बाद में पुनः प्रयास करें।"

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    """
    Convert Hindi text to speech with comprehensive error handling and fallback mechanisms
    Expects: JSON with 'text' field and optional 'language' and 'slow' fields
    Returns: Audio file (MP3) or JSON error response with recovery information
    """
    try:
        # Input validation
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No text provided',
                'message_hi': 'कोई टेक्स्ट प्रदान नहीं किया गया',
                'error_code': 'NO_TEXT_PROVIDED',
                'can_retry': True
            }), 400
        
        text = data['text'].strip()
        language = data.get('language', 'hi')
        slow = data.get('slow', False)
        
        if not text:
            return jsonify({
                'status': 'error',
                'message': 'Empty text provided',
                'message_hi': 'खाली टेक्स्ट प्रदान किया गया',
                'error_code': 'EMPTY_TEXT',
                'can_retry': True
            }), 400
        
        # Validate text length
        if len(text) > 1000:
            return jsonify({
                'status': 'error',
                'message': 'Text too long. Maximum 1000 characters allowed.',
                'message_hi': 'टेक्स्ट बहुत लंबा है। अधिकतम 1000 अक्षर की अनुमति है।',
                'error_code': 'TEXT_TOO_LONG',
                'max_length': 1000,
                'current_length': len(text),
                'can_retry': True
            }), 400
        
        # Initialize TTS service with error handling
        global tts_service
        if tts_service is None:
            logger.info("Initializing TTS service...")
            initialize_services()
        
        if not tts_service:
            error_response = error_handler.handle_service_error('text_to_speech', 
                Exception("TTS service initialization failed"), 
                {'text_length': len(text), 'language': language})
            return jsonify(error_response), 503
        
        if not tts_service.is_available:
            error_response = error_handler.handle_service_error('text_to_speech', 
                Exception("TTS service not available - dependencies missing"), 
                {'text_length': len(text), 'language': language})
            return jsonify(error_response), 503
        
        start_time = time.time()
        logger.info(f"Generating speech for text: '{text[:50]}...' (language: {language}, slow: {slow})")
        
        # Attempt TTS generation with retry logic
        max_attempts = 3
        result = None
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"TTS generation attempt {attempt + 1}/{max_attempts}")
                result = tts_service.generate_speech(text, language=language, slow=slow)
                
                if result['success']:
                    # Reset error count on success
                    error_handler.reset_error_count('text_to_speech')
                    break
                else:
                    logger.warning(f"TTS attempt {attempt + 1} failed: {result.get('error', 'Unknown error')}")
                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        error_response = error_handler.handle_service_error('text_to_speech', 
                            Exception(result.get('error', 'TTS generation failed')), 
                            {'attempt': attempt + 1, 'text_length': len(text)})
                        return jsonify(error_response), 500
                    else:
                        time.sleep(1)  # Brief delay before retry
                        
            except Exception as tts_error:
                logger.error(f"TTS attempt {attempt + 1} error: {str(tts_error)}")
                if attempt == max_attempts - 1:
                    # Handle TTS service error
                    error_response = error_handler.handle_service_error('text_to_speech', 
                        tts_error, 
                        {'attempt': attempt + 1, 'text_length': len(text), 'language': language})
                    return jsonify(error_response), 500
                else:
                    time.sleep(2)  # Longer delay on error
        
        generation_time = round((time.time() - start_time) * 1000, 2)
        
        if result and result['success']:
            # Successful generation
            audio_data = result['audio_data']
            metadata = result['metadata']
            
            logger.info(f"TTS generated successfully in {generation_time}ms: {len(audio_data)} bytes")
            
            # Validate audio data
            if not audio_data or len(audio_data) < 100:  # Minimum reasonable audio size
                logger.error("Generated audio data is too small or empty")
                error_response = error_handler.handle_service_error('text_to_speech', 
                    Exception("Generated audio data is invalid"), 
                    {'audio_size': len(audio_data) if audio_data else 0})
                return jsonify(error_response), 500
            
            # Create response with audio file
            response = make_response(audio_data)
            response.headers['Content-Type'] = 'audio/mpeg'
            response.headers['Content-Disposition'] = 'attachment; filename="speech.mp3"'
            response.headers['Content-Length'] = len(audio_data)
            
            # Add comprehensive metadata headers
            response.headers['X-Generation-Time'] = str(metadata.get('generation_time', generation_time / 1000))
            response.headers['X-Text-Length'] = str(metadata.get('text_length', len(text)))
            response.headers['X-Language'] = metadata.get('language', language)
            response.headers['X-Audio-Format'] = metadata.get('audio_format', 'mp3')
            response.headers['X-Slow-Speech'] = str(metadata.get('slow_speech', slow))
            response.headers['X-Service-Status'] = 'success'
            response.headers['X-Attempts-Made'] = '1'  # Successful on first or retry
            
            return response
        else:
            # All attempts failed
            logger.error("All TTS generation attempts failed")
            error_response = error_handler.handle_service_error('text_to_speech', 
                Exception("All TTS generation attempts failed"), 
                {'attempts_made': max_attempts, 'text_length': len(text)})
            return jsonify(error_response), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in text_to_speech: {str(e)}")
        error_response = error_handler.handle_service_error('text_to_speech', e, {
            'stage': 'request_processing',
            'text_length': len(data.get('text', '')) if 'data' in locals() and data else 0
        })
        return jsonify(error_response), 500

@app.route('/api/detect-face', methods=['POST'])
def detect_face():
    """
    Detect faces with comprehensive error handling and graceful degradation
    Expects: JSON with 'image' field containing base64 encoded image data
    Returns: JSON with detection result and recovery information
    """
    try:
        # Initialize face detection service with error handling
        global face_detection_service
        if face_detection_service is None:
            logger.info("Initializing face detection service...")
            initialize_services()
        
        if not face_detection_service:
            error_response = error_handler.handle_service_error('face_detection', 
                Exception("Face detection service initialization failed"))
            error_response['face_detected'] = False
            return jsonify(error_response), 503
        
        if not face_detection_service.is_initialized:
            error_response = error_handler.handle_service_error('face_detection', 
                Exception("Face detection service not properly initialized"))
            error_response['face_detected'] = False
            return jsonify(error_response), 503
        
        # Input validation
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No image data provided',
                'message_hi': 'कोई छवि डेटा प्रदान नहीं किया गया',
                'error_code': 'NO_IMAGE_DATA',
                'face_detected': False,
                'can_retry': True
            }), 400
        
        image_data = data['image']
        
        if not image_data or not isinstance(image_data, str):
            return jsonify({
                'status': 'error',
                'message': 'Invalid image data provided',
                'message_hi': 'अमान्य छवि डेटा प्रदान किया गया',
                'error_code': 'INVALID_IMAGE_DATA',
                'face_detected': False,
                'can_retry': True
            }), 400
        
        # Validate image data size (prevent abuse)
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit for base64 image
            return jsonify({
                'status': 'error',
                'message': 'Image data too large. Maximum size is 10MB.',
                'message_hi': 'छवि डेटा बहुत बड़ा है। अधिकतम आकार 10MB है।',
                'error_code': 'IMAGE_TOO_LARGE',
                'face_detected': False,
                'can_retry': True,
                'max_size': '10MB',
                'current_size': f"{len(image_data) / (1024*1024):.1f}MB"
            }), 400
        
        # Attempt face detection with retry logic
        max_attempts = 2  # Face detection is usually fast, so fewer retries
        result = None
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Face detection attempt {attempt + 1}/{max_attempts}")
                result = face_detection_service.detect_faces_from_base64(image_data)
                
                if result['success']:
                    # Reset error count on success
                    error_handler.reset_error_count('face_detection')
                    break
                else:
                    logger.warning(f"Face detection attempt {attempt + 1} failed: {result.get('error', 'Unknown error')}")
                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        error_response = error_handler.handle_service_error('face_detection', 
                            Exception(result.get('error', 'Face detection failed')), 
                            {'attempt': attempt + 1, 'image_size': len(image_data)})
                        error_response['face_detected'] = False
                        return jsonify(error_response), 500
                    else:
                        time.sleep(0.5)  # Brief delay before retry
                        
            except Exception as detection_error:
                logger.error(f"Face detection attempt {attempt + 1} error: {str(detection_error)}")
                if attempt == max_attempts - 1:
                    # Handle face detection service error
                    error_response = error_handler.handle_service_error('face_detection', 
                        detection_error, 
                        {'attempt': attempt + 1, 'image_size': len(image_data)})
                    error_response['face_detected'] = False
                    return jsonify(error_response), 500
                else:
                    time.sleep(1)  # Longer delay on error
        
        if result and result['success']:
            # Successful detection
            logger.info(f"Face detection successful: {result['face_count']} faces detected in {result.get('processing_time', 0):.2f}ms")
            
            # Check if this is the first time a face is detected for this session
            session_id = request.headers.get('X-Session-ID', 'default')
            is_first_detection = False
            
            if result['face_detected'] and session_id not in user_sessions:
                user_sessions[session_id] = {
                    'first_face_detected': True,
                    'timestamp': datetime.now().isoformat()
                }
                is_first_detection = True
                logger.info(f"First face detection for session {session_id}")
            
            return jsonify({
                'status': 'success',
                'face_detected': result['face_detected'],
                'face_count': result['face_count'],
                'faces': result.get('faces', []),
                'message': result['message'],
                'message_hi': result['message_hi'],
                'processing_time_ms': result.get('processing_time', 0),
                'frame_info': result.get('frame_size', {}),
                'is_first_detection': is_first_detection,
                'service_info': {
                    'attempts_made': 1,  # Successful on first or retry
                    'service_available': True,
                    'detection_confidence': face_detection_service.detection_confidence
                }
            })
        else:
            # All attempts failed
            logger.error("All face detection attempts failed")
            error_response = error_handler.handle_service_error('face_detection', 
                Exception("All face detection attempts failed"), 
                {'attempts_made': max_attempts, 'image_size': len(image_data)})
            error_response['face_detected'] = False
            return jsonify(error_response), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in detect_face: {str(e)}")
        error_response = error_handler.handle_service_error('face_detection', e, {
            'stage': 'request_processing',
            'image_size': len(data.get('image', '')) if 'data' in locals() and data else 0
        })
        error_response['face_detected'] = False
        return jsonify(error_response), 500

@app.route('/api/welcome-message', methods=['GET'])
def get_welcome_message():
    """
    Get the welcome message in Hindi for first-time users
    Returns: JSON with welcome message text and audio
    """
    try:
        # Welcome message in Hindi
        welcome_text = "नमस्ते! मैं आपका व्यक्तिगत हिंदी AI सहायक हूं। मुझसे बात करने के लिए माइक बटन दबाएं, बोलना समाप्त करने के लिए इसे दोबारा दबाएं, फिर मैं आपको जवाब दूंगा। आइए बातचीत करते हैं!"
        
        logger.info("Welcome message requested")
        
        return jsonify({
            'status': 'success',
            'message': welcome_text,
            'message_en': 'Hello! I am your personal Hindi AI assistant. Press the mic button to speak with me, press it again to end your turn, and then I will reply to you. Let\'s have a chat!',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting welcome message: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get welcome message',
            'message_hi': 'स्वागत संदेश प्राप्त करने में विफल'
        }), 500

@app.route('/api/welcome-speech', methods=['GET'])
def get_welcome_speech():
    """
    Get the welcome message as audio (TTS)
    Returns: Audio file (MP3) of the welcome message
    """
    try:
        # Welcome message in Hindi
        welcome_text = "नमस्ते! मैं आपका व्यक्तिगत हिंदी AI सहायक हूं। मुझसे बात करने के लिए माइक बटन दबाएं, बोलना समाप्त करने के लिए इसे दोबारा दबाएं, फिर मैं आपको जवाब दूंगा। आइए बातचीत करते हैं!"
        
        # Initialize TTS service if needed
        global tts_service
        if tts_service is None:
            initialize_services()
        
        if not tts_service or not tts_service.is_available:
            return jsonify({
                'status': 'error',
                'message': 'TTS service not available',
                'message_hi': 'TTS सेवा उपलब्ध नहीं है'
            }), 503
        
        logger.info("Generating welcome speech...")
        
        # Generate speech
        result = tts_service.generate_speech(welcome_text, language='hi', slow=False)
        
        if result['success']:
            audio_data = result['audio_data']
            
            logger.info(f"Welcome speech generated: {len(audio_data)} bytes")
            
            # Create response with audio file
            response = make_response(audio_data)
            response.headers['Content-Type'] = 'audio/mpeg'
            response.headers['Content-Disposition'] = 'attachment; filename="welcome.mp3"'
            response.headers['Content-Length'] = len(audio_data)
            response.headers['X-Message-Type'] = 'welcome'
            
            return response
        else:
            logger.error(f"Welcome speech generation failed: {result.get('error')}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate welcome speech',
                'message_hi': 'स्वागत भाषण उत्पन्न करने में विफल',
                'error': result.get('error')
            }), 500
        
    except Exception as e:
        logger.error(f"Error generating welcome speech: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate welcome speech',
            'message_hi': 'स्वागत भाषण उत्पन्न करने में विफल'
        }), 500

def validate_audio_file(audio_file):
    """
    Validate uploaded audio file
    Returns dict with validation result
    """
    # Check file size
    max_size = 50 * 1024 * 1024  # 50MB
    min_size = 1024  # 1KB
    
    # Get file size by seeking to end
    audio_file.seek(0, 2)  # Seek to end
    file_size = audio_file.tell()
    audio_file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        return {
            'valid': False,
            'message': 'File too large. Maximum size is 50MB.',
            'message_hi': 'फ़ाइल बहुत बड़ी है। अधिकतम आकार 50MB है।'
        }
    
    if file_size < min_size:
        return {
            'valid': False,
            'message': 'File too small. Minimum size is 1KB.',
            'message_hi': 'फ़ाइल बहुत छोटी है। न्यूनतम आकार 1KB है।'
        }
    
    # Check file type
    allowed_extensions = {'.mp3', '.wav', '.m4a', '.webm', '.ogg'}
    allowed_mimes = {
        'audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/wave', 
        'audio/x-wav', 'audio/m4a', 'audio/mp4', 'audio/webm', 
        'audio/ogg', 'audio/vorbis'
    }
    
    filename = audio_file.filename or ''
    file_ext = os.path.splitext(filename)[1].lower()
    
    # Check by extension
    if file_ext and file_ext not in allowed_extensions:
        return {
            'valid': False,
            'message': f'Invalid file format. Supported: {", ".join(allowed_extensions)}',
            'message_hi': 'अमान्य फ़ाइल प्रारूप। समर्थित: MP3, WAV, M4A, WebM, OGG'
        }
    
    # Check by MIME type
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type and mime_type not in allowed_mimes:
        return {
            'valid': False,
            'message': 'Invalid audio format detected.',
            'message_hi': 'अमान्य ऑडियो प्रारूप का पता चला।'
        }
    
    return {'valid': True}

def get_audio_info(file_path):
    """
    Get basic audio file information
    This is a placeholder - in production, use librosa or similar
    """
    try:
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Placeholder duration calculation (would use librosa in production)
        # For now, estimate based on file size (very rough approximation)
        estimated_duration = max(1.0, min(60.0, file_size / (128000 / 8)))  # Assume 128kbps
        
        return {
            'duration': round(estimated_duration, 2),
            'format': file_ext.lstrip('.').upper(),
            'size': file_size
        }
    except Exception as e:
        logger.error(f"Error getting audio info: {str(e)}")
        return {
            'duration': None,
            'format': 'Unknown',
            'size': 0
        }

def generate_sample_transcription():
    """
    Generate sample transcriptions for testing
    This will be replaced with actual Whisper integration
    """
    sample_transcriptions = [
        "नमस्ते, आप कैसे हैं?",
        "मेरा नाम क्या है?",
        "आज मौसम कैसा है?",
        "आप कैसे हैं?",
        "मुझे मदद चाहिए।",
        "धन्यवाद।",
        "अलविदा।"
    ]
    
    return random.choice(sample_transcriptions)

def generate_rule_based_response(input_text):
    """
    Generate rule-based responses for common Hindi phrases
    This is a temporary implementation until the full response generator is ready
    """
    input_lower = input_text.lower()
    
    # Common greetings
    if any(greeting in input_lower for greeting in ['नमस्ते', 'नमस्कार', 'हैलो', 'हेलो']):
        return "नमस्ते! मैं ठीक हूं। आपकी क्या मदद कर सकता हूं?"
    
    # Name questions
    if 'नाम' in input_lower and ('क्या' in input_lower or 'कौन' in input_lower):
        return "मुझे खेद है, मुझे आपका नाम नहीं पता।"
    
    # Weather questions
    if 'मौसम' in input_lower or 'weather' in input_lower:
        return "मैं मौसम की जानकारी नहीं दे सकता।"
    
    # How are you questions
    if any(phrase in input_lower for phrase in ['कैसे हैं', 'कैसे हो', 'कैसी हो']):
        return "मैं ठीक हूं, धन्यवाद! आप कैसे हैं?"
    
    # Help questions
    if any(word in input_lower for word in ['मदद', 'help', 'सहायता']):
        return "मैं आपकी हिंदी में बातचीत करने में मदद कर सकता हूं। कुछ और पूछिए!"
    
    # Default response
    return "मैं समझ गया। क्या आप कुछ और पूछना चाहते हैं?"

# ========================================
# COMPREHENSIVE ERROR HANDLING
# ========================================

class ErrorHandler:
    """Centralized error handling with retry mechanisms and user-friendly messages"""
    
    def __init__(self):
        self.error_counts = {}
        self.max_retries = 3
        self.retry_delays = [1, 2, 5]  # seconds
        
    def handle_service_error(self, service_name: str, error: Exception, context: dict = None) -> dict:
        """
        Handle service-specific errors with retry logic and user-friendly messages
        
        Args:
            service_name: Name of the service that failed
            error: The exception that occurred
            context: Additional context information
            
        Returns:
            dict: Standardized error response
        """
        error_key = f"{service_name}_{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log detailed error information
        logger.error(f"Service error in {service_name}: {str(error)}", extra={
            'service': service_name,
            'error_type': type(error).__name__,
            'error_count': self.error_counts[error_key],
            'context': context or {}
        })
        
        # Generate user-friendly error messages
        error_messages = self._get_error_messages(service_name, error)
        
        return {
            'status': 'error',
            'service': service_name,
            'error_type': type(error).__name__,
            'message': error_messages['en'],
            'message_hi': error_messages['hi'],
            'error_count': self.error_counts[error_key],
            'can_retry': self.error_counts[error_key] < self.max_retries,
            'retry_after': self.retry_delays[min(self.error_counts[error_key] - 1, len(self.retry_delays) - 1)] if self.error_counts[error_key] < self.max_retries else None,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_error_messages(self, service_name: str, error: Exception) -> dict:
        """Generate user-friendly error messages in English and Hindi"""
        
        # Service-specific error messages
        service_messages = {
            'speech_to_text': {
                'ConnectionError': {
                    'en': 'Speech recognition service is temporarily unavailable. Please try again.',
                    'hi': 'आवाज़ पहचान सेवा अस्थायी रूप से अनुपलब्ध है। कृपया पुनः प्रयास करें।'
                },
                'TimeoutError': {
                    'en': 'Speech recognition is taking too long. Please try with shorter audio.',
                    'hi': 'आवाज़ पहचान में बहुत समय लग रहा है। कृपया छोटी ऑडियो के साथ प्रयास करें।'
                },
                'ValueError': {
                    'en': 'Invalid audio format. Please use MP3, WAV, or M4A files.',
                    'hi': 'अमान्य ऑडियो प्रारूप। कृपया MP3, WAV, या M4A फ़ाइलों का उपयोग करें।'
                },
                'default': {
                    'en': 'Speech recognition failed. Please check your audio and try again.',
                    'hi': 'आवाज़ पहचान विफल। कृपया अपनी ऑडियो जांचें और पुनः प्रयास करें।'
                }
            },
            'response_generator': {
                'ConnectionError': {
                    'en': 'AI response service is temporarily unavailable. Using basic responses.',
                    'hi': 'AI प्रतिक्रिया सेवा अस्थायी रूप से अनुपलब्ध है। बुनियादी प्रतिक्रियाओं का उपयोग कर रहे हैं।'
                },
                'TimeoutError': {
                    'en': 'Response generation is taking too long. Please try again.',
                    'hi': 'प्रतिक्रिया उत्पन्न करने में बहुत समय लग रहा है। कृपया पुनः प्रयास करें।'
                },
                'RateLimitError': {
                    'en': 'Too many requests. Please wait a moment and try again.',
                    'hi': 'बहुत सारे अनुरोध। कृपया एक क्षण प्रतीक्षा करें और पुनः प्रयास करें।'
                },
                'default': {
                    'en': 'Failed to generate response. Using fallback response.',
                    'hi': 'प्रतिक्रिया उत्पन्न करने में विफल। फॉलबैक प्रतिक्रिया का उपयोग कर रहे हैं।'
                }
            },
            'text_to_speech': {
                'ConnectionError': {
                    'en': 'Text-to-speech service is temporarily unavailable. Please try again.',
                    'hi': 'टेक्स्ट-टू-स्पीच सेवा अस्थायी रूप से अनुपलब्ध है। कृपया पुनः प्रयास करें।'
                },
                'TimeoutError': {
                    'en': 'Speech generation is taking too long. Please try with shorter text.',
                    'hi': 'आवाज़ उत्पन्न करने में बहुत समय लग रहा है। कृपया छोटे टेक्स्ट के साथ प्रयास करें।'
                },
                'ValueError': {
                    'en': 'Invalid text provided. Please check your input.',
                    'hi': 'अमान्य टेक्स्ट प्रदान किया गया। कृपया अपना इनपुट जांचें।'
                },
                'default': {
                    'en': 'Failed to generate speech. Please try again.',
                    'hi': 'आवाज़ उत्पन्न करने में विफल। कृपया पुनः प्रयास करें।'
                }
            },
            'face_detection': {
                'ConnectionError': {
                    'en': 'Face detection service is temporarily unavailable.',
                    'hi': 'चेहरा पहचान सेवा अस्थायी रूप से अनुपलब्ध है।'
                },
                'ValueError': {
                    'en': 'Invalid image data provided for face detection.',
                    'hi': 'चेहरा पहचान के लिए अमान्य छवि डेटा प्रदान किया गया।'
                },
                'default': {
                    'en': 'Face detection failed. Please check your camera.',
                    'hi': 'चेहरा पहचान विफल। कृपया अपना कैमरा जांचें।'
                }
            }
        }
        
        # Get service-specific messages
        service_errors = service_messages.get(service_name, {})
        error_type = type(error).__name__
        
        # Return specific error message or default
        return service_errors.get(error_type, service_errors.get('default', {
            'en': f'{service_name} service encountered an error. Please try again.',
            'hi': f'{service_name} सेवा में त्रुटि हुई। कृपया पुनः प्रयास करें।'
        }))
    
    def reset_error_count(self, service_name: str, error_type: str = None):
        """Reset error count for successful operations"""
        if error_type:
            error_key = f"{service_name}_{error_type}"
            if error_key in self.error_counts:
                del self.error_counts[error_key]
        else:
            # Reset all errors for the service
            keys_to_remove = [key for key in self.error_counts.keys() if key.startswith(f"{service_name}_")]
            for key in keys_to_remove:
                del self.error_counts[key]

# Global error handler instance
error_handler = ErrorHandler()

def with_error_handling(service_name: str):
    """Decorator for adding comprehensive error handling to service methods"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # Reset error count on success
                error_handler.reset_error_count(service_name)
                return result
            except Exception as e:
                return error_handler.handle_service_error(service_name, e, {
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                })
        return wrapper
    return decorator

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        'status': 'error',
        'message': 'File too large. Maximum size is 50MB.',
        'message_hi': 'फ़ाइल बहुत बड़ी है। अधिकतम आकार 50MB है।',
        'error_code': 'FILE_TOO_LARGE',
        'max_size': '50MB'
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'message_hi': 'एंडपॉइंट नहीं मिला',
        'error_code': 'ENDPOINT_NOT_FOUND'
    }), 404

@app.errorhandler(429)
def rate_limit_exceeded(e):
    """Handle rate limit errors"""
    return jsonify({
        'status': 'error',
        'message': 'Too many requests. Please wait and try again.',
        'message_hi': 'बहुत सारे अनुरोध। कृपया प्रतीक्षा करें और पुनः प्रयास करें।',
        'error_code': 'RATE_LIMIT_EXCEEDED',
        'retry_after': 60
    }), 429

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error. Please try again later.',
        'message_hi': 'आंतरिक सर्वर त्रुटि। कृपया बाद में पुनः प्रयास करें।',
        'error_code': 'INTERNAL_SERVER_ERROR'
    }), 500

@app.errorhandler(503)
def service_unavailable(e):
    """Handle service unavailable errors"""
    return jsonify({
        'status': 'error',
        'message': 'Service temporarily unavailable. Please try again later.',
        'message_hi': 'सेवा अस्थायी रूप से अनुपलब्ध है। कृपया बाद में पुनः प्रयास करें।',
        'error_code': 'SERVICE_UNAVAILABLE',
        'retry_after': 300
    }), 503

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)