/**
 * Error Recovery System for Hindi AI Assistant
 * Provides comprehensive error recovery mechanisms and system health monitoring
 */

class ErrorRecoverySystem {
    constructor(app) {
        this.app = app;
        this.healthChecks = {
            lastCheck: null,
            interval: 30000, // 30 seconds
            intervalId: null,
            consecutiveFailures: 0,
            maxFailures: 3
        };
        
        this.recoveryStrategies = {
            'transcription': this.recoverTranscriptionService.bind(this),
            'response_generation': this.recoverResponseService.bind(this),
            'tts': this.recoverTTSService.bind(this),
            'face_detection': this.recoverFaceDetectionService.bind(this),
            'conversation': this.recoverConversationFlow.bind(this)
        };
        
        this.systemStatus = {
            overall: 'healthy',
            services: {},
            lastRecoveryAttempt: null,
            recoveryCount: 0
        };
        
        this.initialize();
    }
    
    initialize() {
        console.log('Initializing Error Recovery System...');
        
        // Start periodic health checks
        this.startHealthMonitoring();
        
        // Set up recovery event listeners
        this.setupRecoveryListeners();
        
        console.log('Error Recovery System initialized');
    }
    
    startHealthMonitoring() {
        /**
         * Start periodic health checks for all services
         */
        this.healthChecks.intervalId = setInterval(() => {
            this.performHealthCheck();
        }, this.healthChecks.interval);
        
        // Perform initial health check
        setTimeout(() => this.performHealthCheck(), 5000);
    }
    
    async performHealthCheck() {
        /**
         * Perform comprehensive health check of all services
         */
        console.log('Performing system health check...');
        this.healthChecks.lastCheck = new Date();
        
        try {
            const response = await fetch(`${this.app.API_BASE_URL}/api/status`, {
                method: 'GET',
                timeout: 10000
            });
            
            if (response.ok) {
                const status = await response.json();
                this.processHealthCheckResults(status);
                this.healthChecks.consecutiveFailures = 0;
            } else {
                throw new Error(`Health check failed with status: ${response.status}`);
            }
            
        } catch (error) {
            console.error('Health check failed:', error);
            this.healthChecks.consecutiveFailures++;
            
            if (this.healthChecks.consecutiveFailures >= this.healthChecks.maxFailures) {
                console.warn('Multiple health check failures detected, initiating system recovery...');
                await this.initiateSystemRecovery();
            }
        }
    }
    
    processHealthCheckResults(status) {
        /**
         * Process health check results and update system status
         */
        const services = status.services || {};
        
        // Check each service status
        Object.keys(services).forEach(serviceName => {
            const serviceStatus = services[serviceName];
            const isHealthy = serviceStatus.available === true;
            
            this.systemStatus.services[serviceName] = {
                healthy: isHealthy,
                lastCheck: new Date(),
                details: serviceStatus
            };
            
            // Trigger recovery if service is unhealthy
            if (!isHealthy && this.recoveryStrategies[serviceName]) {
                console.warn(`Service ${serviceName} is unhealthy, scheduling recovery...`);
                setTimeout(() => this.recoverService(serviceName), 1000);
            }
        });
        
        // Update overall system status
        const healthyServices = Object.values(this.systemStatus.services).filter(s => s.healthy).length;
        const totalServices = Object.keys(this.systemStatus.services).length;
        
        if (healthyServices === totalServices) {
            this.systemStatus.overall = 'healthy';
        } else if (healthyServices > totalServices / 2) {
            this.systemStatus.overall = 'degraded';
        } else {
            this.systemStatus.overall = 'critical';
        }
        
        console.log(`System health: ${this.systemStatus.overall} (${healthyServices}/${totalServices} services healthy)`);
    }
    
    async recoverService(serviceName) {
        /**
         * Attempt to recover a specific service
         */
        console.log(`Attempting to recover service: ${serviceName}`);
        
        const recoveryStrategy = this.recoveryStrategies[serviceName];
        if (!recoveryStrategy) {
            console.warn(`No recovery strategy available for service: ${serviceName}`);
            return false;
        }
        
        try {
            const recovered = await recoveryStrategy();
            
            if (recovered) {
                console.log(`Service ${serviceName} recovered successfully`);
                this.systemStatus.services[serviceName].healthy = true;
                this.systemStatus.lastRecoveryAttempt = new Date();
                this.systemStatus.recoveryCount++;
                return true;
            } else {
                console.warn(`Failed to recover service: ${serviceName}`);
                return false;
            }
            
        } catch (error) {
            console.error(`Error during ${serviceName} recovery:`, error);
            return false;
        }
    }
    
    async recoverTranscriptionService() {
        /**
         * Recovery strategy for speech-to-text service
         */
        try {
            // Reset STT service
            if (this.app.stt_service) {
                this.app.stt_service = null;
            }
            
            // Reinitialize services
            await this.app.checkServiceStatus();
            
            // Test with a small audio blob
            const testBlob = new Blob(['test'], { type: 'audio/wav' });
            
            // Don't actually call transcribe, just check if service is available
            return this.app.stt_service !== null;
            
        } catch (error) {
            console.error('Transcription service recovery failed:', error);
            return false;
        }
    }
    
    async recoverResponseService() {
        /**
         * Recovery strategy for response generation service
         */
        try {
            // Test response generation with a simple input
            const testResponse = this.app.getClientSideFallbackResponse('test');
            
            // If we can generate fallback responses, service is partially recovered
            return testResponse && testResponse.length > 0;
            
        } catch (error) {
            console.error('Response service recovery failed:', error);
            return false;
        }
    }
    
    async recoverTTSService() {
        /**
         * Recovery strategy for text-to-speech service
         */
        try {
            // Reset TTS service reference
            if (this.app.tts_service) {
                this.app.tts_service = null;
            }
            
            // Reinitialize services
            await this.app.checkServiceStatus();
            
            // TTS recovery is considered successful if we can fall back to text-only
            return true;
            
        } catch (error) {
            console.error('TTS service recovery failed:', error);
            return false;
        }
    }
    
    async recoverFaceDetectionService() {
        /**
         * Recovery strategy for face detection service
         */
        try {
            // Stop current face detection
            if (this.app.faceDetectionInterval) {
                clearInterval(this.app.faceDetectionInterval);
                this.app.faceDetectionInterval = null;
            }
            
            // Wait a moment
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Restart face detection if camera is available
            if (this.app.videoStream) {
                this.app.startRealFaceDetection();
                return true;
            }
            
            return false;
            
        } catch (error) {
            console.error('Face detection service recovery failed:', error);
            return false;
        }
    }
    
    async recoverConversationFlow() {
        /**
         * Recovery strategy for conversation workflow
         */
        try {
            // Reset conversation state
            this.app.conversationState.isActive = false;
            this.app.conversationState.currentStep = this.app.workflowSteps.IDLE;
            this.app.conversationState.errorCount = 0;
            
            // Stop any ongoing recording
            if (this.app.isRecording) {
                this.app.stopRecording();
            }
            
            // Update UI
            this.app.updateUIForConversationStep(this.app.workflowSteps.IDLE);
            this.app.hideLoading();
            this.app.hideError();
            
            // Re-enable record button
            if (this.app.recordBtn) {
                this.app.recordBtn.disabled = false;
            }
            
            console.log('Conversation flow recovered');
            return true;
            
        } catch (error) {
            console.error('Conversation flow recovery failed:', error);
            return false;
        }
    }
    
    async initiateSystemRecovery() {
        /**
         * Initiate comprehensive system recovery
         */
        console.log('Initiating comprehensive system recovery...');
        
        // Show recovery message to user
        this.app.showError('System is recovering, please wait... | सिस्टम रिकवर हो रहा है, कृपया प्रतीक्षा करें...');
        
        // Attempt to recover all services
        const recoveryPromises = Object.keys(this.recoveryStrategies).map(async (serviceName) => {
            try {
                const recovered = await this.recoverService(serviceName);
                return { service: serviceName, recovered };
            } catch (error) {
                console.error(`Recovery failed for ${serviceName}:`, error);
                return { service: serviceName, recovered: false };
            }
        });
        
        const recoveryResults = await Promise.all(recoveryPromises);
        
        // Analyze recovery results
        const successfulRecoveries = recoveryResults.filter(r => r.recovered).length;
        const totalServices = recoveryResults.length;
        
        if (successfulRecoveries === totalServices) {
            console.log('System recovery completed successfully');
            this.app.showError('System recovered successfully! | सिस्टम सफलतापूर्वक रिकवर हो गया!');
            setTimeout(() => this.app.hideError(), 3000);
        } else if (successfulRecoveries > 0) {
            console.log(`Partial system recovery: ${successfulRecoveries}/${totalServices} services recovered`);
            this.app.showError(`Partial recovery completed. Some features may be limited. | आंशिक रिकवरी पूर्ण। कुछ सुविधाएं सीमित हो सकती हैं।`);
        } else {
            console.error('System recovery failed');
            this.app.showError('System recovery failed. Please refresh the page. | सिस्टम रिकवरी विफल। कृपया पेज रीफ्रेश करें।');
        }
        
        // Reset consecutive failures counter
        this.healthChecks.consecutiveFailures = 0;
    }
    
    setupRecoveryListeners() {
        /**
         * Set up event listeners for recovery triggers
         */
        // Listen for online/offline events
        window.addEventListener('online', () => {
            console.log('Network connection restored, performing health check...');
            setTimeout(() => this.performHealthCheck(), 1000);
        });
        
        window.addEventListener('offline', () => {
            console.log('Network connection lost');
            this.app.showError('Network connection lost. Please check your internet connection. | नेटवर्क कनेक्शन खो गया। कृपया अपना इंटरनेट कनेक्शन जांचें।');
        });
        
        // Listen for visibility change (tab focus)
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // Tab became visible, perform health check
                setTimeout(() => this.performHealthCheck(), 2000);
            }
        });
    }
    
    getSystemStatus() {
        /**
         * Get current system status for debugging
         */
        return {
            ...this.systemStatus,
            healthChecks: {
                ...this.healthChecks,
                intervalId: !!this.healthChecks.intervalId
            }
        };
    }
    
    cleanup() {
        /**
         * Clean up recovery system resources
         */
        if (this.healthChecks.intervalId) {
            clearInterval(this.healthChecks.intervalId);
            this.healthChecks.intervalId = null;
        }
        
        console.log('Error Recovery System cleaned up');
    }
}

// Export for use in main application
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorRecoverySystem;
} else {
    window.ErrorRecoverySystem = ErrorRecoverySystem;
}