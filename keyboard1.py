import pyaudio
import librosa
import numpy as np

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
}

# Define the frequency range to check around each note frequency
FREQ_TOLERANCE = 1.5

# Initialize the PyAudio object
pa = pyaudio.PyAudio()

# Open the audio stream
stream = pa.open(format=pyaudio.paFloat32,
                 channels=CHANNELS,
                 rate=RATE,
                 input=True,
                 frames_per_buffer=CHUNK_SIZE)

def start(stream, pa):
    while True:
        # Read a chunk of audio data from the stream
        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)

        # Convert the raw audio data to a numpy array
        audio = np.frombuffer(data, dtype=np.float32)

        # Compute the short-time Fourier transform (STFT) of the audio
        # audio_padded = np.concatenate((audio, np.zeros_like(audio)))
        # stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        stft = librosa.stft(audio, n_fft=1024, hop_length=512)


        # Compute the magnitude spectrogram of the STFT
        mag_spec = np.abs(stft)

        # Find the index of the frequency bin with the maximum magnitude
        max_idx = np.argmax(mag_spec)

        # Compute the frequency of the note with the maximum magnitude
        freq = librosa.fft_frequencies(sr=RATE, n_fft=2048)[max_idx]

        # Determine if the detected frequency falls within the range of any note frequency
        note = None
        for n, f in NOTE_FREQS.items():
            if abs(freq - f) <= FREQ_TOLERANCE:
                note = n
                break

        # Print the detected note
        if note is not None:
            print(note)

try:
    start(stream, pa)
except KeyboardInterrupt:
    # Clean up the audio stream and PyAudio object
    stream.stop_stream()
    stream.close()
    pa.terminate()