import pyaudio
import numpy as np
import plotly.graph_objs as go
import music21

# Constants
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 22050  # Reduced sample rate
CHUNK = 4096 # increased buffer size

# Create a new PyAudio object
p = pyaudio.PyAudio()
detected_notes = []

# Open a stream to capture audio
# stream = p.open(format=FORMAT,
#                 channels=CHANNELS,
#                 rate=RATE,
#                 input=True,
#                 input_device_index=0, # adjust input device index as necessary
#                 frames_per_buffer=CHUNK,
#                 input_gain=0.5) # adjust input volume as necessary

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

# Define a function to detect the music note from audio data
def detect_note(data):
    # Process the audio data and detect the music note
    # ...
    # Convert the data to a numpy array
    note_to_detect = music21.note.Note('C#5')

    numpy_data = np.frombuffer(data, dtype=np.float32)

    # Apply a Fast Fourier Transform (FFT) to the data
    fft_data = np.fft.fft(numpy_data)

    # Calculate the frequencies corresponding to the FFT data
    freqs = np.fft.fftfreq(len(fft_data)) * RATE

    # Find the index of the frequency closest to the note we want to detect
    idx = (np.abs(freqs - note_to_detect.pitch.frequency)).argmin()

    # Get the magnitude of the FFT data at that frequency
    magnitude = np.abs(fft_data[idx])

    # Check if the magnitude is above a certain threshold
    if magnitude > 1e7:
        # Add the detected note to the list
        detected_notes.append(note_to_detect)

# Create a new plotly figure
fig = go.Figure()
fig.add_scatter()
# Create a new scatter trace for the audio data
trace = go.Scatter(x=[], y=[], mode='lines')

# Add the trace to the figure
fig.add_trace(trace)

# Set the layout of the figure
fig.update_layout(title='Live Audio Stream',
                  xaxis=dict(title='Time (s)'),
                  yaxis=dict(title='Amplitude'))

# Start the audio stream
stream.start_stream()

# Loop to read audio data from the stream
while True:
    try:
        # Read a chunk of audio data from the stream
        data = stream.read(CHUNK)
        # Convert the audio data to a numpy array
        data = np.frombuffer(data, dtype=np.float32)
        # Detect the music note from the audio data
        note = detect_note(data)
        # Add the audio data to the plotly figure
        fig.update_xaxes(range=[0, len(data)/RATE])
        fig.update_yaxes(range=[-1, 1])
        fig.data[0].x = np.arange(len(data))/RATE
        fig.data[0].y = data
        # Display the plotly figure
        # fig.show()
    except IOError as e:
        # If input overflows, skip this chunk and continue
        if e.errno == pyaudio.paInputOverflowed:
            print("Input overflowed - skipping chunk")
            stream.read(CHUNK)
        else:
            print("Error:", e)

# Stop the audio stream
stream.stop_stream()
stream.close()
p.terminate()
