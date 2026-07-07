"""
Audio Round-Trip Test Harness
=============================
Generate shruti tones → feed through detection pipeline → verify identification.

This is the primary regression gate: any change to the audio engine or shruti
model that breaks generate→detect correctness will fail these tests.

Usage:
    pytest tests/test_audio_roundtrip.py -v
    pytest -m roundtrip -v
"""

import numpy as np
import pytest
from core.services.audio_engine import CarnaticAudioEngine, AudioConfig, PitchDetectionResult
from core.models.shruti import (
    ShrutiSystem,
    Shruti,
    SHRUTI_SYSTEM,
    MELAKARTA_RAGAS,
    JANYA_RAGAS,
    find_closest_shruti,
    calculate_shruti_frequency,
    analyze_pitch_deviation,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SAMPLE_RATE = 44100

# The 16 "standard" shrutis (indices 0-15) – excludes the 6 pramana/microtonal
# variants (indices 16-21) which share cent values with neighbours and are
# harder to distinguish in a simple sine-wave round-trip.
STANDARD_SHRUTI_NAMES = [s.name for s in SHRUTI_SYSTEM[:16]]

# A subset of base Sa frequencies spanning the supported range.
BASE_FREQUENCIES = [200, 240, 261.63, 300, 350]

# Shrutis whose frequency ratios are well-separated (>40 cents from any
# neighbour) and therefore reliably round-trip even with autocorrelation
# detection.  We use these for the exhaustive parametrised matrix.
# Shadja(0¢), Chatussruti Ri(182¢), Antara Ga(386¢), Suddha Ma(498¢),
# Panchama(702¢), Chatussruti Dha(884¢), Kakali Ni(1088¢)
WELL_SEPARATED_SHRUTI_NAMES = [
    "Shadja",
    "Chatussruti Rishaba",
    "Antara Gandhara",
    "Suddha Madhyama",
    "Panchama",
    "Chatussruti Dhaivata",
    "Kakali Nishada",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def generate_sine(frequency: float, duration: float = 0.1,
                  sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Generate a pure sine-wave tone at *frequency* Hz."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * frequency * t).astype(np.float32)


def generate_sine_with_noise(frequency: float, snr_db: float,
                             duration: float = 0.1,
                             sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Generate a sine wave with additive white Gaussian noise at *snr_db*."""
    signal = generate_sine(frequency, duration, sample_rate)
    signal_power = np.mean(signal ** 2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = np.sqrt(noise_power) * np.random.default_rng(42).standard_normal(len(signal))
    return (signal + noise).astype(np.float32)


def make_engine(base_sa: float = 261.63) -> CarnaticAudioEngine:
    """Create an engine with generous detection tolerances for test tones."""
    cfg = AudioConfig(
        sample_rate=SAMPLE_RATE,
        buffer_size=4096,           # longer buffer for better freq resolution
        confidence_threshold=0.15,  # sine waves are very clean
        silence_threshold=0.005,
        max_deviation_cents=60.0,   # allow some wiggle room
        autocorr_peak_threshold=0.08,
    )
    engine = CarnaticAudioEngine(config=cfg)
    engine.set_base_frequency(base_sa)
    return engine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def engine():
    """Default engine at Sa = 261.63 Hz (C4)."""
    return make_engine(261.63)


@pytest.fixture
def shruti_system():
    return ShrutiSystem()


# =========================================================================
# 1. Core round-trip: generate each shruti → detect → verify name matches
# =========================================================================
@pytest.mark.roundtrip
@pytest.mark.audio
class TestShrutiRoundTrip:
    """For each well-separated shruti × multiple Sa values:
    generate a sine at the shruti frequency, run detection, assert match."""

    @pytest.mark.parametrize("shruti_name", WELL_SEPARATED_SHRUTI_NAMES)
    @pytest.mark.parametrize("base_sa", BASE_FREQUENCIES)
    def test_generate_detect_matches(self, shruti_name, base_sa):
        """Round-trip: shruti_name → frequency → sine → detect → same name."""
        engine = make_engine(base_sa)
        shruti = engine.shruti_system.get_shruti(shruti_name)
        assert shruti is not None, f"Shruti '{shruti_name}' not found in system"

        freq = shruti.calculate_frequency(base_sa)
        audio = generate_sine(freq, duration=0.1)

        result = engine.detect_shruti(audio)
        assert result is not None, (
            f"Detection returned None for {shruti_name} @ {freq:.2f} Hz "
            f"(base_sa={base_sa})"
        )
        assert result.note_name == shruti_name, (
            f"Expected '{shruti_name}' but got '{result.note_name}' "
            f"(freq={freq:.2f}, base_sa={base_sa}, "
            f"detected_freq={result.detected_frequency:.2f})"
        )

    @pytest.mark.parametrize("shruti_name", WELL_SEPARATED_SHRUTI_NAMES)
    def test_confidence_above_threshold(self, shruti_name):
        """Clean sine wave at exact shruti frequency should yield high confidence."""
        engine = make_engine(261.63)
        shruti = engine.shruti_system.get_shruti(shruti_name)
        freq = shruti.calculate_frequency(261.63)
        audio = generate_sine(freq, duration=0.1)

        result = engine.detect_shruti(audio)
        assert result is not None
        assert result.confidence >= 0.15, (
            f"Confidence {result.confidence:.3f} too low for clean sine"
        )

    @pytest.mark.parametrize("shruti_name", WELL_SEPARATED_SHRUTI_NAMES)
    def test_cent_deviation_within_tolerance(self, shruti_name):
        """Detected frequency should be within 50 cents of the target."""
        engine = make_engine(261.63)
        shruti = engine.shruti_system.get_shruti(shruti_name)
        freq = shruti.calculate_frequency(261.63)
        audio = generate_sine(freq, duration=0.1)

        result = engine.detect_shruti(audio)
        assert result is not None
        assert abs(result.cent_deviation) <= 50, (
            f"Deviation {result.cent_deviation:.1f}¢ exceeds 50¢ for {shruti_name}"
        )


# =========================================================================
# 2. Base frequency range: detection works at edge-case Sa values
# =========================================================================
@pytest.mark.roundtrip
@pytest.mark.audio
class TestBaseFrequencyRange:
    """Verify detection at extreme base Sa frequencies and mid-session changes."""

    @pytest.mark.parametrize("base_sa", [100, 150, 200, 261.63, 350, 440, 500])
    def test_sa_detection_at_various_bases(self, base_sa):
        """Shadja (Sa) must be detectable across the full supported range."""
        engine = make_engine(base_sa)
        audio = generate_sine(base_sa, duration=0.1)
        result = engine.detect_shruti(audio)

        assert result is not None, f"Sa not detected at base_sa={base_sa}"
        assert result.note_name == "Shadja", (
            f"Expected 'Shadja' but got '{result.note_name}' at base_sa={base_sa}"
        )

    @pytest.mark.parametrize("base_sa", [100, 150, 200, 261.63, 350, 440, 500])
    def test_panchama_detection_at_various_bases(self, base_sa):
        """Panchama (Pa, ratio 3/2) must be detectable across the range."""
        engine = make_engine(base_sa)
        pa_freq = base_sa * 1.5  # ratio 3/2
        audio = generate_sine(pa_freq, duration=0.1)
        result = engine.detect_shruti(audio)

        assert result is not None, f"Pa not detected at base_sa={base_sa}"
        assert result.note_name == "Panchama", (
            f"Expected 'Panchama' but got '{result.note_name}' at base_sa={base_sa}"
        )

    def test_mid_session_base_change(self):
        """Changing base_sa mid-session recalibrates detection correctly."""
        engine = make_engine(261.63)

        # Detect Sa at original base
        audio_sa = generate_sine(261.63, duration=0.1)
        r1 = engine.detect_shruti(audio_sa)
        assert r1 is not None and r1.note_name == "Shadja"

        # Change base to 300 Hz
        engine.set_base_frequency(300.0)

        # The old frequency 261.63 is no longer Sa
        audio_old = generate_sine(261.63, duration=0.1)
        r2 = engine.detect_shruti(audio_old)
        # It should NOT match Shadja any more (or might be None / different shruti)
        if r2 is not None:
            assert r2.note_name != "Shadja" or abs(r2.cent_deviation) > 30, (
                "Old Sa frequency should not match Shadja after base change"
            )

        # New Sa at 300 Hz should now be detected as Shadja
        audio_new_sa = generate_sine(300.0, duration=0.1)
        r3 = engine.detect_shruti(audio_new_sa)
        assert r3 is not None and r3.note_name == "Shadja"

    def test_invalid_base_frequency_ignored(self):
        """Setting an out-of-range base frequency should be silently ignored."""
        engine = make_engine(261.63)
        engine.set_base_frequency(30)    # below minimum 50 Hz
        assert engine.base_sa == 261.63  # unchanged

        engine.set_base_frequency(1500)  # above maximum 1000 Hz
        assert engine.base_sa == 261.63  # unchanged


# =========================================================================
# 3. Tone quality: validate generated audio properties
# =========================================================================
@pytest.mark.roundtrip
@pytest.mark.audio
class TestToneQuality:
    """Verify that synthesised test tones have correct spectral properties."""

    @pytest.mark.parametrize("freq", [261.63, 392.44, 440.0])
    def test_sine_sample_count(self, freq):
        """Generated tone has the correct number of samples."""
        duration = 0.5
        audio = generate_sine(freq, duration=duration)
        expected = int(SAMPLE_RATE * duration)
        assert len(audio) == expected

    @pytest.mark.parametrize("freq", [261.63, 392.44, 440.0])
    def test_sine_amplitude_bounds(self, freq):
        """Amplitude stays within [-1, 1]."""
        audio = generate_sine(freq, duration=0.5)
        assert np.max(np.abs(audio)) <= 1.0 + 1e-6

    @pytest.mark.parametrize("freq", [200, 261.63, 440.0, 600.0])
    def test_fft_dominant_frequency(self, freq):
        """FFT of the generated tone peaks at the expected frequency."""
        duration = 0.5  # long enough for good resolution
        audio = generate_sine(freq, duration=duration)
        n = len(audio)
        spectrum = np.abs(np.fft.rfft(audio))
        freqs = np.fft.rfftfreq(n, d=1.0 / SAMPLE_RATE)
        dominant_freq = freqs[np.argmax(spectrum)]
        assert abs(dominant_freq - freq) < 5.0, (
            f"FFT peak at {dominant_freq:.1f} Hz, expected {freq:.1f} Hz"
        )

    def test_octave_up_doubles_frequency(self):
        """A tone one octave above Sa should still resolve to Shadja."""
        base_sa = 261.63
        engine = make_engine(base_sa)
        upper_sa = base_sa * 2  # octave up
        audio = generate_sine(upper_sa, duration=0.1)
        result = engine.detect_shruti(audio)

        assert result is not None, "Upper octave Sa not detected"
        # Octave normalisation should map it back to Shadja
        assert result.note_name == "Shadja", (
            f"Expected 'Shadja' for upper octave but got '{result.note_name}'"
        )

    def test_octave_down_halves_frequency(self):
        """A tone one octave below Sa should still resolve to Shadja."""
        base_sa = 261.63
        engine = make_engine(base_sa)
        lower_sa = base_sa / 2  # octave down
        audio = generate_sine(lower_sa, duration=0.1)
        result = engine.detect_shruti(audio)

        assert result is not None, "Lower octave Sa not detected"
        assert result.note_name == "Shadja", (
            f"Expected 'Shadja' for lower octave but got '{result.note_name}'"
        )


# =========================================================================
# 4. Detection accuracy / robustness
# =========================================================================
@pytest.mark.roundtrip
@pytest.mark.audio
class TestDetectionAccuracy:
    """Detection robustness with noise, detuning, and silence."""

    def test_silence_returns_none(self, engine):
        """Silent input should return None (below silence threshold)."""
        silence = np.zeros(4096, dtype=np.float32)
        result = engine.detect_shruti(silence)
        assert result is None, "Silent audio should not produce a detection"

    def test_noise_returns_none(self, engine):
        """Pure white noise should be rejected (flat spectrum)."""
        rng = np.random.default_rng(123)
        noise = rng.standard_normal(4096).astype(np.float32) * 0.1
        result = engine.detect_shruti(noise)
        # Should be None due to spectral flatness rejection
        assert result is None, "Pure noise should be rejected"

    @pytest.mark.parametrize("snr_db", [30, 20])
    def test_detection_with_moderate_noise(self, snr_db):
        """Sa should still be detected with moderate noise levels.

        Uses a relaxed spectral-flatness threshold so we're testing the
        autocorrelation detector's noise-robustness, not the noise-gate.
        """
        base_sa = 261.63
        cfg = AudioConfig(
            sample_rate=SAMPLE_RATE,
            buffer_size=4096,
            confidence_threshold=0.10,
            silence_threshold=0.005,
            max_deviation_cents=60.0,
            autocorr_peak_threshold=0.08,
            spectral_flatness_threshold=0.7,  # relax for noisy input
        )
        noisy_engine = CarnaticAudioEngine(config=cfg)
        noisy_engine.set_base_frequency(base_sa)

        audio = generate_sine_with_noise(base_sa, snr_db=snr_db, duration=0.1)
        result = noisy_engine.detect_shruti(audio)

        assert result is not None, (
            f"Sa not detected at SNR={snr_db}dB"
        )
        assert result.note_name == "Shadja", (
            f"Expected 'Shadja' at SNR={snr_db}dB but got '{result.note_name}'"
        )

    @pytest.mark.parametrize("cents_offset", [5, 10, 20])
    def test_detection_with_slight_detuning(self, cents_offset):
        """Slightly detuned Sa should still resolve to Shadja."""
        base_sa = 261.63
        engine = make_engine(base_sa)
        # Shift frequency by `cents_offset` cents sharp
        detuned_freq = base_sa * (2 ** (cents_offset / 1200))
        audio = generate_sine(detuned_freq, duration=0.1)
        result = engine.detect_shruti(audio)

        assert result is not None, (
            f"Sa detuned +{cents_offset}¢ not detected"
        )
        assert result.note_name == "Shadja", (
            f"Expected 'Shadja' at +{cents_offset}¢ but got '{result.note_name}'"
        )

    def test_find_closest_shruti_exact_match(self):
        """find_closest_shruti returns zero deviation for exact frequency."""
        base_sa = 261.63
        match = find_closest_shruti(base_sa, base_sa)
        assert match["shruti_name"] == "Shadja"
        assert abs(match["deviation_cents"]) < 1.0

    def test_analyze_pitch_deviation_perfect(self):
        """analyze_pitch_deviation returns near-perfect score for exact pitch."""
        base_sa = 261.63
        result = analyze_pitch_deviation(base_sa, base_sa, target_shruti_index=0)
        assert result["accuracy_score"] > 0.95
        assert result["direction"] == "perfect" or abs(result["deviation_cents"]) < 1
        assert result["target_shruti"] == "Shadja"

    @pytest.mark.parametrize("direction,offset_cents", [("sharp", 30), ("flat", -30)])
    def test_analyze_pitch_deviation_direction(self, direction, offset_cents):
        """Deviation direction is correctly reported as sharp or flat."""
        base_sa = 261.63
        detuned = base_sa * (2 ** (offset_cents / 1200))
        result = analyze_pitch_deviation(detuned, base_sa, target_shruti_index=0)
        assert result["direction"] == direction


# =========================================================================
# 5. Raga phrase end-to-end
# =========================================================================
@pytest.mark.roundtrip
@pytest.mark.audio
class TestRagaPhraseRoundTrip:
    """Generate full raga phrases, detect each note, verify the sequence."""

    # Map abbreviations used in raga definitions → full shruti names
    ABBREV_TO_NAME = {
        "Sa": "Shadja",
        "R₁": "Suddha Rishaba",
        "R₂": "Chatussruti Rishaba",
        "R₃": "Shatsruti Rishaba",
        "G₁": "Suddha Gandhara",
        "G₂": "Sadharana Gandhara",
        "G₃": "Antara Gandhara",
        "M₁": "Suddha Madhyama",
        "M₂": "Prati Madhyama",
        "Pa": "Panchama",
        "D₁": "Suddha Dhaivata",
        "D₂": "Chatussruti Dhaivata",
        "D₃": "Shatsruti Dhaivata",
        "N₁": "Suddha Nishada",
        "N₂": "Kaisika Nishada",
        "N₃": "Kakali Nishada",
    }

    # Raga phrases to test – use only well-separated swaras for reliability
    RAGA_PHRASES = {
        # Sankarabharanam arohanam (melakarta 29)
        "Sankarabharanam": ["Sa", "R₂", "G₃", "M₁", "Pa", "D₂", "N₃"],
        # Mohanam arohanam (pentatonic janya)
        "Mohanam": ["Sa", "R₂", "G₃", "Pa", "D₂"],
        # Kalyani arohanam (melakarta 65)
        "Kalyani": ["Sa", "R₂", "G₃", "M₂", "Pa", "D₂", "N₃"],
    }

    @pytest.mark.parametrize("raga_name", ["Sankarabharanam", "Mohanam", "Kalyani"])
    def test_ascending_phrase_detection(self, raga_name):
        """Generate each note in the arohanam, detect it, verify the sequence."""
        base_sa = 261.63
        engine = make_engine(base_sa)
        phrase = self.RAGA_PHRASES[raga_name]

        detected_sequence = []
        for abbrev in phrase:
            full_name = self.ABBREV_TO_NAME[abbrev]
            shruti = engine.shruti_system.get_shruti(full_name)
            assert shruti is not None, f"Shruti '{full_name}' not in system"

            freq = shruti.calculate_frequency(base_sa)
            audio = generate_sine(freq, duration=0.1)
            result = engine.detect_shruti(audio)

            assert result is not None, (
                f"Failed to detect {full_name} ({abbrev}) in {raga_name} "
                f"@ {freq:.2f} Hz"
            )
            detected_sequence.append(result.note_name)

        expected_sequence = [self.ABBREV_TO_NAME[a] for a in phrase]
        assert detected_sequence == expected_sequence, (
            f"Raga {raga_name} phrase mismatch:\n"
            f"  expected: {expected_sequence}\n"
            f"  detected: {detected_sequence}"
        )

    @pytest.mark.parametrize("raga_name", ["Sankarabharanam", "Mohanam", "Kalyani"])
    def test_descending_phrase_detection(self, raga_name):
        """Detect the avarohanam (descending) — reverse the arohanam."""
        base_sa = 261.63
        engine = make_engine(base_sa)
        phrase = list(reversed(self.RAGA_PHRASES[raga_name]))

        detected_sequence = []
        for abbrev in phrase:
            full_name = self.ABBREV_TO_NAME[abbrev]
            shruti = engine.shruti_system.get_shruti(full_name)
            freq = shruti.calculate_frequency(base_sa)
            audio = generate_sine(freq, duration=0.1)
            result = engine.detect_shruti(audio)

            assert result is not None, (
                f"Failed to detect {full_name} in descending {raga_name}"
            )
            detected_sequence.append(result.note_name)

        expected = [self.ABBREV_TO_NAME[a] for a in phrase]
        assert detected_sequence == expected


# =========================================================================
# 6. Shruti model sanity checks (non-audio)
# =========================================================================
@pytest.mark.roundtrip
class TestShrutiModelSanity:
    """Quick model-level checks that don't need audio processing."""

    def test_22_shrutis_exist(self):
        assert len(SHRUTI_SYSTEM) == 22

    def test_shruti_names_unique(self):
        names = [s.name for s in SHRUTI_SYSTEM]
        assert len(names) == len(set(names)), "Duplicate shruti names found"

    def test_frequency_ratios_positive(self):
        for s in SHRUTI_SYSTEM:
            assert s.frequency_ratio > 0, f"{s.name} has non-positive ratio"

    def test_shadja_ratio_is_one(self):
        assert SHRUTI_SYSTEM[0].name == "Shadja"
        assert SHRUTI_SYSTEM[0].frequency_ratio == 1.0

    def test_panchama_ratio_is_three_halves(self):
        pa = [s for s in SHRUTI_SYSTEM if s.name == "Panchama"]
        assert len(pa) == 1
        assert abs(pa[0].frequency_ratio - 1.5) < 1e-9

    @pytest.mark.parametrize("base_sa", [240, 261.63, 300, 440])
    def test_calculate_shruti_frequency_by_index(self, base_sa):
        """calculate_shruti_frequency(0, base) should equal base_sa."""
        freq = calculate_shruti_frequency(0, base_sa)
        assert abs(freq - base_sa) < 1e-6

    def test_calculate_shruti_frequency_out_of_range(self):
        with pytest.raises(IndexError):
            calculate_shruti_frequency(100, 261.63)

    def test_melakarta_ragas_defined(self):
        assert len(MELAKARTA_RAGAS) >= 3, "At least 3 melakarta ragas expected"

    def test_janya_ragas_defined(self):
        assert len(JANYA_RAGAS) >= 1, "At least 1 janya raga expected"
