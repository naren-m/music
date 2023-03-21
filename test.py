import pyaudio
import numpy as np

class MusicPlayer:
    def __init__(self, tempo=10, volume=0.1):
        self.tempo = tempo
        self.volume = volume
        self.sample_rate = 44100
        self.ticks_per_beat = 4
        self.note_duration = 60 / self.tempo / self.ticks_per_beat
        self.p = pyaudio.PyAudio()
        self.stream = None

    def play_notes(self, notes):
        if self.stream and self.stream.is_active():
            self.stream.stop_stream()
            self.stream.close()

        # Calculate total duration of the music
        total_duration = sum(note[1] for note in notes) * self.note_duration

        # Generate samples for each note
        samples = []
        for note in notes:
            frequency = 440 * 2 ** ((note[0] - 69) / 12)
            duration = note[1] * self.note_duration
            samples += self._generate_samples(frequency, duration)

        # Convert the list of samples to a numpy array
        samples = np.array(samples)

        # Scale the samples to the desired volume
        samples *= self.volume

        # Open a new audio stream and play the samples
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            output=True
        )
        self.stream.write(samples.tobytes())

    def _generate_samples(self, frequency, duration):
        # Generate samples for a sine wave with the given frequency and duration
        duration = 1
        samples = self.sample_rate * duration
        t = np.linspace(0, duration, samples, False)
        note = np.sin(frequency * t * 2 * np.pi)
        return note.astype(np.float32)

    def close(self):
        if self.stream and self.stream.is_active():
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

notes = [(69, 1), (71, 4), (73, 4), (74, 4), (76, 4), (78, 4), (80, 4), (81, 4)]

player = MusicPlayer(tempo=10, volume=0.1)
player.play_notes(notes)
import time
# Wait for the music to finish playing
time.sleep(len(notes) * player.note_duration)

# Close the audio stream
player.close()
