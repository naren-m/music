#!/usr/bin/env python3
"""
Standalone Carnatic Music Detection Script
Works with local microphone access outside Docker
"""

import sys
import os
import time
import json
from datetime import datetime

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from carnatic_detector import CarnaticNoteDetector, carnatic_audio_callback
    import sounddevice as sd
    import numpy as np
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("📦 Please install: pip install sounddevice numpy")
    sys.exit(1)

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_logo():
    """Display Carnatic music logo"""
    logo = """
🎵 ════════════════════════════════════════════ 🎵
   कर्णाटक संगीत श्रुति डिटेक्टर
   Carnatic Music Shruti Detection System
   22-Shruti Real-time Analysis
🎵 ════════════════════════════════════════════ 🎵
    """
    print(logo)

def list_audio_devices():
    """List available audio input devices"""
    print("\n🎤 Available Audio Input Devices:")
    print("-" * 50)
    devices = sd.query_devices()
    input_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append((i, device))
            print(f"{i:2d}: {device['name']}")
    
    return input_devices

def select_device(input_devices):
    """Let user select audio input device"""
    if not input_devices:
        print("❌ No audio input devices found!")
        return None
    
    print(f"\n🎯 Default device: {input_devices[0][0]} - {input_devices[0][1]['name']}")
    choice = input("\nSelect device number (or press Enter for default): ").strip()
    
    if not choice:
        return input_devices[0][0]
    
    try:
        device_id = int(choice)
        if any(dev[0] == device_id for dev in input_devices):
            return device_id
        else:
            print(f"⚠️  Device {device_id} not found, using default")
            return input_devices[0][0]
    except ValueError:
        print("⚠️  Invalid input, using default")
        return input_devices[0][0]

def get_base_frequency():
    """Get base Sa frequency from user"""
    print("\n🎼 Tune your Sa (Shadja):")
    print("   Common frequencies:")
    print("   C4  = 261.63 Hz (default)")
    print("   C#4 = 277.18 Hz")
    print("   D4  = 293.66 Hz")
    print("   Eb4 = 311.13 Hz")
    
    freq_input = input("\nEnter Sa frequency in Hz (or press Enter for 261.63): ").strip()
    
    if not freq_input:
        return 261.63
    
    try:
        frequency = float(freq_input)
        if 100 <= frequency <= 500:
            return frequency
        else:
            print("⚠️  Frequency should be between 100-500 Hz, using default")
            return 261.63
    except ValueError:
        print("⚠️  Invalid frequency, using default")
        return 261.63

class StandaloneInterface:
    """Terminal interface for standalone detection"""
    
    def __init__(self, detector):
        self.detector = detector
        self.detection_history = []
        self.session_start = time.time()
    
    def display_detection(self, result):
        """Display detection result in terminal"""
        clear_screen()
        display_logo()
        
        # Current detection
        print(f"🎵 Current Shruti: {result.shruti.name}")
        print(f"🎼 Western Equiv: {result.shruti.western_equiv}")
        print(f"📏 Frequency: {result.frequency:.2f} Hz")
        print(f"🎯 Expected: {self.detector.shruti_frequencies.get(result.shruti.name, 0):.2f} Hz")
        print(f"📊 Confidence: {result.confidence:.1%}")
        print(f"🔢 Cent Value: {result.shruti.cent_value}")
        
        # Raga context
        raga_context = self.detector.get_raga_context()
        if raga_context:
            print(f"🎭 Raga Context: {raga_context}")
        
        print("-" * 60)
        
        # Session stats
        session_time = int(time.time() - self.session_start)
        unique_shrutis = len(set(d.shruti.name for d in self.detection_history))
        
        print(f"📈 Session: {len(self.detection_history)} detections")
        print(f"🎼 Unique Shrutis: {unique_shrutis}")
        print(f"⏱️  Time: {session_time // 60}:{session_time % 60:02d}")
        
        # Recent history
        if len(self.detection_history) > 1:
            print("\n📜 Recent Detections:")
            for det in self.detection_history[-5:]:
                timestamp = datetime.fromtimestamp(det.timestamp).strftime("%H:%M:%S")
                print(f"   {timestamp} - {det.shruti.name} ({det.confidence:.1%})")
        
        print("\n🛑 Press Ctrl+C to stop detection")
    
    def add_detection(self, result):
        """Add detection to history"""
        self.detection_history.append(result)
        if len(self.detection_history) > 100:
            self.detection_history.pop(0)
        
        self.display_detection(result)
    
    def save_session(self):
        """Save session data"""
        if not self.detection_history:
            return
        
        filename = f"carnatic_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        session_data = {
            'session_start': self.session_start,
            'session_end': time.time(),
            'base_frequency': self.detector.base_frequency,
            'total_detections': len(self.detection_history),
            'unique_shrutis': len(set(d.shruti.name for d in self.detection_history)),
            'detections': [
                {
                    'shruti': d.shruti.name,
                    'western_equiv': d.shruti.western_equiv,
                    'frequency': d.frequency,
                    'confidence': d.confidence,
                    'timestamp': d.timestamp
                }
                for d in self.detection_history
            ]
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)
            print(f"💾 Session saved to: {filename}")
        except Exception as e:
            print(f"⚠️  Could not save session: {e}")

def main():
    """Main function"""
    clear_screen()
    display_logo()
    
    # List and select audio device
    input_devices = list_audio_devices()
    if not input_devices:
        print("❌ No microphone found. Please connect a microphone and try again.")
        return
    
    selected_device = select_device(input_devices)
    if selected_device is None:
        return
    
    # Get base frequency
    base_frequency = get_base_frequency()
    
    print(f"\n🎤 Using device: {selected_device}")
    print(f"🎼 Sa frequency: {base_frequency} Hz")
    print(f"⚙️  Initializing Carnatic detector...")
    
    # Initialize detector
    detector = CarnaticNoteDetector(base_frequency=base_frequency)
    interface = StandaloneInterface(detector)
    
    # Create callback that works with our interface
    def enhanced_callback(indata, frames, time_info, status):
        if status:
            print(f"Audio status: {status}", flush=True)
        
        result = detector.detect_shruti(indata, frames)
        
        if result and result.confidence > detector.confidence_threshold:
            interface.add_detection(result)
    
    print("🎵 Starting detection... Sing or play your instrument!")
    print("🛑 Press Ctrl+C to stop\n")
    
    try:
        with sd.InputStream(
            callback=enhanced_callback,
            blocksize=2048,
            samplerate=detector.sample_rate,
            channels=1,
            device=selected_device
        ):
            while True:
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        clear_screen()
        print("🎵 Detection stopped!")
        
        # Save session
        interface.save_session()
        
        # Show summary
        if interface.detection_history:
            session_time = int(time.time() - interface.session_start)
            unique_shrutis = len(set(d.shruti.name for d in interface.detection_history))
            avg_confidence = sum(d.confidence for d in interface.detection_history) / len(interface.detection_history)
            
            print(f"\n📊 Session Summary:")
            print(f"   Total detections: {len(interface.detection_history)}")
            print(f"   Unique shrutis: {unique_shrutis}")
            print(f"   Average confidence: {avg_confidence:.1%}")
            print(f"   Session duration: {session_time // 60}:{session_time % 60:02d}")
            
            if interface.detector.get_raga_context():
                print(f"   Detected raga context: {interface.detector.get_raga_context()}")
        
        print("\n🙏 Thank you for using Carnatic Music Detection!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure your microphone is connected and accessible.")

if __name__ == "__main__":
    main()