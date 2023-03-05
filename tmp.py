import librosa
import numpy as np


def print_notes(note_matrix):
    prev_notes = [''] * note_matrix.shape[1]  # Initialize with empty strings
    for i in range(note_matrix.shape[0]):
        notes = []
        for j in range(note_matrix.shape[1]):
            note = note_matrix[i, j]
            if note != '':
                notes.append(note)
        if notes != prev_notes:
            print(f"Frame {i}: {' '.join(notes)}")
            prev_notes = notes


def get_notes(audio_file):

    # Load the audio file
    # audio_path = 'path/to/audio/file.wav'
    y, sr = librosa.load(audio_path)

    # Extract chroma features from the audio signal
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)

    # Convert chroma features to log frequencies
    log_freqs = librosa.core.cqt_frequencies(
        chroma.shape[0],
        fmin=librosa.note_to_hz('A0'))[:, np.newaxis] * np.arange(
            chroma.shape[1])

    # Replace any zero values in the log_freqs array with a small positive value
    log_freqs = np.where(log_freqs == 0, 1e-9, log_freqs)

    # Convert log frequencies to MIDI numbers
    midi = librosa.core.hz_to_midi(2**(np.log2(log_freqs / 440.0)))

    # Clip the MIDI values to the valid range (0-127)
    midi = np.clip(midi, 0, 127)

    # Convert MIDI numbers to notes
    notes = librosa.core.midi_to_note(midi)
    return notes


def get_notes2(audio_path):
    y, sr = librosa.load(audio_path, sr=None, mono=True)

    # Extract chroma features
    hop_length = 512
    chromagram = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)

    # Convert chroma features to notes
    notes = []
    for i in range(chromagram.shape[1]):
        chroma_vector = chromagram[:, i]
        # Find the index of the maximum value in the chroma vector
        note_index = np.argmax(chroma_vector)
        # Convert the index to a MIDI note number
        note_midi = note_index + 24
        # Convert the MIDI note number to a note name
        note_name = librosa.midi_to_note(note_midi)
        notes.append(note_name)

    return notes


audio_path = './twinkle-twinkle.wav'
notes = get_notes2(audio_path)
# Print the notes
print(notes)
print(len(notes))
