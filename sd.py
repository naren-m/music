import numpy as np
import sounddevice as sd

# Define the known note frequencies
NOTE_FREQS = {
    "C": 16.35,
    "C#": 17.32,
    "D": 18.35,
    "Eb": 19.45,
    "E": 20.60,
    "F": 21.83,
    "F#": 23.12,
    "G": 24.50,
    "G#": 25.96,
    "A": 27.50,
    "Bb": 29.14,
    "B": 30.87
}

# Define a function to find the closest note to a given frequency
def find_closest_note_freq(frequency):
    distances = {n: abs(frequency - f) for n, f in NOTE_FREQS.items()}
    closest_note, closest_freq = min(distances.items(), key=lambda x: x[1])
    return closest_note, closest_freq

# Define the audio processing callback function
def audio_callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    # Convert audio data to frequency domain using FFT
    magnitude = np.abs(np.fft.rfft(indata[:, 0]))
    # Find the frequency with maximum magnitude
    max_magnitude_idx = np.argmax(magnitude)
    frequency = max_magnitude_idx * sample_rate / frames
    # Find the closest note to the detected frequency
    closest_note, closest_freq = find_closest_note_freq(frequency)
    # Print the detected note and frequency
    print(f"Detected note: {closest_note}, frequency: {closest_freq:.2f} Hz", flush=True)

# Set the audio sampling rate
sample_rate = 44100

# Start the audio stream and run the audio processing callback function
with sd.InputStream(callback=audio_callback, blocksize=2048, samplerate=sample_rate):
    while True:
        pass
