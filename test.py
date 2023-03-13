from play import MusicGenerator




mg = MusicGenerator()

# Generate a melody in the key of A minor using the provided notes and durations
notes = ['A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5', 'A5']
durations = [0.5, 0.5, 0.5, 0.5, 1, 1, 0.5, 0.5]

for n in notes:
    mg.play_sequence(notes, durations)

mg.close()

