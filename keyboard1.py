import pyaudio
import librosa
import numpy as np
from scipy.spatial.distance import euclidean

# Define the audio parameters
CHANNELS = 1
RATE = 44100
CHUNK_SIZE = 1024

# Define the frequency range of the notes on the keyboard
NOTE_FREQS = {
    'C2': 65.41,
    'C#2': 69.30,
    'D2': 73.42,
    'D#2': 77.78,
    'E2': 82.41,
    'F2': 87.31,
    'F#2': 92.50,
    'G2': 98.00,
    'G#2': 103.83,
    'A2': 110.00,
    'A#2': 116.54,
    'B2': 123.47,
    'C3': 130.81,
    'C#3': 138.59,
    'D3': 146.83,
    'D#3': 155.56,
    'E3': 164.81,
    'F3': 174.61,
    'F#3': 185.00,
    'G3': 196.00,
    'G#3': 207.65,
    'A3': 220.00,
    'A#3': 233.08,
    'B3': 246.94,
    'C4': 261.63,
    'C#4': 277.18,
    'D4': 293.66,
    'D#4': 311.13,
    'E4': 329.63,
    'F4': 349.23,
    'F#4': 369.99,
    'G4': 392.00,
    'G#4': 415.30,
    'A4': 440.00,
    'A#4': 466.16,
    'B4': 493.88,
    'C5': 523.25,
    'C#5': 554.37,
    'D5': 587.33,
    'D#5': 622.25,
    'E5': 659.25,
    'F5': 698.46,
    'F#5': 739.99,
    'G5': 783.99,
    'G#5': 830.61,
    'A5': 880.00,
    'A#5': 932.33,
    'B5': 987.77,
    'C6': 1046.50,
    'C#6': 1108.73,
    'D6': 1174.66,
    'D#6': 1244.51,
    'E6': 1318.51,
    'F6': 1396.91,
    'F#6': 1479.98,
    'G6': 1567.98,
    'G#6': 1661.22,
    'A6': 1760.00,
    'A#6': 1864.66,
    'B6': 1975.53,
    'C7': 2093.00,
    'C#7': 2217.46,
    'D7': 2349.32,
    'D#7': 2489.02,
    'E7': 2637.02,
    'F7': 2793.83,
    'F#7': 2959.96,
    'G7': 3135.96,
    'G#7': 3322.44,
    'A7': 3520
}

# Initialize the PyAudio object
pa = pyaudio.PyAudio()

# Define the frequency range to check around each note frequency
FREQ_TOLERANCE = 1.5
DISTANCE_TOLERANCE = 5

# Open the audio stream
stream = pa.open(format=pyaudio.paFloat32,
                 channels=CHANNELS,
                 rate=RATE,
                 input=True,
                 frames_per_buffer=CHUNK_SIZE)


# Define a function to find the closest note to a given frequency
def find_closest_note_freq(frequency, dist_tol=DISTANCE_TOLERANCE):
    distances = {n: abs(frequency - f) for n, f in NOTE_FREQS.items()}
    closest_note, distance = min(distances.items(), key=lambda x: x[1])
    closest_freq = NOTE_FREQS[closest_note]
    if distance > dist_tol:
        return None, None, None
    return closest_note, closest_freq, distance


def start():
    # Continuously record and process the audio
    while True:
        # Read a chunk of audio data from the stream
        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)

        # Convert the raw audio data to a numpy array
        audio = np.frombuffer(data, dtype=np.float32)

        # Compute the short-time Fourier transform (STFT) of the audio
        stft = librosa.stft(audio, n_fft=1024, hop_length=512)

        # Compute the magnitude spectrogram of the STFT
        mag_spec = np.abs(stft)

        # Find the index of the frequency bin with the maximum magnitude
        max_idx = np.argmax(mag_spec)

        # Compute the frequency of the note with the maximum magnitude
        freq = librosa.fft_frequencies(sr=RATE, n_fft=1024)[max_idx]

        # Determine which note corresponds to the frequency
        closest_note, closest_freq, distance = find_closest_note_freq(freq)
        if closest_note is not None:
            print('Closest distance note', closest_note, freq, closest_freq,
                  distance)

        note = None
        for n, f in NOTE_FREQS.items():
            if abs(freq - f) < FREQ_TOLERANCE:
                note = n
                break
        if note is not None:
            print("Regular", note)


try:
    start()
except Exception as e:
    print("Exception", e)
except KeyboardInterrupt:
    # Clean up the audio stream and PyAudio object
    stream.stop_stream()
    stream.close()
    pa.terminate()
