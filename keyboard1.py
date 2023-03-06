import pyaudio
import librosa
import numpy as np
from scipy.spatial.distance import euclidean

# Define the audio parameters
CHANNELS = 1
RATE = 44100
CHUNK_SIZE = 1024

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
            print(
                'Frequence heard: {freq}, closest: {closest_freq}, freq diff: {distance}. \nNote: {closest_note}'
                .format(freq=freq,
                        closest_freq=closest_freq,
                        distance=distance,
                        closest_note=closest_note))

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
