// Hindi AI Assistant - Minimal Interface JavaScript
class HindiAIAssistant {
    constructor() {
        console.log('Hindi AI Assistant - Minimal Interface initialized');
        
        // API Configuration
        this.API_BASE_URL = 'http://localhost:5000';
        
        // State management
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.videoStream = null;
        this.faceDetectionInterval = null;
        this.currentThinkingMessage = null;
        
        // Welcome message state
        this.hasPlayedWelcome = false;
        this.sessionId = this.generateSessionId();
        
        // Debug tracking
        this.processAudioCallCount = 0;
        this.isProcessingAudio = false;
        
        // Audio configuration
        this.audioConfig = {
            sampleRate: 16000,
            channels: 1,
            maxDuration: 60,
            minDuration: 1
        };
        
        // Initialize the application
        this.initializeElements();
        this.setupEventListeners();
        this.initializeAccessibility();
        
        // Initialize camera after a short delay to ensure DOM is ready
        setTimeout(() => {
            if (this.cameraFeed && this.faceDetectionStatus) {
                this.initializeCamera();
            } else {
                console.error('❌ Camera elements not found, retrying in 1 second...');
                setTimeout(() => {
                    this.initializeElements(); // Re-initialize elements
                    if (this.cameraFeed && this.faceDetectionStatus) {
                        this.initializeCamera();
                    } else {
                        console.error('❌ Camera elements still not found after retry');
                    }
                }, 1000);
            }
        }, 500);
        
        console.log('Initialization complete');
    }

    generateSessionId() {
        // Generate a unique session ID for this browser session
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    initializeElements() {
        // Chat interface elements
        this.chatContainer = document.getElementById('chatContainer');
        this.welcomeMessage = document.getElementById('welcomeMessage');
        
        // Audio upload elements
        this.audioFileInput = document.getElementById('audioFile');
        this.audioUploadButton = document.querySelector('.audio-upload-button');
        
        // Camera and microphone elements
        this.cameraFeed = document.getElementById('cameraFeed');
        this.faceDetectionStatus = document.getElementById('faceDetectionStatus');
        this.statusIcon = document.getElementById('statusIcon');
        this.statusText = document.getElementById('statusText');
        
        this.micButton = document.getElementById('micButton');
        this.audioWaves = document.getElementById('audioWaves');
        this.transcriptionDisplay = document.getElementById('transcriptionDisplay');
        this.transcriptionText = document.getElementById('transcriptionText');
        
        // Hidden elements
        this.videoElement = document.getElementById('videoElement');
        this.responseAudio = document.getElementById('responseAudio');
        
        // Overlay elements
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.loadingText = document.getElementById('loadingText');
        this.errorOverlay = document.getElementById('errorOverlay');
        this.errorText = document.getElementById('errorText');
        this.errorCloseBtn = document.getElementById('errorCloseBtn');
        
        // Accessibility elements
        this.highContrastToggle = document.getElementById('highContrastToggle');
        
        console.log('Elements initialized');
    }

    setupEventListeners() {
        // Audio file upload
        if (this.audioFileInput) {
            this.audioFileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileUpload(e.target.files[0]);
                }
            });
        }
        
        // Audio upload button click
        if (this.audioUploadButton) {
            this.audioUploadButton.addEventListener('click', () => {
                this.audioFileInput.click();
            });
            
            // Keyboard support
            this.audioUploadButton.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.audioFileInput.click();
                }
            });
        }
        
        // Microphone button
        if (this.micButton) {
            this.micButton.addEventListener('click', () => {
                this.toggleRecording();
            });
        }
        
        // Error close button
        if (this.errorCloseBtn) {
            this.errorCloseBtn.addEventListener('click', () => {
                this.hideError();
            });
        }
        
        // High contrast toggle
        if (this.highContrastToggle) {
            this.highContrastToggle.addEventListener('click', () => {
                this.toggleHighContrast();
            });
        }
        
        // Audio playback events
        if (this.responseAudio) {
            this.responseAudio.addEventListener('play', () => {
                this.showPlaybackWaves();
            });
            
            this.responseAudio.addEventListener('pause', () => {
                this.hideAllWaves();
            });
            
            this.responseAudio.addEventListener('ended', () => {
                this.hideAllWaves();
            });
        }
        
        console.log('Event listeners set up');
    }

    // ========================================
    // CHAT INTERFACE METHODS
    // ========================================

    addUserMessage(text) {
        console.log('👤👤👤 ADDING USER MESSAGE:', text);
        console.log('👤 Current chat container children:', this.chatContainer.children.length);
        
        const messageContainer = document.createElement('div');
        messageContainer.className = 'message-container';
        
        const message = document.createElement('div');
        message.className = 'message user-message';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '👤';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = text;
        
        message.appendChild(avatar);
        message.appendChild(content);
        messageContainer.appendChild(message);
        
        this.chatContainer.appendChild(messageContainer);
        this.scrollToBottom();
        
        console.log('👤 USER MESSAGE ADDED SUCCESSFULLY - Total messages now:', this.chatContainer.children.length);
    }

    addAgentMessage(text, isThinking = false, thinkingText = 'Thinking...') {
        console.log('🤖🤖🤖 ADDING AGENT MESSAGE:', isThinking ? `THINKING: ${thinkingText}` : `RESPONSE: ${text}`);
        console.log('🤖 Current chat container children:', this.chatContainer.children.length);
        
        const messageContainer = document.createElement('div');
        messageContainer.className = 'message-container';
        
        const message = document.createElement('div');
        message.className = isThinking ? 'message agent-message thinking-message' : 'message agent-message';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '🤖';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        if (isThinking) {
            content.innerHTML = `
                <span class="thinking-text">${thinkingText}</span>
                <div class="thinking-dots">
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                </div>
            `;
            this.currentThinkingMessage = messageContainer;
        } else {
            content.textContent = text;
        }
        
        message.appendChild(avatar);
        message.appendChild(content);
        messageContainer.appendChild(message);
        
        this.chatContainer.appendChild(messageContainer);
        this.scrollToBottom();
        
        console.log('🤖 AGENT MESSAGE ADDED SUCCESSFULLY - Total messages now:', this.chatContainer.children.length);
        return messageContainer;
    }

    updateThinkingMessage(text) {
        if (this.currentThinkingMessage) {
            const content = this.currentThinkingMessage.querySelector('.message-content');
            const message = this.currentThinkingMessage.querySelector('.message');
            
            content.textContent = text;
            message.classList.remove('thinking-message');
            
            this.currentThinkingMessage = null;
            this.scrollToBottom();
            
            console.log('Thinking message updated:', text);
        }
    }

    updateThinkingStatus(statusText) {
        if (this.currentThinkingMessage) {
            const thinkingTextElement = this.currentThinkingMessage.querySelector('.thinking-text');
            if (thinkingTextElement) {
                thinkingTextElement.textContent = statusText;
                console.log('🔄 Thinking status updated:', statusText);
            }
        }
    }

    scrollToBottom() {
        if (this.chatContainer) {
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }
    }

    clearTranscription() {
        if (this.transcriptionText) {
            this.transcriptionText.textContent = '';
            this.transcriptionText.classList.remove('active');
        }
    }

    updateTranscription(text) {
        if (this.transcriptionText) {
            this.transcriptionText.textContent = text;
            this.transcriptionText.classList.add('active');
        }
    }

    // ========================================
    // AUDIO HANDLING METHODS
    // ========================================

    async handleFileUpload(file) {
        try {
            console.log('File upload started:', file.name);
            
            // Validate file
            if (!this.validateAudioFile(file)) {
                return;
            }
            
            // Convert file to blob
            const audioBlob = new Blob([file], { type: file.type });
            
            // Process the audio (non-blocking)
            await this.processAudio(audioBlob);
            
        } catch (error) {
            console.error('File upload error:', error);
            this.showError('Error processing audio file. Please try again.');
        }
    }

    validateAudioFile(file) {
        const validTypes = ['audio/mp3', 'audio/wav', 'audio/m4a', 'audio/webm', 'audio/ogg', 'audio/mpeg'];
        const maxSize = 50 * 1024 * 1024; // 50MB
        
        if (!validTypes.includes(file.type)) {
            this.showError('Invalid file format. Please use MP3, WAV, M4A, WebM, or OGG files.');
            return false;
        }
        
        if (file.size > maxSize) {
            this.showError('File too large. Maximum size is 50MB.');
            return false;
        }
        
        if (file.size < 1000) {
            this.showError('File too small. Please select a valid audio file.');
            return false;
        }
        
        return true;
    }

    async toggleRecording() {
        if (this.isRecording) {
            await this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            console.log('Starting recording...');
            
            // Request microphone access with enhanced settings
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: this.audioConfig.sampleRate,
                    channelCount: this.audioConfig.channels,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Set up MediaRecorder with optimal settings
            const options = {
                mimeType: this.getSupportedMimeType(),
                audioBitsPerSecond: 128000
            };
            
            this.mediaRecorder = new MediaRecorder(stream, options);
            this.audioChunks = [];
            
            // Set up audio analysis for real-time feedback
            await this.setupAudioAnalysis(stream);
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                console.log('🎙️ MediaRecorder onstop event triggered');
                
                const audioBlob = new Blob(this.audioChunks, { type: options.mimeType });
                
                // Basic validation
                if (audioBlob.size < 1000) {
                    console.log('❌ Recording too short:', audioBlob.size, 'bytes');
                    this.showError('Recording too short or empty. Please try again.');
                    return;
                }
                
                console.log(`✅ Recording completed: ${audioBlob.size} bytes`);
                await this.processAudio(audioBlob);
            };
            
            this.mediaRecorder.onerror = (event) => {
                console.error('MediaRecorder error:', event.error);
                this.showError('Recording error occurred. Please try again.');
            };
            
            // Start recording
            this.mediaRecorder.start(1000); // Collect data every second
            this.isRecording = true;
            
            // Play start sound effect
            if (window.playMicStartSound) {
                window.playMicStartSound();
            }
            
            // Update UI
            this.updateRecordingUI(true);
            this.clearTranscription();
            this.updateTranscription('Listening...');
            
            console.log('Recording started with settings:', options);
            
        } catch (error) {
            console.error('Recording start error:', error);
            
            if (error.name === 'NotAllowedError') {
                this.showError('Microphone access denied. Please allow microphone access.');
            } else if (error.name === 'NotFoundError') {
                this.showError('No microphone found. Please connect a microphone.');
            } else {
                this.showError('Failed to start recording. Please try again.');
            }
        }
    }

    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/mp4',
            'audio/wav'
        ];
        
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        
        return 'audio/webm'; // Fallback
    }

    async setupAudioAnalysis(stream) {
        try {
            // Initialize Web Audio API context
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            // Resume audio context if suspended
            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }
            
            // Create audio analysis nodes
            this.microphone = this.audioContext.createMediaStreamSource(stream);
            this.analyser = this.audioContext.createAnalyser();
            
            this.analyser.fftSize = 256;
            this.analyser.smoothingTimeConstant = 0.8;
            
            this.microphone.connect(this.analyser);
            
            // Start audio level monitoring for visual feedback
            this.startAudioLevelMonitoring();
            
        } catch (error) {
            console.error('Error setting up audio analysis:', error);
        }
    }

    startAudioLevelMonitoring() {
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        const updateAudioLevel = () => {
            if (!this.isRecording) return;
            
            this.analyser.getByteFrequencyData(dataArray);
            
            // Calculate average audio level
            const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
            const normalizedLevel = average / 255;
            
            // Update audio wave animation intensity based on level
            this.updateAudioWaveIntensity(normalizedLevel);
            
            // Update transcription display based on audio activity
            if (normalizedLevel > 0.1) {
                this.updateTranscription('Speaking...');
            } else {
                this.updateTranscription('Listening...');
            }
            
            requestAnimationFrame(updateAudioLevel);
        };
        
        updateAudioLevel();
    }

    updateAudioWaveIntensity(level) {
        // Update audio wave animation based on microphone input level
        if (this.audioWaves && this.audioWaves.classList.contains('active')) {
            const waves = this.audioWaves.querySelectorAll('.wave');
            waves.forEach((wave, index) => {
                const delay = index * 0.1;
                const intensity = Math.max(0.3, level);
                wave.style.animationDelay = `${delay}s`;
                wave.style.opacity = intensity;
            });
        }
    }

    async stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            console.log('Stopping recording...');
            
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Play stop sound effect
            if (window.playMicStopSound) {
                window.playMicStopSound();
            }
            
            // Clean up audio analysis
            if (this.microphone) {
                this.microphone.disconnect();
                this.microphone = null;
            }
            
            if (this.analyser) {
                this.analyser.disconnect();
                this.analyser = null;
            }
            
            // Stop all audio tracks
            this.mediaRecorder.stream.getTracks().forEach(track => {
                track.stop();
                console.log('Audio track stopped:', track.kind);
            });
            
            // Update UI
            this.updateRecordingUI(false);
            // Clear transcription instead of showing "Processing..."
            this.clearTranscription();
            
            console.log('Recording stopped successfully');
        }
    }

    updateRecordingUI(recording) {
        if (this.micButton) {
            if (recording) {
                this.micButton.classList.add('recording');
                this.micButton.setAttribute('aria-pressed', 'true');
                this.showRecordingWaves();
            } else {
                this.micButton.classList.remove('recording');
                this.micButton.setAttribute('aria-pressed', 'false');
                this.hideAllWaves();
            }
        }
    }

    showAudioWaves() {
        if (this.audioWaves) {
            this.audioWaves.classList.add('active');
            
            // Add dynamic wave animation
            const waves = this.audioWaves.querySelectorAll('.wave');
            waves.forEach((wave, index) => {
                wave.style.animationDelay = `${index * 0.2}s`;
                wave.style.animationDuration = `${2 + index * 0.2}s`;
            });
        }
    }

    hideAudioWaves() {
        if (this.audioWaves) {
            this.audioWaves.classList.remove('active');
        }
    }

    // Enhanced audio wave control for different states
    showRecordingWaves() {
        this.showAudioWaves();
        if (this.audioWaves) {
            this.audioWaves.classList.add('recording');
        }
    }

    showPlaybackWaves() {
        this.showAudioWaves();
        if (this.audioWaves) {
            this.audioWaves.classList.add('playback');
        }
    }

    hideAllWaves() {
        if (this.audioWaves) {
            this.audioWaves.classList.remove('active', 'recording', 'playback');
        }
    }

    // ========================================
    // CONVERSATION PROCESSING
    // ========================================

    async processAudioCorrectOrder(audioBlob) {
        try {
            console.log('🎤 Processing audio...');
            
            // Clear transcription display
            this.clearTranscription();
            
            // Show processing animation immediately
            const processingMessage = this.addAgentMessage('', true, 'Processing your message...');
            
            // Step 1: Transcribe audio
            const transcription = await this.transcribeAudio(audioBlob);
            
            if (!transcription || transcription.trim().length === 0) {
                this.updateThinkingMessage('No speech detected. Please try again.');
                return;
            }
            
            // Step 2: Generate response
            const response = await this.generateResponse(transcription);
            
            if (!response || response.trim().length === 0) {
                this.updateThinkingMessage('Sorry, I could not generate a response. Please try again.');
                return;
            }
            
            // Step 3: Remove processing message and add both messages together
            processingMessage.remove();
            
            // Add user message first
            this.addUserMessage(transcription);
            
            // Add agent response
            this.addAgentMessage(response);
            
            // Play audio in background
            this.playResponseAudio(response);
            
            console.log('✅ Audio processing complete');
            
        } catch (error) {
            console.error('Audio processing error:', error);
            if (this.currentThinkingMessage) {
                this.updateThinkingMessage('Sorry, I encountered an error. Please try again.');
            } else {
                this.addAgentMessage('Sorry, I encountered an error. Please try again.');
            }
        }
    }

    // Legacy function - redirect to new implementation
    async processAudio(audioBlob) {
        return this.processAudioCorrectOrder(audioBlob);
    }

    async playResponseAudio(text) {
        try {
            const audioUrl = await this.textToSpeech(text);
            if (audioUrl) {
                this.responseAudio.src = audioUrl;
                await this.responseAudio.play();
            }
        } catch (ttsError) {
            console.warn('TTS failed, continuing with text-only:', ttsError);
        }
    }

    async playWelcomeMessage() {
        try {
            console.log('🎤 Playing welcome message...');
            
            // First, get the welcome message text
            const messageResponse = await fetch(`${this.API_BASE_URL}/api/welcome-message`);
            
            if (messageResponse.ok) {
                const messageData = await messageResponse.json();
                
                if (messageData.status === 'success') {
                    // Add welcome message to chat
                    this.addAgentMessage(messageData.message);
                    
                    // Then get and play the audio
                    const audioResponse = await fetch(`${this.API_BASE_URL}/api/welcome-speech`);
                    
                    if (audioResponse.ok) {
                        const audioBlob = await audioResponse.blob();
                        const audioUrl = URL.createObjectURL(audioBlob);
                        
                        // Play welcome audio
                        this.responseAudio.src = audioUrl;
                        await this.responseAudio.play();
                        
                        console.log('✅ Welcome message played successfully');
                    } else {
                        console.warn('Failed to get welcome audio, showing text only');
                    }
                } else {
                    console.error('Failed to get welcome message:', messageData.message);
                }
            } else {
                console.error('Failed to fetch welcome message');
            }
            
        } catch (error) {
            console.error('Error playing welcome message:', error);
            // Fallback: show a simple welcome message
            this.addAgentMessage('नमस्ते! मैं आपका हिंदी AI सहायक हूं। माइक बटन दबाकर मुझसे बात करें!');
        }
    }

    async transcribeAudio(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob);
            
            const response = await fetch(`${this.API_BASE_URL}/api/transcribe`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Transcription failed');
            }
            
            const data = await response.json();
            return data.transcription;
            
        } catch (error) {
            console.error('Transcription error:', error);
            throw error;
        }
    }

    async generateResponse(text) {
        try {
            const response = await fetch(`${this.API_BASE_URL}/api/generate-response`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });
            
            if (!response.ok) {
                throw new Error('Response generation failed');
            }
            
            const data = await response.json();
            return data.response;
            
        } catch (error) {
            console.error('Response generation error:', error);
            // Fallback response
            return this.getFallbackResponse(text);
        }
    }

    getFallbackResponse(inputText) {
        const input = inputText.toLowerCase().trim();
        
        if (input.includes('नमस्ते') || input.includes('hello')) {
            return 'नमस्ते! मैं आपकी सहायता करने की कोशिश कर रहा हूं।';
        }
        
        if (input.includes('धन्यवाद') || input.includes('thank')) {
            return 'आपका स्वागत है!';
        }
        
        if (input.includes('कैसे हैं') || input.includes('कैसे हो')) {
            return 'मैं ठीक हूं, धन्यवाद! आप कैसे हैं?';
        }
        
        return 'मुझे खेद है, मैं अभी आपकी पूरी सहायता नहीं कर पा रहा। कृपया बाद में पुनः प्रयास करें।';
    }

    async textToSpeech(text) {
        try {
            const response = await fetch(`${this.API_BASE_URL}/api/text-to-speech`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });
            
            if (!response.ok) {
                throw new Error('TTS failed');
            }
            
            const audioBlob = await response.blob();
            return URL.createObjectURL(audioBlob);
            
        } catch (error) {
            console.error('TTS error:', error);
            throw error;
        }
    }

    // ========================================
    // CAMERA AND FACE DETECTION
    // ========================================

    async initializeCamera() {
        try {
            console.log('🎥 Initializing camera...');
            console.log('Camera feed element:', this.cameraFeed);
            console.log('Face detection status element:', this.faceDetectionStatus);
            
            if (!this.cameraFeed) {
                console.error('❌ Camera feed element not found!');
                return;
            }
            
            this.updateFaceDetectionStatus('initializing', 'Camera initializing...');
            
            // Check if getUserMedia is available
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('getUserMedia not supported in this browser');
            }
            
            console.log('📱 getUserMedia is available');
            
            // Request camera access with specific constraints for better face detection
            const constraints = {
                video: {
                    width: { ideal: 640, max: 1280 },
                    height: { ideal: 480, max: 720 },
                    frameRate: { ideal: 15, max: 30 },
                    facingMode: 'user'
                },
                audio: false
            };
            
            console.log('🔧 Requesting camera with constraints:', constraints);
            
            this.videoStream = await navigator.mediaDevices.getUserMedia(constraints);
            console.log('✅ Camera stream obtained');
            
            // Set up camera feed
            this.cameraFeed.srcObject = this.videoStream;
            console.log('📺 Stream assigned to video element');
            
            // Wait for video to be ready with timeout
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Video metadata loading timeout'));
                }, 10000);
                
                this.cameraFeed.onloadedmetadata = () => {
                    clearTimeout(timeout);
                    console.log(`📐 Camera feed ready: ${this.cameraFeed.videoWidth}x${this.cameraFeed.videoHeight}`);
                    resolve();
                };
                
                this.cameraFeed.onerror = (error) => {
                    clearTimeout(timeout);
                    reject(new Error(`Video element error: ${error.message || 'Unknown video error'}`));
                };
            });
            
            // Ensure camera feed is playing
            try {
                await this.cameraFeed.play();
                console.log('▶️ Camera feed is now playing');
                console.log(`📊 Video state - Ready: ${this.cameraFeed.readyState}, Paused: ${this.cameraFeed.paused}`);
            } catch (playError) {
                console.warn('⚠️ Camera feed play failed:', playError);
                // Try to play again after a short delay
                setTimeout(async () => {
                    try {
                        await this.cameraFeed.play();
                        console.log('▶️ Camera feed playing after retry');
                    } catch (retryError) {
                        console.error('❌ Camera play retry failed:', retryError);
                    }
                }, 1000);
            }
            
            // Start real-time face detection
            this.startRealFaceDetection();
            
            console.log('🎉 Camera initialized successfully!');
            
        } catch (error) {
            console.error('Camera initialization error:', error);
            
            if (error.name === 'NotAllowedError') {
                this.updateFaceDetectionStatus('error', 'Camera access denied');
            } else if (error.name === 'NotFoundError') {
                this.updateFaceDetectionStatus('error', 'No camera found');
            } else {
                this.updateFaceDetectionStatus('error', 'Camera initialization failed');
            }
        }
    }

    startRealFaceDetection() {
        // Start real-time face detection using backend API
        this.faceDetectionInterval = setInterval(async () => {
            try {
                await this.performFaceDetection();
            } catch (error) {
                console.error('Face detection error:', error);
                this.updateFaceDetectionStatus('error', 'Detection error');
            }
        }, 2000); // Check every 2 seconds
        
        console.log('Real-time face detection started');
    }

    async performFaceDetection() {
        try {
            // Use the visible camera feed instead of hidden element for better reliability
            if (!this.cameraFeed || !this.videoStream) {
                console.log('Camera feed or stream not available');
                return;
            }
            
            // Ensure video is ready
            if (this.cameraFeed.readyState < 2) {
                console.log('Camera feed not ready yet, skipping detection');
                return;
            }
            
            // Create canvas for frame capture (same as standalone test)
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            
            // Use actual video dimensions from the visible camera feed
            const width = this.cameraFeed.videoWidth || 640;
            const height = this.cameraFeed.videoHeight || 480;
            
            canvas.width = width;
            canvas.height = height;
            
            // Draw current video frame to canvas with high quality (same as standalone)
            context.drawImage(this.cameraFeed, 0, 0, width, height);
            
            // Convert canvas to base64 with high quality (same as standalone)
            const imageData = canvas.toDataURL('image/jpeg', 0.95);
            
            console.log(`Capturing frame: ${width}x${height}, data length: ${imageData.length}`);
            
            // Send to backend for face detection with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 8000); // 8 second timeout (same as standalone)
            
            try {
                const response = await fetch(`${this.API_BASE_URL}/api/detect-face`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Session-ID': this.sessionId
                    },
                    body: JSON.stringify({ image: imageData }),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (response.ok) {
                    const result = await response.json();
                    
                    console.log('Face detection API response:', result);
                    
                    if (result.status === 'success') {
                        if (result.face_detected) {
                            const message = result.face_count === 1 
                                ? 'Face detected ✓' 
                                : `${result.face_count} faces detected ✓`;
                            this.updateFaceDetectionStatus('detected', message);
                            
                            // Check if this is the first time a face is detected
                            if (result.is_first_detection && !this.hasPlayedWelcome) {
                                console.log('🎉 First face detected! Playing welcome message...');
                                this.playWelcomeMessage();
                                this.hasPlayedWelcome = true;
                            }
                            
                            // Draw detection markers on camera feed
                            this.drawFaceDetectionMarkers(result.faces);
                            
                            // Log face details
                            if (result.faces && result.faces.length > 0) {
                                console.log('Face locations:', result.faces);
                            }
                        } else {
                            this.updateFaceDetectionStatus('not-detected', 'Move closer to camera');
                        }
                        
                        // Log detection performance
                        if (result.processing_time_ms) {
                            console.log(`Face detection: ${result.face_count} faces in ${result.processing_time_ms}ms`);
                        }
                    } else {
                        console.error('Face detection API error:', result.error || result.message);
                        this.updateFaceDetectionStatus('error', 'Detection failed');
                    }
                } else {
                    console.error('Face detection request failed:', response.status);
                    const errorText = await response.text();
                    console.error('Error response:', errorText);
                    this.updateFaceDetectionStatus('error', 'Service unavailable');
                }
                
            } catch (fetchError) {
                clearTimeout(timeoutId);
                
                if (fetchError.name === 'AbortError') {
                    console.warn('Face detection timeout');
                    this.updateFaceDetectionStatus('error', 'Detection timeout');
                } else {
                    console.error('Face detection fetch error:', fetchError);
                    this.updateFaceDetectionStatus('error', 'Connection error');
                }
            }
            
        } catch (error) {
            console.error('Error performing face detection:', error);
            this.updateFaceDetectionStatus('error', 'Detection error');
        }
    }

    drawFaceDetectionMarkers(faces) {
        // Remove existing markers
        this.clearFaceDetectionMarkers();
        
        if (!faces || faces.length === 0) return;
        
        // Get camera container for positioning
        const cameraContainer = this.cameraFeed.parentElement;
        if (!cameraContainer) return;
        
        // Get video display dimensions
        const videoRect = this.cameraFeed.getBoundingClientRect();
        const containerRect = cameraContainer.getBoundingClientRect();
        
        // Calculate scale factors
        const scaleX = videoRect.width / (this.cameraFeed.videoWidth || 640);
        const scaleY = videoRect.height / (this.cameraFeed.videoHeight || 480);
        
        faces.forEach((face, index) => {
            // Create face detection marker
            const marker = document.createElement('div');
            marker.className = 'face-detection-marker';
            marker.style.position = 'absolute';
            marker.style.border = '3px solid #00ff00';
            marker.style.borderRadius = '8px';
            marker.style.pointerEvents = 'none';
            marker.style.zIndex = '10';
            marker.style.boxShadow = '0 0 10px rgba(0, 255, 0, 0.5)';
            
            // Calculate position and size
            const left = face.x * scaleX;
            const top = face.y * scaleY;
            const width = face.width * scaleX;
            const height = face.height * scaleY;
            
            marker.style.left = `${left}px`;
            marker.style.top = `${top}px`;
            marker.style.width = `${width}px`;
            marker.style.height = `${height}px`;
            
            // Add face number label
            const label = document.createElement('div');
            label.textContent = `Face ${index + 1}`;
            label.style.position = 'absolute';
            label.style.top = '-25px';
            label.style.left = '0';
            label.style.background = 'rgba(0, 255, 0, 0.8)';
            label.style.color = 'black';
            label.style.padding = '2px 6px';
            label.style.borderRadius = '4px';
            label.style.fontSize = '12px';
            label.style.fontWeight = 'bold';
            
            marker.appendChild(label);
            cameraContainer.appendChild(marker);
            
            console.log(`Face ${index + 1} marker: ${width.toFixed(1)}x${height.toFixed(1)} at (${left.toFixed(1)}, ${top.toFixed(1)})`);
        });
    }
    
    clearFaceDetectionMarkers() {
        const cameraContainer = this.cameraFeed?.parentElement;
        if (!cameraContainer) return;
        
        const markers = cameraContainer.querySelectorAll('.face-detection-marker');
        markers.forEach(marker => marker.remove());
    }

    updateFaceDetectionStatus(status, message) {
        if (this.faceDetectionStatus) {
            this.faceDetectionStatus.className = `face-detection-status ${status}`;
        }
        
        if (this.statusText) {
            this.statusText.textContent = message;
        }
        
        // Update icon based on status
        if (this.statusIcon) {
            switch (status) {
                case 'detected':
                    this.statusIcon.textContent = '✅';
                    break;
                case 'not-detected':
                    this.statusIcon.textContent = '❌';
                    // Clear markers when no face detected
                    this.clearFaceDetectionMarkers();
                    break;
                case 'initializing':
                    this.statusIcon.textContent = '⏳';
                    break;
                case 'error':
                    this.statusIcon.textContent = '⚠️';
                    this.clearFaceDetectionMarkers();
                    break;
                default:
                    this.statusIcon.textContent = '👁️';
            }
        }
    }

    // ========================================
    // UI HELPER METHODS
    // ========================================

    showLoading(message) {
        if (this.loadingText) {
            this.loadingText.textContent = message;
        }
        
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'flex';
        }
    }

    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
    }

    showError(message) {
        if (this.errorText) {
            this.errorText.textContent = message;
        }
        
        if (this.errorOverlay) {
            this.errorOverlay.style.display = 'flex';
        }
        
        this.hideLoading();
    }

    hideError() {
        if (this.errorOverlay) {
            this.errorOverlay.style.display = 'none';
        }
    }

    // ========================================
    // ACCESSIBILITY METHODS
    // ========================================

    initializeAccessibility() {
        // Set up high contrast mode
        const savedHighContrast = localStorage.getItem('highContrastMode');
        if (savedHighContrast === 'true') {
            this.enableHighContrast();
        }
        
        console.log('Accessibility features initialized');
    }

    toggleHighContrast() {
        const isEnabled = document.body.classList.contains('high-contrast-mode');
        
        if (isEnabled) {
            this.disableHighContrast();
        } else {
            this.enableHighContrast();
        }
    }

    enableHighContrast() {
        document.body.classList.add('high-contrast-mode');
        localStorage.setItem('highContrastMode', 'true');
        
        if (this.highContrastToggle) {
            this.highContrastToggle.setAttribute('aria-pressed', 'true');
        }
    }

    disableHighContrast() {
        document.body.classList.remove('high-contrast-mode');
        localStorage.setItem('highContrastMode', 'false');
        
        if (this.highContrastToggle) {
            this.highContrastToggle.setAttribute('aria-pressed', 'false');
        }
    }

    // ========================================
    // CLEANUP METHODS
    // ========================================

    cleanup() {
        // Stop face detection
        if (this.faceDetectionInterval) {
            clearInterval(this.faceDetectionInterval);
        }
        
        // Stop video stream
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
        }
        
        // Stop recording if active
        if (this.isRecording) {
            this.stopRecording();
        }
        
        console.log('Cleanup complete');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM loaded, initializing Hindi AI Assistant...');
    
    // Add a small delay to ensure all elements are rendered
    setTimeout(() => {
        try {
            window.hindiAIAssistant = new HindiAIAssistant();
            console.log('✅ Hindi AI Assistant initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize Hindi AI Assistant:', error);
        }
    }, 100);
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.hindiAIAssistant) {
        window.hindiAIAssistant.cleanup();
    }
});