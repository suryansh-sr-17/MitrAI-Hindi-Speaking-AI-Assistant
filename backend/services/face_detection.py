"""
Face Detection Service for Hindi AI Assistant
Uses OpenCV for real-time face detection from webcam frames
"""

import cv2
import numpy as np
import logging
import base64
import io
from PIL import Image
import time
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class FaceDetectionService:
    """
    Face detection service using OpenCV Haar Cascades
    Provides real-time face detection capabilities for webcam frames
    """
    
    def __init__(self):
        """Initialize the face detection service"""
        self.face_cascade = None
        self.is_initialized = False
        self.detection_confidence = 0.5
        self.min_face_size = (20, 20)  # Smaller minimum size for better detection
        self.scale_factor = 1.05  # Smaller scale factor for more thorough detection
        self.min_neighbors = 3  # Fewer neighbors required for detection
        
        # Performance tracking
        self.detection_count = 0
        self.total_processing_time = 0.0
        
        self.initialize()
    
    def initialize(self) -> bool:
        """
        Initialize OpenCV face detection cascade
        Returns True if successful, False otherwise
        """
        try:
            # Load the pre-trained Haar cascade for face detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                logger.error("Failed to load Haar cascade classifier")
                return False
            
            self.is_initialized = True
            logger.info("Face detection service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize face detection service: {str(e)}")
            self.is_initialized = False
            return False
    
    def detect_faces_from_base64(self, image_data: str) -> Dict[str, Any]:
        """
        Detect faces in a base64 encoded image
        
        Args:
            image_data: Base64 encoded image string
            
        Returns:
            Dictionary with detection results
        """
        try:
            if not self.is_initialized:
                return {
                    'success': False,
                    'error': 'Face detection service not initialized',
                    'face_detected': False
                }
            
            start_time = time.time()
            
            # Decode base64 image
            try:
                # Remove data URL prefix if present
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                
                # Decode base64
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
                
                # Convert PIL image to OpenCV format
                opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
            except Exception as e:
                logger.error(f"Failed to decode image: {str(e)}")
                return {
                    'success': False,
                    'error': 'Invalid image data',
                    'face_detected': False
                }
            
            # Perform face detection
            detection_result = self._detect_faces_in_frame(opencv_image)
            
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            self.detection_count += 1
            
            # Add performance metrics
            detection_result['processing_time'] = round(processing_time * 1000, 2)  # Convert to ms
            detection_result['average_processing_time'] = round(
                (self.total_processing_time / self.detection_count) * 1000, 2
            )
            
            logger.info(f"Face detection completed in {detection_result['processing_time']}ms: "
                       f"{detection_result['face_count']} faces detected")
            
            return detection_result
            
        except Exception as e:
            logger.error(f"Error in detect_faces_from_base64: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'face_detected': False
            }
    
    def _detect_faces_in_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Internal method to detect faces in an OpenCV frame
        
        Args:
            frame: OpenCV image frame (BGR format)
            
        Returns:
            Dictionary with detection results
        """
        try:
            # Log frame info for debugging
            logger.info(f"Processing frame: {frame.shape} (H x W x C)")
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply histogram equalization to improve contrast
            gray = cv2.equalizeHist(gray)
            
            # Detect faces using Haar cascade with multiple parameter sets
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=self.scale_factor,
                minNeighbors=self.min_neighbors,
                minSize=self.min_face_size,
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # If no faces found with strict parameters, try more lenient ones
            if len(faces) == 0:
                logger.info("No faces found with default parameters, trying more lenient detection...")
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.03,
                    minNeighbors=2,
                    minSize=(15, 15),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
            
            logger.info(f"Face detection result: {len(faces)} faces found")
            
            face_count = len(faces)
            face_detected = face_count > 0
            
            # Extract face information
            face_info = []
            for (x, y, w, h) in faces:
                face_info.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'confidence': self.detection_confidence  # Haar cascades don't provide confidence
                })
            
            # Determine status message
            if face_count == 0:
                status_message = "No user detected"
                status_message_hi = "कोई उपयोगकर्ता नहीं मिला"
            elif face_count == 1:
                status_message = "User detected ✓"
                status_message_hi = "उपयोगकर्ता मिला ✓"
            else:
                status_message = f"{face_count} users detected ✓"
                status_message_hi = f"{face_count} उपयोगकर्ता मिले ✓"
            
            return {
                'success': True,
                'face_detected': face_detected,
                'face_count': face_count,
                'faces': face_info,
                'message': status_message,
                'message_hi': status_message_hi,
                'frame_size': {
                    'width': frame.shape[1],
                    'height': frame.shape[0]
                }
            }
            
        except Exception as e:
            logger.error(f"Error detecting faces in frame: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'face_detected': False,
                'face_count': 0
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get service status and statistics
        
        Returns:
            Dictionary with service status information
        """
        avg_processing_time = 0.0
        if self.detection_count > 0:
            avg_processing_time = round((self.total_processing_time / self.detection_count) * 1000, 2)
        
        return {
            'initialized': self.is_initialized,
            'detection_count': self.detection_count,
            'average_processing_time_ms': avg_processing_time,
            'total_processing_time_s': round(self.total_processing_time, 2),
            'settings': {
                'scale_factor': self.scale_factor,
                'min_neighbors': self.min_neighbors,
                'min_face_size': self.min_face_size,
                'detection_confidence': self.detection_confidence
            }
        }
    
    def update_settings(self, **kwargs) -> bool:
        """
        Update detection settings
        
        Args:
            **kwargs: Settings to update (scale_factor, min_neighbors, etc.)
            
        Returns:
            True if settings updated successfully
        """
        try:
            if 'scale_factor' in kwargs:
                self.scale_factor = max(1.01, min(2.0, float(kwargs['scale_factor'])))
            
            if 'min_neighbors' in kwargs:
                self.min_neighbors = max(1, min(20, int(kwargs['min_neighbors'])))
            
            if 'detection_confidence' in kwargs:
                self.detection_confidence = max(0.1, min(1.0, float(kwargs['detection_confidence'])))
            
            if 'min_face_size' in kwargs:
                size = kwargs['min_face_size']
                if isinstance(size, (list, tuple)) and len(size) == 2:
                    self.min_face_size = (max(10, int(size[0])), max(10, int(size[1])))
            
            logger.info(f"Face detection settings updated: scale_factor={self.scale_factor}, "
                       f"min_neighbors={self.min_neighbors}, min_face_size={self.min_face_size}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update face detection settings: {str(e)}")
            return False
    
    def reset_statistics(self):
        """Reset performance statistics"""
        self.detection_count = 0
        self.total_processing_time = 0.0
        logger.info("Face detection statistics reset")

# Global service instance
_face_detection_service = None

def get_face_detection_service() -> FaceDetectionService:
    """
    Get or create the global face detection service instance
    
    Returns:
        FaceDetectionService instance
    """
    global _face_detection_service
    
    if _face_detection_service is None:
        _face_detection_service = FaceDetectionService()
    
    return _face_detection_service

def test_face_detection_service():
    """
    Test function for the face detection service
    Creates a simple test image and runs detection
    """
    try:
        service = get_face_detection_service()
        
        if not service.is_initialized:
            print("❌ Face detection service failed to initialize")
            return False
        
        # Create a simple test image (white background)
        test_image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        # Add some simple shapes to simulate a face-like pattern
        cv2.rectangle(test_image, (250, 150), (390, 330), (200, 200, 200), -1)  # Face outline
        cv2.circle(test_image, (290, 200), 15, (0, 0, 0), -1)  # Left eye
        cv2.circle(test_image, (350, 200), 15, (0, 0, 0), -1)  # Right eye
        cv2.rectangle(test_image, (310, 250), (330, 280), (0, 0, 0), -1)  # Nose
        cv2.ellipse(test_image, (320, 300), (30, 15), 0, 0, 180, (0, 0, 0), 2)  # Mouth
        
        # Test detection
        result = service._detect_faces_in_frame(test_image)
        
        print(f"✅ Face detection test completed:")
        print(f"   - Success: {result['success']}")
        print(f"   - Faces detected: {result.get('face_count', 0)}")
        print(f"   - Message: {result.get('message', 'N/A')}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Face detection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Run test when script is executed directly
    print("Testing Face Detection Service...")
    test_face_detection_service()