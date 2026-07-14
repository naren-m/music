"""
Tests for upper Sa validation and octave equivalence.
Verifies that 523.26Hz (upper Sa) validates correctly when expected note is "Sa'".
"""

import pytest
import numpy as np
from api.audio.websocket import SWARA_TO_SHRUTI_INDEX, ExerciseSequence
from core.services.audio_engine import CarnaticAudioEngine, AudioConfig
from core.models.shruti import SHRUTI_SYSTEM


class TestUpperSaMappings:
    """Verify SWARA_TO_SHRUTI_INDEX octave equivalence mappings."""

    def test_upper_sa_maps_to_same_index_as_base_sa(self):
        """Upper Sa ('Sa'', 'S'', 'Ṡ') should map to same index as base Sa."""
        assert SWARA_TO_SHRUTI_INDEX['Sa'] == 0, "Base Sa should map to index 0"
        assert SWARA_TO_SHRUTI_INDEX['S'] == 0, "S should map to index 0"

        # Upper Sa variants
        assert SWARA_TO_SHRUTI_INDEX['Sa\''] == 0, "Sa' should map to index 0"
        assert SWARA_TO_SHRUTI_INDEX['S\''] == 0, "S' should map to index 0"
        assert SWARA_TO_SHRUTI_INDEX['Ṡ'] == 0, "Ṡ should map to index 0"

    def test_upper_sa_is_not_komal_rishaba(self):
        """Verify upper Sa is NOT index 16 (Komal Rishaba)."""
        # This was the bug: 'Sa'' was mapping to index 16 which is Komal Rishaba
        # After fix, it should map to 0 (Sa)
        assert SWARA_TO_SHRUTI_INDEX.get('Sa\'') != 16, \
            "Upper Sa should NOT map to index 16 (Komal Rishaba)"

        # Confirm index 16 is Komal Rishaba if it exists
        if len(SHRUTI_SYSTEM) > 16:
            assert "Komal Rishaba" in SHRUTI_SYSTEM[16].name or \
                   "Rishaba" in SHRUTI_SYSTEM[16].name, \
                   "Index 16 should be a Rishaba variant"


class TestUpperSaDetectionAndValidation:
    """Test full roundtrip: detect 523.26Hz and validate against 'Sa''."""

    def setup_method(self):
        """Set up engine and test fixtures."""
        self.config = AudioConfig(sample_rate=44100, buffer_size=2048)
        self.engine = CarnaticAudioEngine(self.config)
        self.base_sa = self.engine.base_sa  # 261.63 Hz
        self.sample_rate = self.config.sample_rate
        self.duration = 0.5

    def generate_sine_tone(self, frequency):
        """Generate a pure sine tone at given frequency."""
        num_samples = int(self.duration * self.sample_rate)
        t = np.arange(num_samples) / self.sample_rate
        tone = 0.5 * np.sin(2 * np.pi * frequency * t)
        return tone.astype(np.float32)

    def test_upper_sa_frequency_detection(self):
        """Verify 523.26Hz is detected as Shadja (after octave folding)."""
        upper_sa_freq = self.base_sa * 2  # 523.26 Hz
        tone = self.generate_sine_tone(upper_sa_freq)

        result = self.engine.detect_shruti(tone)

        assert result is not None, "Should detect upper Sa frequency"
        assert result.note_name == 'Shadja', \
            f"523.26Hz should normalize to Shadja, got {result.note_name}"
        assert abs(result.cent_deviation) < 2, \
            f"Deviation should be < 2¢, got {result.cent_deviation}"
        assert result.confidence > 0.95, \
            f"Confidence should be > 0.95, got {result.confidence}"

    def test_upper_sa_validation_with_exercise_sequence(self):
        """Full roundtrip: detect 523.26Hz and validate it against 'Sa''."""
        upper_sa_freq = self.base_sa * 2  # 523.26 Hz

        # Create exercise sequence with upper Sa at the end
        exercise = ExerciseSequence(pattern_sequence=['Sa', 'Sa\''], tolerance_cents=50.0)

        # Simulate practice: play first note (base Sa)
        tone_sa = self.generate_sine_tone(self.base_sa)
        result_sa = self.engine.detect_shruti(tone_sa)
        assert result_sa is not None

        # Validate first note
        validation_sa = exercise.validate_note(result_sa.note_name, result_sa.confidence)
        assert validation_sa['is_correct'], \
            f"Base Sa should validate correctly. Got: {validation_sa}"
        assert exercise.current_position == 1, "Should advance to next note"

        # Play upper Sa
        tone_upper = self.generate_sine_tone(upper_sa_freq)
        result_upper = self.engine.detect_shruti(tone_upper)
        assert result_upper is not None, "Should detect upper Sa"

        # Validate upper Sa (THIS IS THE KEY TEST)
        accuracy_score = min(1.0, result_upper.confidence) \
            if abs(result_upper.cent_deviation) < 50 else 0.5
        validation_upper = exercise.validate_note(result_upper.note_name, accuracy_score)

        # CRITICAL: After fix, this should now PASS
        assert validation_upper['is_correct'], \
            f"Upper Sa should validate correctly against 'Sa''. " \
            f"Got note_matches={validation_upper['note_matches']}, " \
            f"expected_note={validation_upper['expected_note']}, " \
            f"detected_note={validation_upper['detected_note']}"

        assert validation_upper['completed'], "Exercise should be marked completed"

    def test_upper_sa_name_matching_logic(self):
        """Verify the validation name-matching logic for upper Sa."""
        expected_note = 'Sa\''
        detected_shruti_name = 'Shadja'

        # This is the exact logic from ExerciseSequence.validate_note()
        expected_index = SWARA_TO_SHRUTI_INDEX.get(expected_note)
        detected_index = SWARA_TO_SHRUTI_INDEX.get(detected_shruti_name)

        note_matches = (detected_index is not None and
                       expected_index is not None and
                       detected_index == expected_index)

        assert note_matches, \
            f"Upper Sa ('Sa\'') should match Shadja detection. " \
            f"expected_index={expected_index}, detected_index={detected_index}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
