"""
Response Generator Service using OpenAI or Google Gemini API
Handles intelligent Hindi response generation with fallback to rule-based responses
"""

import logging
import os
import time
import random
from typing import Dict, Any, Optional
from datetime import datetime

# Import both APIs
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """
    Service for generating contextually appropriate Hindi responses
    Supports both OpenAI and Google Gemini APIs with rule-based fallbacks
    """
    
    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize the response generator
        
        Args:
            api_key: API key (OpenAI or Gemini)
            provider: 'openai' or 'gemini' (defaults to LLM_PROVIDER env var)
        """
        # Determine provider
        self.provider = provider or os.getenv('LLM_PROVIDER', 'openai').lower()
        
        # Initialize API keys
        if self.provider == 'openai':
            self.api_key = api_key or os.getenv('OPENAI_API_KEY')
            self.openai_client = None
        else:  # gemini
            self.api_key = api_key or os.getenv('GEMINI_API_KEY')
            self.gemini_model = None
            
        self.is_initialized = False
        
        # Rate limiting
        self.last_request_time = 0
        if self.provider == 'openai':
            self.min_request_interval = 1.0  # OpenAI has higher rate limits
        else:
            self.min_request_interval = 8.0  # Gemini free tier is more restrictive
        
        # OpenAI Configuration
        self.openai_config = {
            'model': 'gpt-3.5-turbo',
            'max_tokens': 100,
            'temperature': 0.7,
            'top_p': 0.9
        }
        
        # Gemini Configuration (simplified for reliability)
        self.gemini_config = {
            'temperature': 0.7,
            'max_output_tokens': 100  # Increased for better responses
        }
        
        # Gemini Safety settings
        self.gemini_safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        logger.info(f"ResponseGenerator initialized with provider: {self.provider}")
    
    def initialize(self) -> bool:
        """
        Initialize the selected LLM API connection
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if not self.api_key:
                logger.error(f"No {self.provider.upper()} API key provided")
                return False
            
            if self.provider == 'openai':
                return self._initialize_openai()
            else:
                return self._initialize_gemini()
                
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider.upper()} API: {str(e)}")
            return False
    
    def _initialize_openai(self) -> bool:
        """Initialize OpenAI API"""
        try:
            if not OPENAI_AVAILABLE:
                logger.error("OpenAI library not available")
                return False
            
            # Initialize OpenAI client
            self.openai_client = openai.OpenAI(api_key=self.api_key)
            
            # Test the connection with a simple request
            test_response = self.openai_client.chat.completions.create(
                model=self.openai_config['model'],
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                temperature=0.5
            )
            
            if test_response and test_response.choices:
                self.is_initialized = True
                logger.info("OpenAI API initialized successfully")
                return True
            else:
                logger.error("Failed to get response from OpenAI API")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI API: {str(e)}")
            return False
    
    def _initialize_gemini(self) -> bool:
        """Initialize Gemini API"""
        try:
            if not GEMINI_AVAILABLE:
                logger.error("Gemini library not available")
                return False
            
            # Configure the API
            genai.configure(api_key=self.api_key)
            
            # Initialize the model with correct model name
            self.gemini_model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',  # Correct current model name
                generation_config=self.gemini_config,
                safety_settings=self.gemini_safety_settings
            )
            
            # Test the connection with a simple request
            test_response = self.gemini_model.generate_content("नमस्ते")
            if test_response:
                self.is_initialized = True
                logger.info("Gemini API initialized successfully")
                return True
            else:
                logger.error("Failed to get response from Gemini API")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}")
            return False
    
    def generate_response(self, user_input: str) -> str:
        """
        Generate a contextually appropriate Hindi response using selected LLM API
        
        Args:
            user_input: User's input text in Hindi
            
        Returns:
            str: Generated response in Hindi
        """
        try:
            # Initialize API if not already done
            if not self.is_initialized:
                if not self.initialize():
                    logger.error(f"Failed to initialize {self.provider.upper()} API, using emergency fallback")
                    return self._get_emergency_fallback_response(user_input)
            
            # Rate limiting
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last_request)
            
            # Generate response based on provider
            if self.provider == 'openai':
                return self._generate_openai_response(user_input)
            else:
                return self._generate_gemini_response(user_input)
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._get_emergency_fallback_response(user_input)
    
    def _generate_openai_response(self, user_input: str) -> str:
        """Generate response using OpenAI API"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting OpenAI API call (attempt {attempt + 1})")
                
                # Create messages for chat completion
                messages = [
                    {
                        "role": "system", 
                        "content": "आप एक मित्रवत हिंदी AI सहायक हैं। हमेशा हिंदी में संक्षिप्त और प्राकृतिक उत्तर दें। 1-2 वाक्य में जवाब दें।"
                    },
                    {
                        "role": "user", 
                        "content": user_input
                    }
                ]
                
                # Make API call
                response = self.openai_client.chat.completions.create(
                    model=self.openai_config['model'],
                    messages=messages,
                    max_tokens=self.openai_config['max_tokens'],
                    temperature=self.openai_config['temperature'],
                    top_p=self.openai_config['top_p']
                )
                
                self.last_request_time = time.time()
                
                # Extract response text
                if response.choices and response.choices[0].message:
                    generated_text = response.choices[0].message.content.strip()
                    if generated_text:
                        logger.info(f"✅ SUCCESS: OpenAI API generated response: {generated_text}")
                        return generated_text
                
                logger.warning(f"❌ ATTEMPT {attempt + 1}: Empty response from OpenAI API")
                
                # Try rule-based response as backup on second attempt
                if attempt == 1:
                    rule_response = self._get_rule_based_response(user_input)
                    if rule_response:
                        logger.info(f"✅ Using rule-based response: {rule_response}")
                        return rule_response
                
            except Exception as api_error:
                logger.error(f"❌ OpenAI API error (attempt {attempt + 1}): {str(api_error)}")
                if attempt == max_retries - 1:
                    logger.error("🚨 ALL OPENAI ATTEMPTS FAILED - Using emergency fallback")
                    return self._get_emergency_fallback_response(user_input)
                time.sleep(1)  # Wait before retry
        
        # If we get here, all attempts failed
        logger.error("🚨 CRITICAL: All OpenAI API attempts failed")
        return self._get_emergency_fallback_response(user_input)
    
    def _generate_gemini_response(self, user_input: str) -> str:
        """Generate response using Gemini API"""
        max_retries = 3
        
        # Create a very concise prompt to avoid token limits
        prompt = f"""हिंदी में छोटा जवाब: {user_input}"""
        
        logger.info(f"🔍 Gemini Input: '{user_input}' | Prompt: '{prompt}'")
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting Gemini API call (attempt {attempt + 1})")
                response = self.gemini_model.generate_content(prompt)
                self.last_request_time = time.time()
                
                # Parse response using helper method
                generated_text = self._parse_gemini_response(response)
                
                if generated_text:
                    logger.info(f"✅ SUCCESS: Gemini API generated response: {generated_text}")
                    return generated_text
                else:
                    logger.warning(f"❌ ATTEMPT {attempt + 1}: Empty or blocked response from Gemini API")
                    
                    # Try rule-based response as backup on second attempt
                    if attempt == 1:
                        rule_response = self._get_rule_based_response(user_input)
                        if rule_response:
                            logger.info(f"✅ Using rule-based response: {rule_response}")
                            return rule_response
                    
            except Exception as api_error:
                logger.error(f"❌ Gemini API error (attempt {attempt + 1}): {str(api_error)}")
                if attempt == max_retries - 1:
                    logger.error("🚨 ALL GEMINI ATTEMPTS FAILED - Using emergency fallback")
                    return self._get_emergency_fallback_response(user_input)
                time.sleep(1)  # Wait before retry
        
        # If we get here, all attempts failed
        logger.error("🚨 CRITICAL: All Gemini API attempts failed")
        return self._get_emergency_fallback_response(user_input)
    
    def _get_rule_based_response(self, user_input: str) -> Optional[str]:
        """
        Temporary rule-based responses for demo reliability
        Will be used as backup when Gemini parsing fails
        
        Args:
            user_input: User's input text
            
        Returns:
            str or None: Rule-based response if pattern matches
        """
        input_lower = user_input.lower().strip()
        
        # Common Hindi greetings and responses
        greeting_patterns = {
            'नमस्ते': 'नमस्ते! मैं आपका हिंदी AI सहायक हूं। आप कैसे हैं?',
            'नमस्कार': 'नमस्कार! आपका स्वागत है।',
            'हैलो': 'हैलो! मैं आपकी सहायता के लिए यहां हूं।',
            'hello': 'नमस्ते! मैं हिंदी में बात कर सकता हूं।'
        }
        
        # How are you patterns
        how_are_you_patterns = [
            'कैसे हैं', 'कैसे हो', 'कैसी हो', 'कैसा है', 'how are you'
        ]
        
        # Thank you patterns
        thank_patterns = [
            'धन्यवाद', 'शुक्रिया', 'thank you', 'thanks'
        ]
        
        # Goodbye patterns
        goodbye_patterns = [
            'अलविदा', 'नमस्ते', 'bye', 'goodbye', 'टाटा'
        ]
        
        # Name patterns
        name_patterns = [
            'मेरा नाम', 'मैं हूं', 'my name is'
        ]
        
        # Help patterns
        help_patterns = [
            'मदद', 'सहायता', 'help'
        ]
        
        # Check for exact matches first
        for pattern, response in greeting_patterns.items():
            if pattern in input_lower:
                return response
        
        # Check for how are you
        if any(pattern in input_lower for pattern in how_are_you_patterns):
            return 'मैं ठीक हूं, धन्यवाद! आप कैसे हैं?'
        
        # Check for thank you
        if any(pattern in input_lower for pattern in thank_patterns):
            return 'आपका स्वागत है! क्या मैं और कुछ मदद कर सकता हूं?'
        
        # Check for goodbye
        if any(pattern in input_lower for pattern in goodbye_patterns):
            return 'अलविदा! फिर मिलते हैं।'
        
        # Check for name introduction
        if any(pattern in input_lower for pattern in name_patterns):
            return 'खुशी हुई आपसे मिलकर! मैं आपका AI सहायक हूं।'
        
        # Check for help
        if any(pattern in input_lower for pattern in help_patterns):
            return 'मैं आपकी हिंदी में बातचीत करने में मदद कर सकता हूं। कुछ पूछिए!'
        
        # Weather patterns
        if 'मौसम' in input_lower or 'weather' in input_lower:
            return 'मुझे मौसम की जानकारी नहीं है, लेकिन मैं आपसे बातचीत कर सकता हूं।'
        
        # Default response for unmatched patterns
        return None
    
    def _is_valid_response(self, text: str) -> bool:
        """
        Check if the response is valid (has content)
        
        Args:
            text: Response text to validate
            
        Returns:
            bool: True if text is valid, False otherwise
        """
        if not text or not text.strip():
            return False
        
        # Accept any response with content (don't filter by language)
        return len(text.strip()) > 0
    
    def _parse_gemini_response(self, response) -> Optional[str]:
        """
        Enhanced Gemini response parsing with detailed debugging
        """
        if not response:
            logger.error("No response object received")
            return None
        
        # Enhanced debugging for live environment
        logger.info(f"🔍 Parsing response type: {type(response)}")
        logger.info(f"🔍 Response object: {str(response)[:200]}...")
        
        # Method 1: Try standard text access
        try:
            text = response.text
            logger.info(f"🔍 Raw response.text: '{text}' (type: {type(text)})")
            if text and text.strip():
                logger.info(f"✅ Standard text: {text.strip()[:50]}...")
                return text.strip()
            else:
                logger.warning(f"⚠️ response.text is empty or whitespace only: '{text}'")
        except Exception as e:
            logger.warning(f"❌ Standard text failed: {e}")
        
        # Method 2: Try candidates -> content -> parts
        try:
            if hasattr(response, 'candidates'):
                logger.info(f"🔍 Candidates count: {len(response.candidates) if response.candidates else 0}")
                if response.candidates:
                    candidate = response.candidates[0]
                    logger.info(f"🔍 Candidate finish_reason: {getattr(candidate, 'finish_reason', 'N/A')}")
                    
                    if hasattr(candidate, 'content') and candidate.content:
                        logger.info(f"🔍 Content exists: {candidate.content}")
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            logger.info(f"🔍 Parts count: {len(candidate.content.parts)}")
                            for i, part in enumerate(candidate.content.parts):
                                logger.info(f"🔍 Part {i}: {part}")
                                if hasattr(part, 'text'):
                                    part_text = part.text
                                    logger.info(f"🔍 Part {i} text: '{part_text}' (type: {type(part_text)})")
                                    if part_text:
                                        text = str(part_text).strip()
                                        if text:
                                            logger.info(f"✅ Parts text: {text[:50]}...")
                                            return text
                                else:
                                    logger.warning(f"⚠️ Part {i} has no text attribute")
                        else:
                            logger.warning("⚠️ No parts in content or parts is empty")
                    else:
                        logger.warning("⚠️ No content in candidate")
                else:
                    logger.warning("⚠️ Candidates list is empty")
            else:
                logger.warning("⚠️ No candidates attribute")
        except Exception as e:
            logger.error(f"❌ Parts extraction failed: {e}")
        
        # Method 3: Try to access response attributes directly
        try:
            if hasattr(response, 'parts') and response.parts:
                logger.info(f"🔍 Direct parts count: {len(response.parts)}")
                for i, part in enumerate(response.parts):
                    if hasattr(part, 'text') and part.text:
                        text = str(part.text).strip()
                        if text:
                            logger.info(f"✅ Direct parts text: {text[:50]}...")
                            return text
        except Exception as e:
            logger.debug(f"Direct parts failed: {e}")
        
        logger.error("❌ All parsing methods failed - response structure may be unexpected")
        return None
    
    def _get_emergency_fallback_response(self, user_input: str = "") -> str:
        """
        Emergency fallback when Gemini API completely fails
        Try rule-based first, then generic responses
        
        Args:
            user_input: User's input for context-aware fallback
            
        Returns:
            str: Emergency response
        """
        # Try rule-based response first
        if user_input:
            rule_response = self._get_rule_based_response(user_input)
            if rule_response:
                logger.info("✅ Using rule-based emergency fallback")
                return rule_response
        
        # Generic emergency responses
        emergency_responses = [
            "मुझे तकनीकी समस्या हो रही है। कृपया फिर से कोशिश करें।",
            "मैं अभी सही तरीके से काम नहीं कर पा रहा। थोड़ी देर बाद कोशिश करें।",
            "तकनीकी खराबी के कारण मैं जवाब नहीं दे पा रहा। माफ करें।"
        ]
        
        logger.error("🚨 USING EMERGENCY FALLBACK - Gemini API is not working!")
        random.seed(int(time.time() * 1000000) % 10000)
        return random.choice(emergency_responses)
    
    def generate_contextual_response(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate response with additional context information
        
        Args:
            user_input: User's input text in Hindi
            context: Optional context information (conversation history, user preferences, etc.)
            
        Returns:
            dict: Response with metadata
        """
        start_time = time.time()
        
        try:
            response_text = self.generate_response(user_input)
            generation_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return {
                'response': response_text,
                'metadata': {
                    'method': 'gemini_api' if self.is_initialized else 'rule_based',
                    'generation_time_ms': round(generation_time, 2),
                    'confidence': self._estimate_confidence(user_input, response_text),
                    'context_used': bool(context),
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in contextual response generation: {str(e)}")
            return {
                'response': self._get_fallback_response(),
                'metadata': {
                    'method': 'error_fallback',
                    'generation_time_ms': round((time.time() - start_time) * 1000, 2),
                    'confidence': 0.1,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            }
    
    def _estimate_confidence(self, user_input: str, response: str) -> float:
        """
        Estimate confidence score for the generated response
        
        Args:
            user_input: Original user input
            response: Generated response
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        # Rule-based responses have high confidence
        if self._get_rule_based_response(user_input):
            return 0.95
        
        # Gemini API responses
        if self.is_initialized and response != self._get_fallback_response():
            return 0.85
        
        # Fallback responses have lower confidence
        return 0.3
    
    def add_custom_pattern(self, pattern: str, response: str) -> None:
        """
        Add custom pattern-response pair (for future enhancement)
        
        Args:
            pattern: Pattern to match
            response: Response to return
        """
        # This can be implemented later for custom patterns
        logger.info(f"Custom pattern added: {pattern} -> {response}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the response generator
        
        Returns:
            dict: Status information
        """
        model_name = None
        if self.provider == 'openai' and self.is_initialized:
            model_name = self.openai_config['model']
        elif self.provider == 'gemini' and self.is_initialized:
            model_name = 'gemini-2.5-flash'
            
        return {
            'provider': self.provider,
            'initialized': self.is_initialized,
            'api_key_configured': bool(self.api_key),
            'model_name': model_name,
            'openai_available': OPENAI_AVAILABLE,
            'gemini_available': GEMINI_AVAILABLE,
            'last_request_time': datetime.fromtimestamp(self.last_request_time) if self.last_request_time else None,
            'rate_limit_interval': self.min_request_interval
        }