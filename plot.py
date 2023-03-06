import pyaudio
import numpy as np
import plotly.graph_objs as go

# Define constants
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100
CHUNK_SIZE = 2048
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
# Define the layout for the Plotly graph
layout = go.Layout(
    title="Detected Music Notes",
    xaxis=dict(title="Time (s)"),
    yaxis=dict(title="Note")
)

# Create the Plotly figure and traces
fig = go.Figure(layout=layout)
freq_trace = go.Scatter(x=[], y=[], mode="lines", name="Frequency")
note_trace = go.Scatter(x=[], y=[], mode="markers", name="Note")
fig.add_trace(freq_trace)
fig.add_trace(note_trace)

# Create the PyAudio stream
pa = pyaudio.PyAudio()
stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK_SIZE
)

# Define a function to find the closest note to a given frequency
def find_closest_note_freq(frequency):
    distances = {n: abs(frequency - f) for n, f in NOTE_FREQS.items()}
    closest_note, closest_freq = min(distances.items(), key=lambda x: x[1])
    return closest_note, closest_freq

# Start the stream and update the Plotly graph in real-time
t = 0
while True:
    # Read audio data from the stream
    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
    samples = np.frombuffer(data, dtype=np.float32)

    # Compute the FFT of the audio samples
    freqs = np.fft.rfftfreq(len(samples), d=1/RATE)
    fft = np.fft.rfft(samples)
    fft_db = 20 * np.log10(np.abs(fft))

    # Find the peak frequency and note
    peak_freq = freqs[np.argmax(fft_db)]
    closest_note, closest_freq = find_closest_note_freq(peak_freq)

    # Add the data to the Plotly traces
    freq_trace.x = np.append(freq_trace.x, t)
    freq_trace.y = np.append(freq_trace.y, peak_freq)
    note_trace.x = np.append(note_trace.x, t)
    note_trace.y = np.append(note_trace.y, closest_note)

    # Update the Plotly figure layout
    fig.layout.xaxis.range = [t - 10, t]

    # Update the Plotly figure
    fig.show()

    # Increment the time counter
    t += CHUNK_SIZE / RATE
