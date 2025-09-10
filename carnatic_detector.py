"""
Enhanced Carnatic Music Note Detection System
Supports 22 Shruti system and traditional South Indian Classical Music
"""

import numpy as np
import sounddevice as sd
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import threading
import time
import json

@dataclass
class Shruti:
    """Represents a Carnatic shruti with its properties"""
    name: str
    western_equiv: str
    cent_value: int
    frequency_ratio: float
    raga_usage: List[str]

@dataclass 
class DetectionResult:
    """Result of note detection"""
    shruti: Shruti
    frequency: float
    magnitude: float
    confidence: float
    timestamp: float

class CarnaticNoteDetector:
    """Advanced note detection system for Carnatic music"""
    
    def __init__(self, base_frequency: float = 261.63, sample_rate: int = 44100):
        """
        Initialize Carnatic detector
        Args:
            base_frequency: Sa (Shadja) frequency in Hz, typically C4 (261.63 Hz)
            sample_rate: Audio sampling rate
        """
        self.base_frequency = base_frequency
        self.sample_rate = sample_rate
        self.detection_threshold = 15.0
        self.confidence_threshold = 0.6
        
        # Initialize shruti system
        self.shrutis = self._initialize_shruti_system()
        self.shruti_frequencies = self._calculate_shruti_frequencies()
        
        # Detection history for pattern analysis
        self.detection_history = deque(maxlen=50)
        self.current_raga_context = None
        
        # Performance optimization
        self._frequency_cache = {}
        self.detection_lock = threading.Lock()
    
    def _initialize_shruti_system(self) -> List[Shruti]:
        """Initialize the 22-shruti system with traditional mappings"""
        shrutis = [
            # Shadja Grama (Sa family)
            Shruti("Shadja", "C", 0, 1.0, ["All ragas"]),
            Shruti("Suddha Ri", "C#♭", 90, 256/243, ["Mayamalavagowla", "Kalyani"]),
            Shruti("Chatussruti Ri", "D♭", 112, 16/15, ["Mohanam", "Sankarabharanam"]),
            Shruti("Shatsruti Ri", "D", 182, 10/9, ["Kharaharapriya", "Natabhairavi"]),
            Shruti("Suddha Ga", "D#♭", 294, 32/27, ["Todi", "Bhairavi"]),
            Shruti("Sadharana Ga", "E♭", 316, 5/4, ["Kharaharapriya"]),
            Shruti("Antara Ga", "E", 386, 81/64, ["Sankarabharanam", "Kalyani"]),
            
            # Madhyama (Ma family)
            Shruti("Suddha Ma", "F", 498, 4/3, ["Most ragas"]),
            Shruti("Prati Ma", "F#", 590, 729/512, ["Kalyani", "Shanmukhapriya"]),
            
            # Panchama (Pa family) 
            Shruti("Panchama", "G", 702, 3/2, ["All ragas except Varali"]),
            
            # Dhaivata (Dha family)
            Shruti("Suddha Dha", "G#♭", 792, 128/81, ["Natabhairavi", "Todi"]),
            Shruti("Chatussruti Dha", "A♭", 814, 8/5, ["Kharaharapriya"]),
            Shruti("Shatsruti Dha", "A", 884, 5/3, ["Sankarabharanam", "Mohanam"]),
            Shruti("Suddha Ni", "A#♭", 996, 16/9, ["Natabhairavi"]),
            Shruti("Kaisika Ni", "B♭", 1018, 9/5, ["Kharaharapriya"]),
            Shruti("Kakali Ni", "B", 1088, 15/8, ["Sankarabharanam", "Kalyani"]),
            
            # Microtonal variations (Pramana shrutis)
            Shruti("Ri Komal", "C#♭♭", 70, 25/24, ["Bhairavi variations"]),
            Shruti("Ga Tivra", "E♭+", 350, 125/96, ["Todi variations"]),
            Shruti("Dha Komal", "G#♭♭", 772, 25/16, ["Malkauns"]),
            Shruti("Ni Komal", "A#♭♭", 976, 125/72, ["Darbari"]),
            Shruti("Ma Tivra", "F#+", 610, 45/32, ["Raga Yaman"]),
            Shruti("Pa Komal", "G♭", 680, 64/45, ["Varali"])
        ]
        return shrutis
    
    def _calculate_shruti_frequencies(self) -> Dict[str, float]:
        """Calculate actual frequencies for each shruti based on base frequency"""
        frequencies = {}
        for shruti in self.shrutis:
            # Calculate frequency using just intonation ratios
            freq = self.base_frequency * shruti.frequency_ratio
            frequencies[shruti.name] = freq
            
            # Add octave variations
            for octave in range(-2, 4):
                octave_freq = freq * (2 ** octave)
                frequencies[f"{shruti.name}_{octave}"] = octave_freq
        
        return frequencies
    
    def detect_shruti(self, audio_data: np.ndarray, frames: int) -> Optional[DetectionResult]:
        """
        Detect Carnatic shruti from audio data with enhanced accuracy
        """
        with self.detection_lock:
            # Enhanced FFT analysis with windowing
            windowed_data = audio_data[:, 0] * np.hanning(len(audio_data))
            
            # Zero-pad for better frequency resolution
            fft_size = max(4096, len(windowed_data))
            padded_data = np.pad(windowed_data, (0, fft_size - len(windowed_data)))
            
            # Perform FFT
            fft_result = np.fft.rfft(padded_data)
            magnitude_spectrum = np.abs(fft_result)
            
            # Find peaks with minimum separation
            peak_indices = self._find_spectral_peaks(magnitude_spectrum)
            
            if not peak_indices:
                return None
            
            # Convert peaks to frequencies
            freq_resolution = self.sample_rate / fft_size
            peak_frequencies = peak_indices * freq_resolution
            peak_magnitudes = magnitude_spectrum[peak_indices]
            
            # Find best shruti match
            best_match = self._match_to_shruti(peak_frequencies, peak_magnitudes)
            
            if best_match:
                result = DetectionResult(
                    shruti=best_match['shruti'],
                    frequency=best_match['frequency'],
                    magnitude=best_match['magnitude'],
                    confidence=best_match['confidence'],
                    timestamp=time.time()
                )
                
                # Update detection history
                self.detection_history.append(result)
                
                # Analyze for raga context
                self._update_raga_context(result)
                
                return result
        
        return None
    
    def _find_spectral_peaks(self, magnitude_spectrum: np.ndarray, 
                           min_height: float = None) -> np.ndarray:
        """Find spectral peaks with noise reduction"""
        if min_height is None:
            min_height = self.detection_threshold
            
        # Simple peak finding - can be enhanced with scipy.signal.find_peaks
        peaks = []
        for i in range(1, len(magnitude_spectrum) - 1):
            if (magnitude_spectrum[i] > magnitude_spectrum[i-1] and 
                magnitude_spectrum[i] > magnitude_spectrum[i+1] and
                magnitude_spectrum[i] > min_height):
                peaks.append(i)
        
        return np.array(peaks)
    
    def _match_to_shruti(self, frequencies: np.ndarray, magnitudes: np.ndarray) -> Optional[Dict]:
        """Match detected frequencies to closest shruti"""
        best_match = None
        best_score = 0
        
        for freq, mag in zip(frequencies, magnitudes):
            if freq < 50 or freq > 2000:  # Reasonable vocal range
                continue
                
            # Find closest shruti
            min_distance = float('inf')
            closest_shruti = None
            
            for shruti_name, shruti_freq in self.shruti_frequencies.items():
                # Calculate cent difference (logarithmic frequency distance)
                cent_diff = abs(1200 * np.log2(freq / shruti_freq))
                
                # Accept matches within 25 cents (quarter semitone)
                if cent_diff < 25 and cent_diff < min_distance:
                    min_distance = cent_diff
                    closest_shruti = shruti_name
            
            if closest_shruti:
                # Calculate confidence based on magnitude and frequency accuracy
                frequency_accuracy = max(0, 1 - (min_distance / 25))
                magnitude_factor = min(1, mag / 100)
                confidence = (frequency_accuracy * 0.7 + magnitude_factor * 0.3)
                
                if confidence > self.confidence_threshold and confidence > best_score:
                    # Find shruti object
                    shruti_obj = None
                    shruti_base_name = closest_shruti.split('_')[0]
                    for s in self.shrutis:
                        if s.name == shruti_base_name:
                            shruti_obj = s
                            break
                    
                    if shruti_obj:
                        best_match = {
                            'shruti': shruti_obj,
                            'frequency': freq,
                            'magnitude': mag,
                            'confidence': confidence,
                            'cent_deviation': min_distance
                        }
                        best_score = confidence
        
        return best_match
    
    def _update_raga_context(self, result: DetectionResult):
        """Update raga context based on detection history"""
        if len(self.detection_history) < 5:
            return
        
        # Analyze recent detections for raga patterns
        recent_shrutis = [det.shruti.name for det in list(self.detection_history)[-10:]]
        
        # Simple raga pattern matching
        common_ragas = {
            'Sankarabharanam': ['Shadja', 'Chatussruti Ri', 'Antara Ga', 'Suddha Ma', 'Panchama', 'Shatsruti Dha', 'Kakali Ni'],
            'Kharaharapriya': ['Shadja', 'Chatussruti Ri', 'Sadharana Ga', 'Suddha Ma', 'Panchama', 'Chatussruti Dha', 'Kaisika Ni'],
            'Mayamalavagowla': ['Shadja', 'Suddha Ri', 'Antara Ga', 'Suddha Ma', 'Panchama', 'Suddha Dha', 'Kakali Ni'],
            'Mohanam': ['Shadja', 'Chatussruti Ri', 'Antara Ga', 'Panchama', 'Shatsruti Dha'],
            'Kalyani': ['Shadja', 'Chatussruti Ri', 'Antara Ga', 'Prati Ma', 'Panchama', 'Shatsruti Dha', 'Kakali Ni']
        }
        
        # Count matches for each raga
        raga_scores = {}
        for raga_name, raga_notes in common_ragas.items():
            score = sum(1 for shruti in recent_shrutis if shruti in raga_notes)
            raga_scores[raga_name] = score
        
        # Update current raga context
        if raga_scores:
            best_raga = max(raga_scores.keys(), key=lambda x: raga_scores[x])
            if raga_scores[best_raga] >= 3:
                self.current_raga_context = best_raga
    
    def get_raga_context(self) -> Optional[str]:
        """Get current raga context"""
        return self.current_raga_context
    
    def set_base_frequency(self, frequency: float):
        """Update base Sa frequency and recalculate shruti frequencies"""
        self.base_frequency = frequency
        self.shruti_frequencies = self._calculate_shruti_frequencies()
        self._frequency_cache.clear()
    
    def get_shruti_info(self, shruti_name: str) -> Optional[Dict]:
        """Get detailed information about a shruti"""
        for shruti in self.shrutis:
            if shruti.name == shruti_name:
                return {
                    'name': shruti.name,
                    'western_equiv': shruti.western_equiv,
                    'cent_value': shruti.cent_value,
                    'frequency': self.shruti_frequencies.get(shruti.name, 0),
                    'ratio': shruti.frequency_ratio,
                    'ragas': shruti.raga_usage
                }
        return None
    
    def export_detection_history(self) -> List[Dict]:
        """Export detection history for analysis"""
        return [
            {
                'shruti': det.shruti.name,
                'frequency': det.frequency,
                'magnitude': det.magnitude,
                'confidence': det.confidence,
                'timestamp': det.timestamp
            }
            for det in self.detection_history
        ]

# Audio callback function for real-time detection
def carnatic_audio_callback(detector: CarnaticNoteDetector, socketio=None):
    """Enhanced audio callback for Carnatic detection"""
    
    def callback(indata, frames, time_info, status):
        if status:
            print(f"Audio status: {status}", flush=True)
        
        result = detector.detect_shruti(indata, frames)
        
        if result and result.confidence > detector.confidence_threshold:
            # Format output
            output = {
                'shruti': result.shruti.name,
                'western_equiv': result.shruti.western_equiv,
                'frequency': round(result.frequency, 2),
                'detected_frequency': round(result.frequency, 2),
                'magnitude': round(result.magnitude, 2),
                'confidence': round(result.confidence, 3),
                'cent_value': result.shruti.cent_value,
                'raga_context': detector.get_raga_context(),
                'timestamp': result.timestamp
            }
            
            print(f"Detected shruti: {output['shruti']} ({output['western_equiv']}) - "
                  f"Freq: {output['frequency']} Hz, Confidence: {output['confidence']:.3f}", 
                  flush=True)
            
            # Emit to web interface if available
            if socketio:
                socketio.emit('note_detected', output)
    
    return callback

# Example usage
if __name__ == "__main__":
    # Initialize detector with Sa = C4 (261.63 Hz)
    detector = CarnaticNoteDetector(base_frequency=261.63)
    
    print("Carnatic Music Note Detector initialized")
    print("22-shruti system ready for detection")
    print("Base Sa frequency:", detector.base_frequency, "Hz")
    print("\nListening... Press Ctrl+C to stop")
    
    # Create callback
    callback = carnatic_audio_callback(detector)
    
    # Start audio stream
    try:
        with sd.InputStream(
            callback=callback,
            blocksize=2048,
            samplerate=detector.sample_rate,
            channels=1
        ):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping detection...")
        
        # Export history
        history = detector.export_detection_history()
        if history:
            with open('carnatic_detection_log.json', 'w') as f:
                json.dump(history, f, indent=2)
            print(f"Exported {len(history)} detections to carnatic_detection_log.json")