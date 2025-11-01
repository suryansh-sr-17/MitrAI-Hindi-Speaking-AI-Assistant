// Generate mic start sound effect programmatically
// This creates a pleasant "beep" sound to indicate recording start

function createMicStartSound() {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const duration = 0.3; // 300ms
    const sampleRate = audioContext.sampleRate;
    const buffer = audioContext.createBuffer(1, duration * sampleRate, sampleRate);
    const data = buffer.getChannelData(0);
    
    // Create a pleasant ascending tone (C to E)
    const freq1 = 523.25; // C5
    const freq2 = 659.25; // E5
    
    for (let i = 0; i < buffer.length; i++) {
        const t = i / sampleRate;
        const progress = t / duration;
        
        // Frequency sweep from C to E
        const freq = freq1 + (freq2 - freq1) * progress;
        
        // Envelope (fade in and out)
        let envelope = 1;
        if (t < 0.05) {
            envelope = t / 0.05; // Fade in
        } else if (t > duration - 0.1) {
            envelope = (duration - t) / 0.1; // Fade out
        }
        
        // Generate tone with envelope
        data[i] = Math.sin(2 * Math.PI * freq * t) * envelope * 0.3;
    }
    
    return buffer;
}

function playMicStartSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const buffer = createMicStartSound();
        const source = audioContext.createBufferSource();
        const gainNode = audioContext.createGain();
        
        source.buffer = buffer;
        source.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Set volume
        gainNode.gain.value = 0.4;
        
        source.start();
        
        console.log('🔊 Mic start sound played');
    } catch (error) {
        console.warn('Could not play mic start sound:', error);
    }
}

// Export for use in main app
window.playMicStartSound = playMicStartSound;