// Generate mic stop sound effect programmatically
// This creates a pleasant "boop" sound to indicate recording stop

function createMicStopSound() {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const duration = 0.4; // 400ms
    const sampleRate = audioContext.sampleRate;
    const buffer = audioContext.createBuffer(1, duration * sampleRate, sampleRate);
    const data = buffer.getChannelData(0);
    
    // Create a pleasant descending tone (E to C)
    const freq1 = 659.25; // E5
    const freq2 = 523.25; // C5
    
    for (let i = 0; i < buffer.length; i++) {
        const t = i / sampleRate;
        const progress = t / duration;
        
        // Frequency sweep from E to C (descending)
        const freq = freq1 + (freq2 - freq1) * progress;
        
        // Envelope (fade in and out)
        let envelope = 1;
        if (t < 0.05) {
            envelope = t / 0.05; // Fade in
        } else if (t > duration - 0.15) {
            envelope = (duration - t) / 0.15; // Longer fade out
        }
        
        // Generate tone with envelope
        data[i] = Math.sin(2 * Math.PI * freq * t) * envelope * 0.25;
    }
    
    return buffer;
}

function playMicStopSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const buffer = createMicStopSound();
        const source = audioContext.createBufferSource();
        const gainNode = audioContext.createGain();
        
        source.buffer = buffer;
        source.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Set volume (slightly quieter than start sound)
        gainNode.gain.value = 0.3;
        
        source.start();
        
        console.log('🔊 Mic stop sound played');
    } catch (error) {
        console.warn('Could not play mic stop sound:', error);
    }
}

// Export for use in main app
window.playMicStopSound = playMicStopSound;