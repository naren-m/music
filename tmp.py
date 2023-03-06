import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np
import sounddevice as sd
import librosa
import librosa.display

# Constants for audio processing
FRAME_SIZE = 2048
HOP_SIZE = 512
SAMPLE_RATE = 44100

# Constants for note detection
NOTE_RANGE = 48  # Number of notes to consider (starting from A0)
CQT_BINS = 7 * NOTE_RANGE  # Number of frequency bins in CQT
CQT_FMIN = librosa.note_to_hz('C6')  # Minimum frequency for CQT

# Set up the figure with two subplots: audio waveform and note detection
fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
audio_trace = go.Scatter(x=[], y=[], mode='lines', name='Audio waveform')
fig.add_trace(audio_trace, row=1, col=1)
note_trace = go.Scatter(x=[], y=[], mode='markers', name='Detected notes')
fig.add_trace(note_trace, row=2, col=1)

# Define the callback function that will be called with each new audio buffer
def audio_callback(indata, frames, time, status):
    # Compute the CQT of the audio signal
    # cqt = np.abs(librosa.cqt(indata[:, 0], sr=SAMPLE_RATE, hop_length=HOP_SIZE,
    #                          n_bins=CQT_BINS, fmin=CQT_FMIN))
    cqt =  np.abs(librosa.cqt(indata[:, 0], sr=SAMPLE_RATE, hop_length=HOP_SIZE, fmin=CQT_FMIN,
                              n_bins=CQT_BINS, bins_per_octave=24))


    # Compute the mean magnitude of each note across all frequency bins
    note_mags = np.zeros(NOTE_RANGE)
    for i in range(NOTE_RANGE):
        note_mags[i] = cqt[i*7:(i+1)*7, :].mean()

    # Detect the note with the highest magnitude
    max_note = note_mags.argmax()
    max_mag = note_mags[max_note]

    # Convert the note index to a MIDI note number and frequency
    midi_note = max_note + 21  # MIDI note numbers start at 21 for A0
    freq = librosa.midi_to_hz(midi_note)

    # Add the detected note to the plot
    note_trace.x.append(time.time())
    note_trace.y.append(freq)

    # Truncate the plot data to only show the most recent 5 seconds
    if len(note_trace.x) > 0 and time.time() - note_trace.x[0] > 5:
        note_trace.x.pop(0)
        note_trace.y.pop(0)

    # Update the audio waveform plot
    audio_trace.x = np.arange(len(indata)) / SAMPLE_RATE
    audio_trace.y = indata[:, 0]

    # Update the plot layout
    fig.update_layout(title='Live Note Detection',
                      xaxis=dict(title='Time (s)'),
                      yaxis=dict(title='Frequency (Hz)', range=[0, 400]))

    # Update the plot
    fig.update()

# Start the audio stream
stream = sd.InputStream(channels=1, samplerate=SAMPLE_RATE, blocksize=FRAME_SIZE,
                         callback=audio_callback)
stream.start()

# Show the plot
fig.show()
