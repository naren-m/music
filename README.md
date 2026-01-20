# 🎵 Carnatic Music Note Detection System

Advanced real-time music note detection system with support for both Western 12-tone and traditional **Carnatic 22-shruti** systems.

## ✨ Features

### 🎼 **Dual Detection Systems**

- **Western Notes**: Standard 12-tone equal temperament (C-B)
- **Carnatic Shrutis**: Traditional 22-shruti system with microtonal accuracy
- **Raga Recognition**: Automatic raga context analysis based on note patterns

### 🎯 **Detection Modes**

1. **Web Interface**: Professional browser-based interface with visual shruti scale
2. **Standalone Terminal**: Enhanced command-line interface with direct microphone access
3. **Docker Container**: Containerized web service (limited audio access on macOS)

### 🎵 **Carnatic Music Features**

- **22 Shruti Detection**: Complete traditional South Indian system
- **Raga Analysis**: Supports Sankarabharanam, Kharaharapriya, Mayamalavagowla, Mohanam, Kalyani
- **Tunable Sa**: Adjustable base frequency for different tanpuras/instruments
- **Devanagari Display**: Traditional Sanskrit notation alongside Western equivalents
- **Session Recording**: Export detection history to JSON files

## 🚀 Quick Start

### Option 1: Standalone Script (Recommended for Microphone Access)

```bash
# Install dependencies
./install_standalone.sh

# Activate virtual environment
source .venv/bin/activate

# Run Carnatic detection
python3 standalone_carnatic.py
```

### Option 2: Docker Web Interface

```bash
# Launch web interface
docker-compose up -d

# Access interfaces
# Western interface: http://localhost:3001/
# Carnatic interface: http://localhost:3001/carnatic
```

**Note**: Docker containers cannot access microphone on macOS - use for interface exploration only.

## 📋 Installation Requirements

### System Dependencies (macOS)

```bash
brew install portaudio
```

### System Dependencies (Linux)

```bash
sudo apt-get install portaudio19-dev python3-dev python3-pip
```

### Python Dependencies

```bash
pip install sounddevice numpy scipy flask flask-socketio
```

## 🎼 Usage Examples

### Standalone Carnatic Detection

```bash
python3 standalone_carnatic.py
```

Features:

- 🎤 **Device Selection**: Choose your microphone
- 🎼 **Sa Tuning**: Set base frequency (100-500 Hz)
- 📊 **Live Display**: Real-time shruti detection with confidence
- 🎭 **Raga Context**: Automatic raga identification
- 💾 **Session Export**: Save analysis to JSON files

### Enhanced Terminal Detection

```bash
python3 sd.py
```

Features:

- 🌊 **Waveform Visualization**: ASCII art frequency display
- 📈 **Confidence Meters**: Visual accuracy indicators  
- 🎯 **Volume Bars**: Input level monitoring
- ⚡ **Real-time Updates**: 10fps detection refresh

### Basic Note Playing

```bash
python3 test.py     # MIDI-style note player
python3 play.py     # Frequency-based synthesis
```

## 🎵 Carnatic Music System

### Supported Shrutis (22-tone system)

```
Shadja (Sa), Suddha Ri (R₁), Chatussruti Ri (R₂), Shatsruti Ri (R₃)
Suddha Ga (G₁), Sadharana Ga (G₂), Antara Ga (G₃)
Suddha Ma (M₁), Prati Ma (M₂)
Panchama (Pa)
Suddha Dha (D₁), Chatussruti Dha (D₂), Shatsruti Dha (D₃)
Suddha Ni (N₁), Kaisika Ni (N₂), Kakali Ni (N₃)
```

### Supported Ragas

- **Sankarabharanam**: S R₂ G₃ M₁ P D₂ N₃ Ṡ (Major scale)
- **Kharaharapriya**: S R₂ G₂ M₁ P D₂ N₂ Ṡ (Natural minor)  
- **Mayamalavagowla**: S R₁ G₃ M₁ P D₁ N₃ Ṡ (15th melakarta)
- **Mohanam**: S R₂ G₃ P D₂ Ṡ (Pentatonic)
- **Kalyani**: S R₂ G₃ M₂ P D₂ N₃ Ṡ (Lydian mode)

## 🔧 Development

### Project Structure

```
├── app.py                 # Flask web server
├── carnatic_detector.py   # Advanced Carnatic detection engine
├── standalone_carnatic.py # Full-featured terminal interface
├── sd.py                  # Enhanced Western note detection
├── play.py               # Audio synthesis and playback
├── test.py               # MIDI note player
├── templates/            # Web interface templates
│   ├── index.html        # Western note interface
│   └── carnatic.html     # Carnatic shruti interface
└── docker-compose.yml    # Container orchestration
```

### Core Technologies

- **Audio Processing**: sounddevice, numpy, scipy
- **Web Framework**: Flask, SocketIO for real-time communication
- **Music Theory**: Just intonation ratios, traditional Carnatic tuning
- **Frontend**: Modern CSS3, responsive design, WebSocket integration

## 📊 Technical Details

### Detection Accuracy

- **Frequency Resolution**: ±25 cents (quarter semitone)
- **Confidence Scoring**: Magnitude + frequency accuracy weighted
- **Sample Rate**: 44.1kHz standard audio
- **Latency**: <100ms real-time processing

### Carnatic Tuning System

- **Base System**: Just intonation with frequency ratios
- **Shruti Intervals**: Traditional 22-tone mathematical ratios
- **Raga Logic**: Pattern-based context analysis
- **Cultural Accuracy**: Authentic South Indian classical system

### Carnatic to Western Notation Reference

**Sarali Varisai Swaras (Mayamalavagowla Raga, Base Sa = C4 = 261.63 Hz):**

| Swara | Shruti Name | Ratio | Frequency (Hz) | Western Note | Cents from Sa |
|-------|-------------|-------|----------------|--------------|---------------|
| **Sa** | Shadja | 1/1 | 261.63 | C4 | 0 |
| **Ri** | Suddha Rishaba (R₁) | 256/243 | 275.63 | C#4 | 90 |
| **Ga** | Antara Gandhara (G₃) | 81/64 | 331.13 | E4 | 386 |
| **Ma** | Suddha Madhyama (M₁) | 4/3 | 348.84 | F4 | 498 |
| **Pa** | Panchama | 3/2 | 392.44 | G4 | 702 |
| **Da** | Suddha Dhaivata (D₁) | 128/81 | 413.44 | G#4 | 792 |
| **Ni** | Kakali Nishada (N₃) | 15/8 | 490.56 | B4 | 1088 |
| **Ṡ** | Upper Shadja | 2/1 | 523.26 | C5 | 1200 |

**Complete 22-Shruti System (Base Sa = 261.63 Hz):**

| Index | Shruti Name | Symbol | Ratio | Frequency (Hz) | Cents |
|-------|-------------|--------|-------|----------------|-------|
| 0 | Shadja | Sa | 1/1 | 261.63 | 0 |
| 1 | Suddha Rishaba | R₁ | 256/243 | 275.63 | 90 |
| 2 | Chatussruti Rishaba | R₂ | 9/8 | 294.33 | 182 |
| 3 | Shatsruti Rishaba | R₃ | 32/27 | 310.08 | 294 |
| 4 | Suddha Gandhara | G₁ | 32/27 | 310.08 | 294 |
| 5 | Sadharana Gandhara | G₂ | 5/4 | 327.04 | 316 |
| 6 | Antara Gandhara | G₃ | 81/64 | 331.13 | 386 |
| 7 | Suddha Madhyama | M₁ | 4/3 | 348.84 | 498 |
| 8 | Prati Madhyama | M₂ | 45/32 | 367.92 | 590 |
| 9 | Panchama | Pa | 3/2 | 392.44 | 702 |
| 10 | Suddha Dhaivata | D₁ | 128/81 | 413.44 | 792 |
| 11 | Chatussruti Dhaivata | D₂ | 5/3 | 436.05 | 884 |
| 12 | Shatsruti Dhaivata | D₃ | 16/9 | 465.12 | 996 |
| 13 | Suddha Nishada | N₁ | 16/9 | 465.12 | 996 |
| 14 | Kaisika Nishada | N₂ | 9/5 | 470.93 | 1018 |
| 15 | Kakali Nishada | N₃ | 15/8 | 490.56 | 1088 |

> **Note**: Frequencies scale proportionally with the base Sa. For example, if Sa = 240 Hz (common tanpura tuning), multiply all frequencies by 240/261.63 ≈ 0.917.

## 🎯 Use Cases

- **Learning**: Students studying Carnatic music theory
- **Practice**: Musicians tuning instruments to traditional pitches  
- **Analysis**: Researchers studying microtonal music systems
- **Performance**: Real-time pitch reference during concerts
- **Teaching**: Educational tool for music theory instruction

## 📚 References

- [Music Note Frequencies](https://mixbutton.com/mixing-articles/music-note-to-frequency-chart/)
- [Scientific Pitch Notation](https://pages.mtu.edu/~suits/notefreqs.html)  
- [Carnatic Frequency Chart](https://karunyamusicals.com/wp-content/uploads/2020/03/FrequencyChartforMusic.pdf)
- [Original Code Reference](https://github.com/ianvonseggern1/note-prediction/blob/master/note_recognition.py)

## 🤝 Contributing

Contributions welcome! Areas of interest:

- Additional raga pattern recognition
- North Indian (Hindustani) music system support
- Mobile/web audio API integration
- Machine learning-based instrument recognition

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

🎵 **Happy Music Making with Traditional Precision!** 🎵
