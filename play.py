import pyaudio
import numpy as np
import librosa


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

class MusicGenerator:
    def __init__(self, sr=22050, duration=1):
        self.sr = sr
        self.duration = duration
        self.p = pyaudio.PyAudio()

    def generate_sinewave(self, frequency):
        samples = self.sr * self.duration
        t = np.linspace(0, self.duration, samples, False)
        note = np.sin(frequency * t * 2 * np.pi)
        return note.astype(np.float32)

    def play_sound(self, frequency):
        note = self.generate_sinewave(frequency)
        stream = self.p.open(format=pyaudio.paFloat32,
                             channels=1,
                             rate=self.sr,
                             output=True)
        stream.write(note.tobytes())
        stream.stop_stream()
        stream.close()

    def play_sequence(self, notes, durations):
        for n in notes:
            self.play_sound(NOTE_FREQS[n]) # plays an A4 note

    def play_song(self, song_path):
        y, sr = librosa.load(song_path, duration=self.duration)
        stream = self.p.open(format=pyaudio.paFloat32,
                             channels=1,
                             rate=sr,
                             output=True)
        stream.write(y.tobytes())
        stream.stop_stream()
        stream.close()

    def close(self):
        self.p.terminate()


mg = MusicGenerator(sr=44100, duration=0.5)

# Generate a melody in the key of A minor using the provided notes and durations
notes = ['A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5', 'A5']
durations = [0.5, 0.5, 0.5, 0.5, 1, 1, 0.5, 0.5]

mg.play_sequence(notes, durations)

mg.close()

