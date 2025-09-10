# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a music experiment repository focusing on audio processing, music generation, and note recognition. The codebase contains various Python scripts for playing audio, detecting notes from microphone input, generating music sequences, and experimenting with neural networks for music generation.

## Development Environment Setup

### Dependencies Installation
```bash
# Install system dependencies (macOS)
brew install portaudio

# Create virtual environment
make venv
source .venv/bin/activate

# Install Python dependencies
make install
```

### Key Dependencies
- **pyaudio**: Real-time audio I/O
- **numpy**: Numerical operations for audio processing
- **scipy**: Signal processing functions
- **librosa**: Music and audio analysis
- **sounddevice**: Alternative audio interface
- **music21**: Music theory and MIDI processing
- **tensorflow**: Neural network framework for music generation

## Common Development Commands

### Environment Management
```bash
make venv          # Create virtual environment
make activate      # Activate virtual environment (instructions only)
make install       # Install dependencies from requirements.txt
```

### Code Quality
```bash
make format        # Format code using yapf
make test          # Run tests with coverage report
make clean         # Remove coverage files
```

### Running Scripts
```bash
python play.py     # Play musical sequences using PyAudio
python sd.py       # Real-time note detection from microphone
python keyboard.py # Basic audio recording and note detection
python test.py     # Note playing with MusicPlayer class
python gen.py      # Neural network music generation (incomplete)
```

## Code Architecture

### Core Components

#### Audio Generation (`play.py`)
- **MusicGenerator**: Main class for audio synthesis and playback
- **NOTE_FREQS**: Complete frequency mapping for musical notes (C0-B8)
- Methods: `generate_sinewave()`, `play_sound()`, `play_sequence()`, `play_song()`

#### Real-time Note Detection (`sd.py`)
- Uses **sounddevice** for continuous audio input processing
- **audio_callback()**: Real-time frequency analysis and note identification
- **find_closest_note_freq()**: Maps detected frequencies to musical notes
- FFT-based frequency domain analysis

#### Music Player (`test.py`)
- **MusicPlayer**: Tempo-based music playback system
- MIDI note number format (69 = A4 = 440Hz)
- Configurable tempo, volume, and note duration

#### Audio Recording (`keyboard.py`)
- **librosa**-based audio recording and onset detection
- Microphone input processing with PyAudio
- Basic note detection from recorded audio

#### Neural Network Generation (`gen.py`)
- **music21** for MIDI file processing
- **TensorFlow/Keras** LSTM model for note sequence generation
- Incomplete implementation for AI music composition

### Key Technical Details

#### Note Frequency System
- Standard equal temperament tuning (A4 = 440Hz)
- Complete chromatic scale from C0 (16.35Hz) to B8 (7902Hz)
- MIDI note numbers: 69 = A4, conversion formula: freq = 440 * 2^((note-69)/12)

#### Audio Processing
- Default sample rate: 44.1kHz
- Audio format: 32-bit float
- Real-time processing with configurable buffer sizes

#### Music Representation
- Note sequences as frequency/duration pairs
- MIDI-compatible note numbering system
- Support for both note names (C4, A#5) and MIDI numbers

## File Structure Context
- `*.py` files are standalone experiment scripts
- No package structure - each file is meant to be run independently
- `requirements.txt` contains all necessary Python dependencies
- `makefile` provides development workflow automation
- `*.wav` files are generated audio outputs

## Testing Strategy
The repository uses pytest for testing with coverage reporting. Tests are located in the main directory as individual test files rather than a separate tests/ directory.