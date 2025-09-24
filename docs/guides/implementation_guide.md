# Implementation Guide - Carnatic Shruti Detection

## Quick Start

This guide walks through implementing and customizing the Carnatic music shruti detection system based on traditional 22-shruti theory.

## Prerequisites

### Required Knowledge
- Basic JavaScript for audio processing
- Understanding of Web Audio API
- Familiarity with WebSocket communication
- Basic music theory (helpful but not required)

### Browser Requirements
- Modern browser with Web Audio API support
- Microphone access permissions
- HTTPS for production deployment (microphone security requirement)

## Implementation Steps

### 1. Project Setup

#### Directory Structure
```
music/
├── docs/                  # Documentation (this directory)
│   ├── references/        # Sangita Ratnakara PDFs
│   ├── theory/           # Musical theory docs
│   ├── api/              # API documentation
│   └── guides/           # Implementation guides
├── templates/
│   └── carnatic.html     # Main shruti detection interface
├── app.py               # Flask backend with WebSocket
└── requirements-web.txt # Python dependencies
```

#### Backend Setup
```bash
# Install Python dependencies
pip install flask flask-socketio python-socketio python-engineio eventlet

# Start the Flask server
python app.py
```

#### Docker Deployment
```bash
# Build and run container
docker-compose build --no-cache
docker-compose up -d

# Access interface
open http://localhost:3005/carnatic
```

### 2. Core Audio Processing

#### Initialize Audio Context
```javascript
// Request microphone access
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

// Create audio processing chain
audioContext = new (window.AudioContext || window.webkitAudioContext)();
analyser = audioContext.createAnalyser();
microphone = audioContext.createMediaStreamSource(stream);

// Configure for Carnatic precision
analyser.fftSize = 8192;  // High resolution for microtones
analyser.smoothingTimeConstant = 0.8;  // Balanced responsiveness

// Connect audio nodes
microphone.connect(analyser);
```

#### Real-time Analysis Loop
```javascript
function analyzeCarnaticAudio() {
    if (!detectionActive) return;

    // Get frequency data
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const freqArray = new Float32Array(bufferLength);
    
    analyser.getByteFrequencyData(dataArray);
    analyser.getFloatFrequencyData(freqArray);

    // Calculate signal strength
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
        sum += dataArray[i] * dataArray[i];
    }
    const volume = Math.sqrt(sum / bufferLength);

    // Find dominant frequency in Carnatic range
    const minBin = Math.floor(80 * bufferLength / (audioContext.sampleRate / 2));
    const maxBin = Math.floor(1200 * bufferLength / (audioContext.sampleRate / 2));
    
    let maxIndex = 0;
    let maxValue = -Infinity;
    
    for (let i = minBin; i < maxBin; i++) {
        if (freqArray[i] > maxValue) {
            maxValue = freqArray[i];
            maxIndex = i;
        }
    }

    const frequency = maxIndex * audioContext.sampleRate / (2 * bufferLength);
    
    // Process detection if signal is strong enough
    if (volume > 15 && frequency > 80 && frequency < 1200 && maxValue > -50) {
        const result = detectCarnaticShruti(frequency);
        if (result && result.confidence > 0.3) {
            updateShrutiDisplay(result);
            addToHistory(result);
            highlightShruti(result.note);
        }
    }

    // Continue analysis loop
    animationId = requestAnimationFrame(analyzeCarnaticAudio);
}
```

### 3. Shruti Detection Algorithm

#### Complete 22-Shruti Mapping
```javascript
const shrutiCents = [
    {name: 'Shadja', cents: 0, western: 'Sa'},
    {name: 'Suddha Ri', cents: 90, western: 'R₁'},
    {name: 'Chatussruti Ri', cents: 204, western: 'R₂'},
    {name: 'Shatsruti Ri', cents: 294, western: 'R₃'},
    {name: 'Suddha Ga', cents: 316, western: 'G₁'},
    {name: 'Sadharana Ga', cents: 386, western: 'G₂'},
    {name: 'Antara Ga', cents: 408, western: 'G₃'},
    {name: 'Suddha Ma', cents: 498, western: 'M₁'},
    {name: 'Prati Ma', cents: 612, western: 'M₂'},
    {name: 'Panchama', cents: 702, western: 'Pa'},
    {name: 'Suddha Dha', cents: 792, western: 'D₁'},
    {name: 'Chatussruti Dha', cents: 906, western: 'D₂'},
    {name: 'Shatsruti Dha', cents: 996, western: 'D₃'},
    {name: 'Suddha Ni', cents: 1018, western: 'N₁'},
    {name: 'Kaisika Ni', cents: 1088, western: 'N₂'},
    {name: 'Kakali Ni', cents: 1110, western: 'N₃'}
];
```

#### Detection Function
```javascript
function detectCarnaticShruti(frequency) {
    const baseFreq = parseFloat(document.getElementById('baseFreq').value);
    
    // Calculate cents from Sa (tonic)
    const cents = 1200 * Math.log2(frequency / baseFreq);
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
    
    // Return result if within tolerance
    if (closestShruti && minDiff < 60) {
        const confidence = Math.max(0.3, 1 - (minDiff / 60));
        
        return {
            note: closestShruti.name,
            western_equiv: closestShruti.western,
            frequency: parseFloat((baseFreq * Math.pow(2, closestShruti.cents / 1200)).toFixed(2)),
            detected_frequency: parseFloat(frequency.toFixed(2)),
            confidence: confidence,
            cent_value: Math.round(normalizedCents - closestShruti.cents),
            timestamp: Date.now(),
            raga_context: determineRagaContext(closestShruti.name)
        };
    }
    
    return null;
}
```

### 4. User Interface Integration

#### Horizontal History Display
```css
.history-container {
    display: flex;
    overflow-x: auto;
    gap: 15px;
    padding: 10px 0;
    scroll-behavior: smooth;
}

.history-item {
    background: rgba(45, 52, 54, 0.7);
    padding: 15px;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 120px;
    flex-shrink: 0;
    transition: all 0.3s ease;
}

.history-item:hover {
    transform: translateY(-3px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}
```

#### Real-time Updates
```javascript
function updateShrutiDisplay(data) {
    // Update main display
    document.getElementById('currentShruti').textContent = data.note;
    document.getElementById('shrutiWestern').textContent = `${data.western_equiv} (${data.note})`;
    document.getElementById('frequency').textContent = data.frequency + ' Hz';
    document.getElementById('detectedFreq').textContent = data.detected_frequency + ' Hz';
    document.getElementById('confidence').textContent = Math.round(data.confidence * 100) + '%';
    document.getElementById('centValue').textContent = data.cent_value;

    // Update raga context
    if (data.raga_context) {
        const raga = ragaInfo[data.raga_context];
        if (raga) {
            document.getElementById('ragaName').textContent = `${raga.english} (${data.raga_context})`;
            document.getElementById('ragaAroha').textContent = `Aroha: ${raga.aroha}`;
            document.getElementById('ragaAvaroha').textContent = `Avaroha: ${raga.avaroha}`;
        }
    }
}
```

### 5. Advanced Features

#### Auto-Detection of Sa (Tonic)
```javascript
async function autoDetectSa() {
    // Collect 30 stable frequency samples
    const samples = [];
    
    // Temporary audio analysis for Sa detection
    const tempContext = new AudioContext();
    const tempAnalyser = tempContext.createAnalyser();
    const tempMic = tempContext.createMediaStreamSource(stream);
    
    tempAnalyser.fftSize = 8192;
    tempMic.connect(tempAnalyser);
    
    // Collect samples over 5 seconds
    for (let i = 0; i < 30; i++) {
        const frequency = await getSampleFrequency(tempAnalyser);
        if (frequency > 100 && frequency < 500) {
            samples.push(frequency);
        }
        await sleep(100);
    }
    
    // Calculate median for stability
    samples.sort((a, b) => a - b);
    const detectedSa = samples[Math.floor(samples.length / 2)];
    
    // Update base frequency
    document.getElementById('baseFreq').value = detectedSa.toFixed(2);
    socket.emit('set_base_frequency', {frequency: detectedSa});
    
    tempContext.close();
}
```

#### Raga Context Analysis
```javascript
function determineRagaContext(shrutiName) {
    const recentNotes = detectionHistory.slice(0, 5).map(d => d.note);
    
    // Pattern matching for common ragas
    if (recentNotes.includes('Chatussruti Ri') && recentNotes.includes('Antara Ga')) {
        return 'Sankarabharanam';  // Major scale equivalent
    } else if (recentNotes.includes('Chatussruti Ri') && recentNotes.includes('Sadharana Ga')) {
        return 'Kharaharapriya';  // Natural minor
    } else if (recentNotes.includes('Suddha Ri') && recentNotes.includes('Antara Ga')) {
        return 'Mayamalavagowla';  // Morning raga
    } else if (recentNotes.includes('Prati Ma')) {
        return 'Kalyani';  // Lydian mode
    } else if (!recentNotes.includes('Suddha Ma') && !recentNotes.includes('Prati Ma')) {
        return 'Mohanam';  // Pentatonic
    }
    
    return 'Sankarabharanam';  // Default
}
```

## Customization Options

### Detection Sensitivity
```javascript
// Adjust tolerance for different skill levels
const TOLERANCE_SETTINGS = {
    beginner: 60,    // ±60 cents (forgiving)
    intermediate: 40, // ±40 cents (moderate)
    advanced: 20     // ±20 cents (precise)
};

// Adjust confidence threshold
const confidence = Math.max(0.3, 1 - (deviation / TOLERANCE_SETTINGS.intermediate));
```

### Visual Themes
```css
/* Dark theme for evening practice */
:root {
    --primary-bg: #1a1a1a;
    --secondary-bg: #2d3436;
    --accent-color: #74b9ff;
    --text-color: #e1e5e9;
}

/* Light theme for daytime practice */
:root {
    --primary-bg: #f5f6fa;
    --secondary-bg: #ffffff;
    --accent-color: #2d3436;
    --text-color: #2d3436;
}
```

## Troubleshooting

### Common Issues

#### Microphone Access Denied
```javascript
// Check permissions and provide guidance
if (error.name === 'NotAllowedError') {
    showMicrophoneError('Please allow microphone access in browser settings');
}
```

#### Poor Detection Accuracy
- **Check Sa tuning**: Ensure base frequency matches your practice
- **Reduce background noise**: Use in quiet environment
- **Adjust tolerance**: Increase for learning, decrease for performance
- **Verify microphone quality**: Use external microphone for better results

#### Performance Issues
- **Lower FFT size**: Reduce from 8192 to 4096 for faster processing
- **Increase confidence threshold**: Filter out weak detections
- **Limit history size**: Reduce from 15 to 10 items

## Integration with External Systems

### MIDI Output
```javascript
// Send detected shrutis as MIDI notes
function sendMIDI(shruti) {
    if (navigator.requestMIDIAccess) {
        navigator.requestMIDIAccess().then(access => {
            const outputs = access.outputs.values();
            const output = outputs.next().value;
            
            if (output) {
                const midiNote = shrutiToMIDI(shruti.name);
                output.send([0x90, midiNote, 127]); // Note on
                setTimeout(() => {
                    output.send([0x80, midiNote, 0]); // Note off
                }, 500);
            }
        });
    }
}
```

### Data Export
```javascript
// Export session data as JSON
function exportSession() {
    const sessionData = {
        timestamp: Date.now(),
        base_frequency: document.getElementById('baseFreq').value,
        detections: detectionHistory,
        analytics: {
            total_detections: detectionHistory.length,
            unique_shrutis: Array.from(uniqueShrutis),
            avg_confidence: avgConfidence,
            session_duration: sessionDuration
        }
    };
    
    const blob = new Blob([JSON.stringify(sessionData, null, 2)], 
                         {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `carnatic_session_${new Date().toISOString()}.json`;
    a.click();
}
```

## Best Practices

### Performance Optimization
- Use `requestAnimationFrame` for smooth animations
- Batch DOM updates to prevent layout thrashing
- Properly cleanup audio contexts and event listeners
- Implement efficient frequency analysis algorithms

### Cultural Sensitivity
- Use traditional Sanskrit terminology correctly
- Respect historical accuracy in frequency ratios
- Provide educational context for traditional concepts
- Maintain connection to classical music traditions

### User Experience
- Provide clear visual feedback for all interactions
- Include helpful error messages and guidance
- Offer multiple difficulty levels for different skill levels
- Ensure accessibility for users with disabilities

This implementation guide provides a complete foundation for building and customizing Carnatic music detection systems based on the traditional 22-shruti system documented in Sangita Ratnakara.