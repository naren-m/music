import pyaudio
import numpy as np
import librosa

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


mg = MusicGenerator(sr=22050, duration=1)
mg.play_sound(440) # plays an A4 note

mg.close()