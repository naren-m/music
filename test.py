import numpy as np
from scipy.io.wavfile import write

samplerate = 44100  #Frequecy in Hz


def get_wave(freq, duration=0.5):
    '''
    Function takes the "frequecy" and "time_duration" for a wave
    as the input and returns a "numpy array" of values at all points
    in time
    '''

    amplitude = 4096
    t = np.linspace(0, duration, int(samplerate * duration))
    wave = amplitude * np.sin(2 * np.pi * freq * t)

    return wave


# To get a 1 second long wave of frequency 440Hz
a_wave = get_wave(440, 1)

#wave features
print(len(a_wave))  # 44100
print(np.max(a_wave))  # 4096
print(np.min(a_wave))  # -4096

# import matplotlib.pyplot as plt

# plt.plot(a_wave[0:int(44100/440)])
# plt.xlabel('time')
# plt.ylabel('Amplitude')
# plt.show()

# note_freq = base_freq * 2^(n/12)


def get_piano_notes():
    '''
    Returns a dict object for all the piano
    note's frequencies
    '''
    # White keys are in Uppercase and black keys (sharps) are in lowercase
    octave = ['C', 'c', 'D', 'd', 'E', 'F', 'f', 'G', 'g', 'A', 'a', 'B']
    # octave = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    base_freq = 261.63  #Frequency of Note C4

    note_freqs = {
        octave[i]: base_freq * pow(2, (i / 12))
        for i in range(len(octave))
    }
    note_freqs[''] = 0.0  # silent note

    return note_freqs


def get_piano_notes():
    # White keys are in Uppercase and black keys (sharps) are in lowercase
    octave = ['C', 'c', 'D', 'd', 'E', 'F', 'f', 'G', 'g', 'A', 'a', 'B']
    base_freq = 440  #Frequency of Note A4
    keys = np.array([x + str(y) for y in range(0, 9) for x in octave])
    # Trim to standard 88 keys
    start = np.where(keys == 'A0')[0][0]
    end = np.where(keys == 'C8')[0][0]
    keys = keys[start:end + 1]

    note_freqs = dict(
        zip(keys,
            [2**((n + 1 - 49) / 12) * base_freq for n in range(len(keys))]))
    note_freqs[''] = 0.0  # stop
    return note_freqs


def get_sine_wave(frequency, duration, sample_rate=44100, amplitude=4096):
    t = np.linspace(0, duration, int(sample_rate * duration))  # Time axis
    wave = amplitude * np.sin(2 * np.pi * frequency * t)
    return wave


def get_song_data(music_notes):
    '''
    Function to concatenate all the waves (notes)
    '''
    frequency = 1
    note_freqs = get_piano_notes()  # Function that we made earlier
    sine_wave = get_sine_wave(frequency, duration=2, amplitude=2048)
    song = [get_wave(note_freqs[note]) for note in music_notes.split('-')]
    song = np.concatenate(song)
    return song


music_notes = 'C-C-G-G-A-A-G--F-F-E-E-D-D-C--G-G-F-F-E-E-D--G-G-F-F-E-E-D--C-C-G-G-A-A-G--F-F-E-E-D-D-C'
data = get_song_data(music_notes)

# data = data * (16300/np.max(data)) # Adjusting the Amplitude (Optional)

# write('twinkle-twinkle.wav', samplerate, data.astype(np.int16))

# Pure sine wave
# sine_wave = get_sine_wave(frequency, duration=2, amplitude=2048)
# wavfile.write('pure_c.wav', rate=44100, data=sine_wave.astype(np.int16))
