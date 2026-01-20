
from core.models.shruti import Shruti

def test_note_calculation():
    # Test cases: Frequency -> Expected Note
    test_cases = [
        (261.63, "C4"),   # Middle C
        (440.0, "A4"),    # Concert A
        (466.16, "A#4"),
        (523.25, "C5"),
        (0, ""),
        (-100, "")
    ]
    
    print("Testing Frequency to Note Calculation:")
    print("-" * 40)
    
    all_passed = True
    for freq, expected in test_cases:
        result = Shruti._freq_to_note_name(freq)
        status = "✅" if result == expected else f"❌ (Expected {expected})"
        print(f"Freq: {freq} Hz -> {result:<4} {status}")
        if result != expected:
            all_passed = False
            
    # Test Shruti instance method
    print("\nTesting Shruti Instance Method (Base Sa = C4/261.63Hz):")
    print("-" * 40)
    s = Shruti("Test", "Sa", 0, 1.0, []) # Sa
    note_name = s.get_western_note_name(261.63)
    print(f"Shruti Sa (Ratio 1.0) -> {note_name} {'✅' if note_name == 'C4' else '❌'}")
    
    s_pa = Shruti("Pa", "Pa", 702, 1.5, []) # Pa (Perfect Fifth) ~ G4
    note_name_pa = s_pa.get_western_note_name(261.63)
    # C4 * 1.5 = ~392.44 Hz -> G4
    print(f"Shruti Pa (Ratio 1.5) -> {note_name_pa} {'✅' if note_name_pa == 'G4' else '❌'}")

if __name__ == "__main__":
    test_note_calculation()
