# Shruti Detection API Documentation

## Overview

The Carnatic Music Shruti Detection System provides real-time audio analysis and traditional Indian music note identification based on the 22-shruti system documented in Sangita Ratnakara.

## Core Detection Function

### `detectCarnaticShruti(frequency)`

Analyzes an input frequency and returns the closest shruti in the 22-shruti system.

#### Parameters

- `frequency` (float): Input frequency in Hz (typically 80-1200 Hz range)
- `baseFreq` (float): Tonic (Sa) frequency in Hz (default: 261.63 Hz)

#### Returns

```javascript
{
    note: "Shruti name",           // e.g., "Shadja", "Chatussruti Ri"
    western_note: "C4",            // Actual Western note (calculated)
    western_equiv: "Sa",           // Carnatic Solfege notation
    frequency: 261.63,             // Theoretical frequency for this shruti
    detected_frequency: 265.40,    // Actual detected frequency
    confidence: 0.85,              // Detection confidence (0.0-1.0)
    cent_value: 15,                // Deviation in cents from theoretical
    timestamp: 1694524800000,      // Detection timestamp
    raga_context: "Sankarabharanam" // Suggested raga context
}
```

#### Implementation

```javascript
function detectCarnaticShruti(frequency) {
    const baseFreq = parseFloat(document.getElementById('baseFreq').value);
    
    // Calculate cents from Sa
    const cents = 1200 * Math.log2(frequency / baseFreq);
    
    // Shruti mapping with cent values
    const shrutiCents = [
        {name: 'Shadja', cents: 0, western: 'Sa'},
        {name: 'Suddha Ri', cents: 90, western: 'R₁'},
        {name: 'Chatussruti Ri', cents: 204, western: 'R₂'},
        // ... complete 22-shruti mapping
    ];
    
    // Normalize cents to 0-1200 range
    const normalizedCents = ((cents % 1200) + 1200) % 1200;
    
    // Find closest shruti
    let closestShruti = null;
    let minDiff = Infinity;
    
    shrutiCents.forEach(shruti => {
        const diff = Math.min(
            Math.abs(normalizedCents - shruti.cents),
            Math.abs(normalizedCents - shruti.cents + 1200),
            Math.abs(normalizedCents - shruti.cents - 1200)
        );
        
        if (diff < minDiff) {
            minDiff = diff;
            closestShruti = shruti;
        }
    });
    
    // Calculate confidence and return result
    if (closestShruti && minDiff < 60) {
        const confidence = Math.max(0.3, 1 - (minDiff / 60));
        
        return {
            note: closestShruti.name,
            western_note: closestShruti.western_note, // Calculated note
            western_equiv: closestShruti.western,     // Solfege
            frequency: parseFloat((baseFreq * Math.pow(2, closestShruti.cents / 1200)).toFixed(2)),
            detected_frequency: parseFloat(frequency.toFixed(2)),
            confidence: confidence,
            cent_value: Math.round(normalizedCents - closestShruti.cents),
            timestamp: Date.now(),
            raga_context: determineRagaContext(closestShruti.name)
        };
    }
    
    return null; // No valid shruti detected
}
```

## Audio Processing Pipeline

### 1. Microphone Input

```javascript
// Request microphone access
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

// Create audio context
audioContext = new (window.AudioContext || window.webkitAudioContext)();
analyser = audioContext.createAnalyser();
microphone = audioContext.createMediaStreamSource(stream);

// Configure analyser for Carnatic precision
analyser.fftSize = 8192;  // Higher resolution
analyser.smoothingTimeConstant = 0.8;
```

### 2. Frequency Analysis

```javascript
function analyzeCarnaticAudio() {
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const freqArray = new Float32Array(bufferLength);
    
    analyser.getByteFrequencyData(dataArray);
    analyser.getFloatFrequencyData(freqArray);

    // Calculate volume (RMS)
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
        sum += dataArray[i] * dataArray[i];
    }
    const volume = Math.sqrt(sum / bufferLength);

    // Find dominant frequency in Carnatic range (80Hz - 1200Hz)
    let maxIndex = 0;
    let maxValue = -Infinity;
    
    const minBin = Math.floor(80 * bufferLength / (audioContext.sampleRate / 2));
    const maxBin = Math.floor(1200 * bufferLength / (audioContext.sampleRate / 2));
    
    for (let i = minBin; i < maxBin; i++) {
        if (freqArray[i] > maxValue) {
            maxValue = freqArray[i];
            maxIndex = i;
        }
    }

    const frequency = maxIndex * audioContext.sampleRate / (2 * bufferLength);
    
    // Detection threshold for Carnatic precision
    if (volume > 15 && frequency > 80 && frequency < 1200 && maxValue > -50) {
        const result = detectCarnaticShruti(frequency);
        if (result && result.confidence > 0.3) {
            updateShrutiDisplay(result);
            addToHistory(result);
        }
    }
}
```

## WebSocket Events

### Client → Server

#### `set_base_frequency`

Set the tonic (Sa) frequency for shruti calculations.

```javascript
socket.emit('set_base_frequency', {frequency: 261.63});
```

#### `start_detection`

Begin real-time shruti detection.

```javascript
socket.emit('start_detection', {base_frequency: 261.63});
```

#### `stop_detection`

Stop shruti detection.

```javascript
socket.emit('stop_detection');
```

### Server → Client

#### `detection_status`

Status updates for detection system.

```javascript
socket.on('detection_status', function(data) {
    // data.status: 'started', 'stopped', 'error', 'connected'
    // data.message: Status message
    // data.base_frequency: Current Sa frequency
});
```

#### `note_detected`

Real-time shruti detection results.

```javascript
socket.on('note_detected', function(data) {
    // Complete shruti detection object
    updateShrutiDisplay(data);
    addToHistory(data);
});
```

## Configuration Options

### Audio Settings

- **Sample Rate**: 44.1 kHz (default browser rate)
- **FFT Size**: 8192 (high resolution for microtonal precision)
- **Smoothing**: 0.8 (balanced responsiveness and stability)
- **Frequency Range**: 80-1200 Hz (Carnatic vocal/instrumental range)

### Detection Parameters

- **Volume Threshold**: 15 (minimum signal strength)
- **Confidence Threshold**: 0.3 (minimum detection confidence)
- **Tolerance**: ±60 cents (forgiving mode for learning)
- **Update Rate**: ~60 FPS (real-time responsiveness)

### Tonic (Sa) Configuration

- **Default**: 261.63 Hz (Middle C)
- **Range**: 100-500 Hz (practical vocal range)
- **Auto-Detection**: Available for automatic Sa identification

## Error Handling

### Microphone Access

```javascript
try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    // Success - proceed with detection
} catch (error) {
    if (error.name === 'NotAllowedError') {
        showMicrophoneError('Microphone access denied');
    } else if (error.name === 'NotFoundError') {
        showMicrophoneError('No microphone found');
    } else {
        showMicrophoneError('Microphone error: ' + error.message);
    }
}
```

### Detection Validation

```javascript
function validateDetection(result) {
    return result && 
           result.confidence > 0.3 && 
           result.frequency > 80 && 
           result.frequency < 1200 &&
           result.note && 
           result.western_note &&
           result.western_equiv;
}
```

## Performance Optimization

### Efficient Processing

- **Batch Updates**: Group UI updates to prevent flickering
- **Frequency Filtering**: Pre-filter audio to Carnatic range
- **Confidence Gating**: Only process high-confidence detections
- **History Limiting**: Maintain fixed-size detection history

### Memory Management

- **Audio Context Cleanup**: Properly close contexts on stop
- **Buffer Reuse**: Reuse typed arrays for analysis
- **Event Listener Cleanup**: Remove listeners on component unmount

## Cultural Considerations

### Traditional Accuracy

- Frequency ratios based on Sangita Ratnakara specifications
- Shruti names using traditional Sanskrit terminology
- Raga context determination following classical patterns
- Historical validation against medieval music theory

### Modern Adaptation

- Equal temperament compatibility for practical use
- Western notation equivalents for cross-cultural understanding
- Digital precision while maintaining traditional essence
- Educational value for contemporary learners
