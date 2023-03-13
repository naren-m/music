import numpy as np
import librosa
import pyaudio

class MusicGenerator:
    def __init__(self):
        self.sample_rate = 22050
        self.duration = 0.5
        self.volume = 0.5
        self.notes = {
            'C': 0,
            'C#': 1,
            'D': 2,
            'D#': 3,
            'E': 4,
            'F': 5,
            'F#': 6,
            'G': 7,
            'G#': 8,
            'A': 9,
            'A#': 10,
            'B': 11
        }
        self.chroma = {
            'C': 0,
            'C#': 1,
            'D': 2,
            'D#': 3,
            'E': 4,
            'F': 5,
            'F#': 6,
            'G': 7,
            'G#': 8,
            'A': 9,
            'A#': 10,
            'B': 11
        }

    def generate_chord(self, root, chord_type, duration):
        chroma = np.zeros(12)
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        semitones = 0

        for interval in chord_type:
            if interval.isdigit():
                semitones += int(interval)
            elif interval == 'm':
                semitones += 3
            elif interval == 'M':
                semitones += 4
            elif interval == 'A':
                semitones += 5

        chroma[(semitones + self.notes[root]) % 12] = 1
        chord = librosa.util.normalize(chroma)

        samples = np.zeros(int(duration * self.sample_rate))
        waveform = np.array([])

        for i, note in enumerate(notes):
            if chord[i] != 0:
                waveform = np.append(waveform, librosa.core.tone(440 * 2 ** ((i - self.notes['A']) / 12), self.sample_rate, self.duration) * self.volume)

        waveform *= (2 ** 15 - 1) / np.max(np.abs(waveform))
        samples[:waveform.shape[0]] += waveform
        return samples.astype(np.int16)

if __name__ == '__main__':
    mg = MusicGenerator()
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=mg.sample_rate, output=True)

    # Generate and play C major chord for 2 seconds
    signal = mg.generate_chord('C', 'major', 2)
    stream.write
