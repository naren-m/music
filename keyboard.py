import pyaudio
import librosa
import numpy as np

# Define the sampling rate and duration of the audio recording
sr = 44100
duration = 2

# Create an instance of PyAudio
pa = pyaudio.PyAudio()

# Open a stream for recording audio from the microphone
stream = pa.open(format=pyaudio.paFloat32,
                 channels=1,
                 rate=sr,
                 input=True,
                 frames_per_buffer=1024)

# Record audio for the specified duration
frames = []
for i in range(int(sr / 1024 * duration)):
    data = stream.read(1024)
    frames.append(np.frombuffer(data, dtype=np.float32))

# Convert the recorded audio to a mono audio signal
signal = np.concatenate(frames)
signal = librosa.to_mono(signal)

# Detect the piano notes in the audio signal
notes = librosa.onset.onset_detect(y=signal, sr=sr)

# Print the detected piano notes
print("Detected piano notes:")
for note in notes:
    print(librosa.hz_to_note(librosa.fft_frequencies(n_fft=2048, sr=sr)[note]))
