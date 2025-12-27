# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Carnatic Music Learning Platform** - A full-stack application for teaching Carnatic music fundamentals through real-time note recognition and structured practice exercises.

**Core Mission**: Enable students to practice playing correct notes through lessons with real-time feedback on their pitch accuracy.

### Key Features
- **22-Shruti System**: Authentic Carnatic microtonal pitch detection (not Western 12-tone)
- **Sarali/Janta/Alankaram Exercises**: Traditional progressive exercise patterns
- **Real-time Feedback**: WebSocket-based live pitch detection with cent deviation display
- **Gamification**: Streaks, achievements, and progress tracking

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React/TS)                   │
│  SaraliInterface → AudioContext → WebSocket → Backend   │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                   Backend (Flask/Python)                 │
│  api/audio/websocket.py → core/services/audio_engine.py │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                      Core Services                       │
│  Shruti Model → Pitch Detection → Exercise Validation   │
└─────────────────────────────────────────────────────────┘
```

## Development Environment Setup

### Backend Setup
```bash
# Install system dependencies (macOS)
brew install portaudio

# Create virtual environment
make venv
source .venv/bin/activate

# Install Python dependencies
make install

# Run Flask backend
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Key Dependencies
**Backend:**
- Flask + Flask-SocketIO (real-time WebSocket)
- numpy/scipy (audio signal processing)
- librosa (music analysis)

**Frontend:**
- React + TypeScript
- Framer Motion (animations)
- Web Audio API (browser audio capture)

## Code Architecture

### Core Components

#### Pitch Detection (`core/services/audio_engine.py`)
- **Autocorrelation algorithm** for pitch detection (more accurate than FFT for music)
- Maps detected frequencies to 22 Carnatic shrutis
- Returns confidence score and cent deviation

#### Shruti System (`core/models/shruti.py`)
- Defines all 22 shrutis with just intonation frequency ratios
- `find_closest_shruti()` - Maps any frequency to nearest shruti
- Base frequency: Sa = 240Hz (configurable)

#### Exercise Patterns (`modules/exercises/`)
- **Sarali Varisai** (`sarali/patterns.py`): 12 levels of ascending/descending patterns
- **Janta Varisai** (`janta/`): Double-note patterns
- **Alankaram** (`alankaram/`): Complex melodic ornaments

#### Practice Interface (`frontend/src/components/exercises/sarali/SaraliInterface.tsx`)
- Three modes: Listen, Practice, Assessment
- Real-time shruti detection display
- Visual feedback on pitch accuracy (green/yellow/red)

### API Endpoints (`api/`)

| Module | Purpose |
|--------|---------|
| `audio/` | WebSocket for real-time pitch streaming |
| `learning/` | Lesson progress and exercise data |
| `auth/` | User authentication |
| `gamification/` | Achievements, streaks, leaderboards |
| `analytics/` | Practice session analytics |
| `raga/` | Raga definitions and patterns |
| `tala/` | Rhythm/beat patterns |

## Common Development Commands

```bash
# Backend
make venv          # Create virtual environment
make install       # Install dependencies
make format        # Format code using yapf
make test          # Run tests with coverage

# Frontend
cd frontend
npm run dev        # Start dev server
npm run build      # Production build
npm run lint       # ESLint check
```

## Key Technical Details

### 22-Shruti System (vs Western 12-tone)
Carnatic music uses 22 microtones per octave with just intonation ratios:
- Sa (1/1), Ri1 (256/243), Ri2 (16/15), Ri3 (10/9)...
- This provides more nuanced pitch detection than Western equal temperament

### Audio Processing Pipeline
1. Browser captures audio via Web Audio API
2. Audio chunks sent via WebSocket to backend
3. `audio_engine.py` performs autocorrelation pitch detection
4. Detected frequency mapped to closest shruti
5. Result (shruti, cents deviation, confidence) sent back to frontend

### Exercise Validation
- Each exercise has expected shruti sequence
- Real-time comparison of sung/played notes vs expected
- Tolerance: typically ±25 cents for "correct" assessment

## File Structure

```
music/
├── app.py                 # Flask entry point
├── api/                   # REST + WebSocket endpoints
│   ├── audio/            # Real-time audio WebSocket
│   ├── learning/         # Lesson/exercise APIs
│   └── ...
├── core/
│   ├── models/shruti.py  # 22-shruti definitions
│   ├── services/audio_engine.py  # Pitch detection
│   └── ml/adaptive_engine.py     # Adaptive difficulty
├── modules/exercises/     # Exercise pattern definitions
│   ├── sarali/
│   ├── janta/
│   └── alankaram/
├── frontend/             # React/TypeScript app
│   └── src/components/exercises/  # Practice UIs
├── tests/                # pytest tests
└── k8s/                  # Kubernetes deployment
```

## Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_carnatic_simple.py -v

# E2E tests (requires Playwright)
pytest tests/e2e/ -v
```

## Deployment

The application is containerized and deployed to a homelab Kubernetes cluster. See `k8s/` for manifests and `jenkins/Jenkinsfile` for CI/CD pipeline.
