import numpy as np
import sounddevice as sd
import librosa.display
import matplotlib.pyplot as plt
import plotly.graph_objects as go

NOTE_FREQS = {
    'C': 16.35,
    'C#': 17.32,
    'D': 18.35,
    'Eb': 19.45,
    'E': 20.60,
    'F': 21.83,
    'F#': 23.12,
    'G': 24.50,
    'G#': 25.96,
    'A': 27.50,
    'Bb': 29.14,
    'B': 30.87,
}

def get_closest_note_freq(freq):
    closest_note = min(NOTE_FREQS, key=lambda n: abs(NOTE_FREQS[n]-freq))
    closest_freq = NOTE_FREQS[closest_note]
    return closest_note, closest_freq

def plot_live_audio(indata, frames, fig):
    # Compute spectrogram
    spectrogram = np.abs(librosa.stft(indata[:, 0]))

    # Compute log-scale mel spectrogram
    logmel_spectrogram = librosa.power_to_db(
        librosa.feature.melspectrogram(
            y=indata[:, 0], sr=sd.query_devices('default')['default_samplerate']
        ),
        ref=np.max
    )

    # Compute pitch
    pitch, _ = librosa.core.pitch.piptrack(
        y=indata[:, 0],
        sr=sd.query_devices('default')['default_samplerate'],
        fmin=20,
        fmax=4000
    )
    pitch = pitch[:, 0]

    # Get the closest note to the pitch
    note, freq = get_closest_note_freq(pitch)

    # Add the note to the plot
    fig.add_trace(go.Scatter(
        x=[time_info['current_time']],
        y=[freq],
        mode='markers',
        name='Note',
        marker=dict(color='red', size=10),
    ))

    # Update x-axis range of plot
    fig.update_xaxes(range=[time_info['current_time']-5, time_info['current_time']])

    # Update title of plot
    fig.update_layout(title=f"Live Audio - Note: {note} ({freq:.2f} Hz)")

    # Update the logmel spectrogram plot
    fig['layout']['xaxis2']['range'] = [time_info['current_time']-5, time_info['current_time']]
    fig['layout']['yaxis2']['range'] = [0, 5]
    fig['layout']['yaxis2']['autorange'] = False
    fig['layout']['yaxis2']['title'] = 'Log-Mel Spectrogram'
    fig['data'][1]['z'] = logmel_spectrogram[:, int(time_info['samples_since_start']/512):int(time_info['samples_since_start']/512)+288].tolist()

# Initialize live audio stream
stream = sd.InputStream(
    channels=1, blocksize=2048,
    samplerate=sd.query_devices('default')['default_samplerate']
)

# Initialize plot
fig = go.FigureWidget()
fig.add_trace(go.Scatter(x=[], y=[], mode='lines', name='Note'))
fig.add_trace(go.Heatmap(z=[], colorscale='viridis'))

# Start audio stream and plot live audio
with stream:
    while True:
        time_info, indata = stream.read(2048)
        plot_live_audio(indata,
