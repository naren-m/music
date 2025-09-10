import numpy as np
import sounddevice as sd
import os
import sys

# Source: https://www.seventhstring.com/resources/notefrequencies.html
# 	C	    C#	    D	    Eb	    E	    F	    F#	    G	    G#	    A	    Bb	    B
# 0	16.35	17.32	18.35	19.45	20.60	21.83	23.12	24.50	25.96	27.50	29.14	30.87
# 1	32.70	34.65	36.71	38.89	41.20	43.65	46.25	49.00	51.91	55.00	58.27	61.74
# 2	65.41	69.30	73.42	77.78	82.41	87.31	92.50	98.00	103.8	110.0	116.5	123.5
# 3	130.8	138.6	146.8	155.6	164.8	174.6	185.0	196.0	207.7	220.0	233.1	246.9
# 4	261.6	277.2	293.7	311.1	329.6	349.2	370.0	392.0	415.3	440.0	466.2	493.9
# 5	523.3	554.4	587.3	622.3	659.3	698.5	740.0	784.0	830.6	880.0	932.3	987.8
# 6	1047	1109	1175	1245	1319	1397	1480	1568	1661	1760	1865	1976
# 7	2093	2217	2349	2489	2637	2794	2960	3136	3322	3520	3729	3951
# 8	4186	4435	4699	4978	5274	5588	5920	6272	6645	7040	7459	7902

NOTE_FREQS = {
    "C0": 16.35,
    "C#0": 17.32,
    "D0": 18.35,
    "Eb0": 19.45,
    "E0": 20.60,
    "F0": 21.83,
    "F#0": 23.12,
    "G0": 24.50,
    "G#0": 25.96,
    "A0": 27.50,
    "Bb0": 29.14,
    "B0": 30.87,
    "C1": 32.70,
    "C#1": 34.65,
    "D1": 36.71,
    "Eb1": 38.89,
    "E1": 41.20,
    "F1": 43.65,
    "F#1": 46.25,
    "G1": 49.00,
    "G#1": 51.91,
    "A1": 55.00,
    "Bb1": 58.27,
    "B1": 61.74,
    "C2": 65.41,
    "C#2": 69.30,
    "D2": 73.42,
    "Eb2": 77.78,
    "E2": 82.41,
    "F2": 87.31,
    "F#2": 92.50,
    "G2": 98.00,
    "G#2": 103.8,
    "A2": 110.0,
    "Bb2": 116.5,
    "B2": 123.5,
    "C3": 130.8,
    "C#3": 138.6,
    "D3": 146.8,
    "Eb3": 155.6,
    "E3": 164.8,
    "F3": 174.6,
    "F#3": 185.0,
    "G3": 196.0,
    "G#3": 207.7,
    "A3": 220.0,
    "Bb3": 233.1,
    "B3": 246.9,
    "C4": 261.6,
    "C#4": 277.2,
    "D4": 293.7,
    "Eb4": 311.1,
    "E4": 329.6,
    "F4": 349.2,
    "F#4": 370.0,
    "G4": 392.0,
    "G#4": 415.3,
    "A4": 440.0,
    "Bb4": 466.2,
    "B4": 493.9,
    "C5": 523.3,
    "C#5": 554.4,
    "D5": 587.3,
    "Eb5": 622.3,
    "E5": 659.3,
    "F5": 698.5,
    "F#5": 740.0,
    "G5": 784.0,
    "G#5": 830.6,
    "A5": 880.0,
    "Bb5": 932.3,
    "B5": 987.8,
    "C6": 1047,
    "C#6": 1109,
    "D6": 1175,
    "Eb6": 1245,
    "E6": 1319,
    "F6": 1397,
    "F#6": 1480,
    "G6": 1568,
    "G#6": 1661,
    "A6": 1760,
    "Bb6": 1865,
    "B6": 1976,
    "C7": 2093,
    "C#7": 2217,
    "D7": 2349,
    "Eb7": 2489,
    "E7": 2637,
    "F7": 2794,
    "F#7": 2960,
    "G7": 3136,
    "G#7": 3322,
    "A7": 3520,
    "Bb7": 3729,
    "B7": 3951,
    "C8": 4186,
    "C#8": 4435,
    "D8": 4699,
    "Eb8": 4978,
    "E8": 5274,
    "F8": 5588,
    "F#8": 5920,
    "G8": 6272,
    "G#8": 6645,
    "A8": 7040,
    "Bb8": 7459,
    "B8": 7902,
}

FREQ_TRESHOLD = 1

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def create_waveform_visualization(magnitude_array, width=80):
    """Create enhanced ASCII waveform with visual appeal"""
    if len(magnitude_array) == 0:
        return "─" * width
    
    # Normalize the magnitude array
    max_mag = max(magnitude_array) if magnitude_array else 1
    normalized = [int((mag / max_mag) * 10) for mag in magnitude_array[-width:]]
    
    # Enhanced ASCII bars with color-like representation
    chars = [' ', '░', '▒', '▓', '▁', '▂', '▃', '▄', '▅', '▆', '█']
    waveform = ''.join(chars[min(level, 10)] for level in normalized)
    
    # Pad if necessary
    return waveform.ljust(width, '─')

def calculate_confidence(frequency, closest_freq, magnitude):
    """Calculate confidence based on frequency match and magnitude"""
    freq_diff = abs(frequency - closest_freq)
    freq_confidence = max(0, 100 - (freq_diff * 2))
    mag_confidence = min(100, magnitude * 2)
    return min(freq_confidence, mag_confidence)

def format_data_row(note, frequency, confidence, volume):
    """Format the main data row with consistent spacing"""
    return f"♪ {note:>4} │ {frequency:>7.1f}Hz │ {confidence:>5.1f}% │ {volume:>5.1f}% ♪"

def format_waveform_row(waveform):
    """Format the waveform row with visual enhancements"""
    return f"♫ {waveform} ♫"

def get_confidence_indicator(confidence):
    """Get visual confidence indicator"""
    if confidence >= 90:
        return "🟢"
    elif confidence >= 70:
        return "🟡" 
    elif confidence >= 50:
        return "🟠"
    else:
        return "🔴"

def get_volume_bar(volume, width=20):
    """Create a visual volume level bar"""
    filled = int((volume / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}]"

# Define a function to find the closest note to a given frequency
def find_closest_note_freq(frequency):
    distances = {n: abs(frequency - f) for n, f in NOTE_FREQS.items()}
    closest_note, closest_freq = min(distances.items(), key=lambda x: x[1])
    return closest_note, closest_freq


def get_magnitude_frequency(indata, frames):
    # Convert audio data to frequency domain using FFT
    magnitude = np.abs(np.fft.rfft(indata[:, 0]))
    # Find the frequency with maximum magnitude
    max_magnitude_idx = np.argmax(magnitude)
    frequency = max_magnitude_idx * sample_rate / frames

    return magnitude[max_magnitude_idx], frequency, magnitude

# Global variables for visualization
magnitude_history = []
last_display_time = 0
display_interval = 0.1  # Update display every 100ms

# Define the audio processing callback function
def audio_callback(indata, frames, sTime, status):
    global magnitude_history, last_display_time
    
    if status:
        print(status, flush=True)

    magnitude, frequency, full_magnitude = get_magnitude_frequency(indata, frames)
    
    # Add magnitude to history for waveform
    magnitude_history.append(magnitude)
    if len(magnitude_history) > 100:  # Keep last 100 samples
        magnitude_history.pop(0)

    if magnitude < 9 or frequency < FREQ_TRESHOLD:
        return

    # Find the closest note to the detected frequency
    closest_note, closest_freq = find_closest_note_freq(frequency)
    if closest_note:
        # Calculate confidence and normalize volume
        confidence = calculate_confidence(frequency, NOTE_FREQS[closest_note], magnitude)
        volume = min(100, magnitude / 2)  # Normalize volume to 0-100
        
        # Only update display every display_interval seconds
        current_time = sTime
        if current_time - last_display_time >= display_interval:
            # Clear screen and display enhanced UI
            clear_screen()
            
            # Modern header with better typography
            print("┌─────────────────────────────────────────────────────────────────────────────────┐")
            print("│                          🎵 REAL-TIME NOTE DETECTION 🎵                          │")
            print("└─────────────────────────────────────────────────────────────────────────────────┘")
            print()
            
            # Main data row - clean and focused
            confidence_indicator = get_confidence_indicator(confidence)
            data_row = format_data_row(closest_note, frequency, confidence, volume)
            print(f"  {confidence_indicator} {data_row}")
            print()
            
            # Waveform visualization row
            waveform = create_waveform_visualization(magnitude_history, 75)
            waveform_row = format_waveform_row(waveform)
            print(f"  {waveform_row}")
            print()
            
            # Volume level bar
            volume_bar = get_volume_bar(volume, 30)
            print(f"  🔊 Volume: {volume_bar} {volume:>5.1f}%")
            print()
            
            # Technical details (compact)
            freq_diff = frequency - NOTE_FREQS[closest_note]
            print("┌─────────────────────────────────────────────────────────────────────────────────┐")
            print(f"│ Target: {NOTE_FREQS[closest_note]:>7.1f}Hz │ Detected: {frequency:>7.1f}Hz │ Difference: {freq_diff:>+6.1f}Hz │")
            print("└─────────────────────────────────────────────────────────────────────────────────┘")
            print()
            print("  💡 Tip: Use a microphone close to your instrument for best results")
            print("  ⌨️  Press Ctrl+C to stop")
            
            last_display_time = current_time

# Set the audio sampling rate
device = None
sample_rate = 44100
device_info = sd.query_devices(device, 'input')
sample_rate = device_info['default_samplerate']

print("┌─────────────────────────────────────────────────────────────────────────────────┐")
print("│                      🎤 AUDIO SYSTEM INITIALIZATION 🎤                        │")
print("└─────────────────────────────────────────────────────────────────────────────────┘")
print()
print(f"  ⚙️  Sample Rate: {sample_rate}Hz")
print(f"  🎵 Note Range: C0 ({NOTE_FREQS['C0']}Hz) to B8 ({NOTE_FREQS['B8']}Hz)")
print(f"  🔍 Detection Threshold: {FREQ_TRESHOLD}Hz")
print()
print("  🟢 System ready! Start playing music...")
print()

# Start the audio stream and run the audio processing callback function
try:
    with sd.InputStream(callback=audio_callback, blocksize=2048, samplerate=sample_rate):
        while True:
            pass
except KeyboardInterrupt:
    clear_screen()
    print("┌─────────────────────────────────────────────────────────────────────────────────┐")
    print("│                          🎵 SESSION COMPLETE 🎵                               │")
    print("└─────────────────────────────────────────────────────────────────────────────────┘")
    print()
    print("  ✅ Note detection stopped successfully")
    print("  🙏 Thank you for using the note detector!")
    print()
except Exception as e:
    clear_screen()
    print("┌─────────────────────────────────────────────────────────────────────────────────┐")
    print("│                            ❌ ERROR OCCURRED ❌                               │")
    print("└─────────────────────────────────────────────────────────────────────────────────┘")
    print()
    print(f"  🔧 Error details: {e}")
    print("  💡 Try checking your microphone connection")
    print()
