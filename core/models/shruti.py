"""
Enhanced 22-Shruti System for Carnatic Music Learning
Implements traditional South Indian microtonal scale with just intonation
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np


@dataclass
class Shruti:
    """Represents a Carnatic shruti with its musical properties"""
    name: str
    western_equiv: str
    cent_value: int
    frequency_ratio: float
    raga_usage: List[str]
    gamaka_patterns: Optional[List[str]] = None
    
    def calculate_frequency(self, base_sa: float) -> float:
        """Calculate frequency for this shruti given Sa frequency"""
        return base_sa * self.frequency_ratio
    
    def cent_deviation(self, detected_freq: float, base_sa: float) -> float:
        """Calculate cent deviation from target frequency"""
        target_freq = self.calculate_frequency(base_sa)
        if detected_freq <= 0 or target_freq <= 0:
            return float('inf')
        return 1200 * np.log2(detected_freq / target_freq)


class ShrutiSystem:
    """Complete 22-shruti system with traditional Carnatic music theory"""
    
    def __init__(self):
        self.shrutis = self._initialize_22_shruti_system()
        self.shruti_lookup = {s.name: s for s in self.shrutis}
        
    def _initialize_22_shruti_system(self) -> List[Shruti]:
        """Initialize the complete 22-shruti system with accurate ratios"""
        return [
            # Shadja grama (Sa family)
            Shruti("Shadja", "Sa", 0, 1.0, ["All ragas"]),
            
            # Rishaba grama (Ri family)
            Shruti("Suddha Rishaba", "R₁", 90, 256/243, 
                   ["Mayamalavagowla", "Hanumatodi", "Natabhairavi"]),
            Shruti("Chatussruti Rishaba", "R₂", 182, 9/8, 
                   ["Sankarabharanam", "Kharaharapriya", "Mohanam"]),
            Shruti("Shatsruti Rishaba", "R₃", 294, 32/27, 
                   ["Todi", "Shubhapantuvarali"]),
            
            # Gandhara grama (Ga family)
            Shruti("Suddha Gandhara", "G₁", 294, 32/27, 
                   ["Todi", "Bhairavi"]),
            Shruti("Sadharana Gandhara", "G₂", 316, 5/4, 
                   ["Kharaharapriya", "Natabhairavi"]),
            Shruti("Antara Gandhara", "G₃", 386, 81/64, 
                   ["Sankarabharanam", "Kalyani", "Mohanam"]),
            
            # Madhyama grama (Ma family)
            Shruti("Suddha Madhyama", "M₁", 498, 4/3, 
                   ["Sankarabharanam", "Kharaharapriya", "Most ragas"]),
            Shruti("Prati Madhyama", "M₂", 590, 45/32, 
                   ["Kalyani", "Shanmukhapriya", "Yaman"]),
            
            # Panchama grama (Pa family)
            Shruti("Panchama", "Pa", 702, 3/2, 
                   ["All ragas except Varali"]),
            
            # Dhaivata grama (Dha family)
            Shruti("Suddha Dhaivata", "D₁", 792, 128/81, 
                   ["Mayamalavagowla", "Todi", "Natabhairavi"]),
            Shruti("Chatussruti Dhaivata", "D₂", 884, 5/3, 
                   ["Sankarabharanam", "Kharaharapriya", "Mohanam"]),
            Shruti("Shatsruti Dhaivata", "D₃", 996, 16/9, 
                   ["Kalyani", "Shanmukhapriya"]),
            
            # Nishada grama (Ni family)
            Shruti("Suddha Nishada", "N₁", 996, 16/9, 
                   ["Natabhairavi", "Todi"]),
            Shruti("Kaisika Nishada", "N₂", 1018, 9/5, 
                   ["Kharaharapriya", "Dhanyasi"]),
            Shruti("Kakali Nishada", "N₃", 1088, 15/8, 
                   ["Sankarabharanam", "Kalyani", "Mohanam"]),
            
            # Microtonal variations (Pramana shrutis)
            Shruti("Komal Rishaba", "R₁⁻", 70, 25/24, 
                   ["Bhairavi variations", "Todi phrases"]),
            Shruti("Tivra Gandhara", "G₃⁺", 350, 125/96, 
                   ["Todi variations", "Raga Multani"]),
            Shruti("Komal Dhaivata", "D₁⁻", 772, 25/16, 
                   ["Malkauns", "Bageshri"]),
            Shruti("Komal Nishada", "N₁⁻", 976, 125/72, 
                   ["Darbari", "Asavari"]),
            Shruti("Tivra Madhyama", "M₂⁺", 610, 45/32, 
                   ["Raga Yaman", "Purvi"]),
            Shruti("Komal Panchama", "Pa⁻", 680, 64/45, 
                   ["Varali", "Rare ragas"])
        ]
    
    def get_shruti(self, name: str) -> Optional[Shruti]:
        """Get shruti by name"""
        return self.shruti_lookup.get(name)
    
    def find_closest_shruti(self, frequency: float, base_sa: float, 
                          tolerance_cents: float = 25) -> Optional[Shruti]:
        """Find closest shruti to given frequency within tolerance"""
        best_shruti = None
        min_deviation = float('inf')
        
        for shruti in self.shrutis:
            deviation = abs(shruti.cent_deviation(frequency, base_sa))
            if deviation < tolerance_cents and deviation < min_deviation:
                min_deviation = deviation
                best_shruti = shruti
                
        return best_shruti
    
    def get_raga_shrutis(self, raga_name: str) -> List[Shruti]:
        """Get all shrutis used in a specific raga"""
        return [s for s in self.shrutis if raga_name in s.raga_usage]
    
    def calculate_shruti_frequencies(self, base_sa: float) -> Dict[str, float]:
        """Calculate all shruti frequencies for given Sa"""
        return {s.name: s.calculate_frequency(base_sa) for s in self.shrutis}
    
    def get_gamaka_patterns(self, shruti_name: str) -> List[str]:
        """Get traditional gamaka patterns for a shruti"""
        shruti = self.get_shruti(shruti_name)
        return shruti.gamaka_patterns if shruti and shruti.gamaka_patterns else []


# Raga pattern definitions
MELAKARTA_RAGAS = {
    1: {"name": "Kanakangi", "arohanam": ["Sa", "R₁", "G₁", "M₁", "Pa", "D₁", "N₁"]},
    15: {"name": "Mayamalavagowla", "arohanam": ["Sa", "R₁", "G₃", "M₁", "Pa", "D₁", "N₃"]},
    22: {"name": "Kharaharapriya", "arohanam": ["Sa", "R₂", "G₂", "M₁", "Pa", "D₂", "N₂"]},
    29: {"name": "Sankarabharanam", "arohanam": ["Sa", "R₂", "G₃", "M₁", "Pa", "D₂", "N₃"]},
    65: {"name": "Kalyani", "arohanam": ["Sa", "R₂", "G₃", "M₂", "Pa", "D₂", "N₃"]},
    # Add more melakarta ragas as needed
}

JANYA_RAGAS = {
    "Mohanam": {
        "parent": 29,  # Sankarabharanam
        "arohanam": ["Sa", "R₂", "G₃", "Pa", "D₂"],
        "avarohanam": ["Sa", "N₃", "D₂", "Pa", "G₃", "R₂", "Sa"],
        "vakra": False
    },
    "Hamsadhvani": {
        "parent": 29,  # Sankarabharanam  
        "arohanam": ["Sa", "R₂", "G₃", "Pa", "N₃"],
        "avarohanam": ["Sa", "N₃", "Pa", "G₃", "R₂", "Sa"],
        "vakra": False
    },
    # Add more janya ragas
}


class RagaAnalyzer:
    """Analyzes note sequences for raga identification"""
    
    def __init__(self, shruti_system: ShrutiSystem):
        self.shruti_system = shruti_system
        self.melakarta_ragas = MELAKARTA_RAGAS
        self.janya_ragas = JANYA_RAGAS
    
    def analyze_note_sequence(self, shruti_sequence: List[str]) -> Dict[str, float]:
        """Analyze sequence and return raga probability scores"""
        raga_scores = {}
        
        # Check against janya ragas first (more specific)
        for raga_name, raga_data in self.janya_ragas.items():
            score = self._calculate_raga_match_score(shruti_sequence, raga_data)
            raga_scores[raga_name] = score
        
        # Check against melakarta ragas
        for raga_num, raga_data in self.melakarta_ragas.items():
            raga_name = raga_data["name"]
            score = self._calculate_raga_match_score(shruti_sequence, raga_data)
            raga_scores[raga_name] = score
            
        return raga_scores
    
    def _calculate_raga_match_score(self, sequence: List[str], raga_data: Dict) -> float:
        """Calculate how well a sequence matches a raga pattern"""
        raga_notes = set(raga_data["arohanam"])
        if "avarohanam" in raga_data:
            raga_notes.update(raga_data["avarohanam"])
            
        sequence_notes = set(sequence)
        
        # Calculate Jaccard similarity
        intersection = len(sequence_notes.intersection(raga_notes))
        union = len(sequence_notes.union(raga_notes))
        
        if union == 0:
            return 0.0
            
        base_score = intersection / union
        
        # Bonus for exact matches and penalize for foreign notes
        bonus = 0.0
        if sequence_notes.issubset(raga_notes):
            bonus += 0.2  # All notes belong to raga
            
        if len(sequence_notes.intersection(raga_notes)) == len(raga_notes):
            bonus += 0.3  # All raga notes present
            
        return min(1.0, base_score + bonus)