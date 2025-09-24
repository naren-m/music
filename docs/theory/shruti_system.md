# 22 Shruti System - Theoretical Foundation

## Overview

The 22-shruti system forms the microtonal foundation of Carnatic music, as documented in the Sangita Ratnakara by Śārṅgadeva (13th century). This system provides the theoretical basis for our shruti detection implementation.

## Historical Context

From Sangita Ratnakara, Chapter 1 (Svaragatadhyaya):
- **22 Shrutis**: Smallest detectable pitch intervals
- **19 Svaras Total**: 12 vikrit (altered) + 7 shuddha (pure)
- **Mathematical Precision**: Each shruti has specific cent values from Sa (tonic)

## Shruti Mapping

### Complete 22-Shruti System

| Shruti Name | English | Western | Cents from Sa | Frequency Ratio |
|-------------|---------|---------|---------------|-----------------|
| Shadja | Shadja | Sa (C) | 0 | 1.000 |
| Suddha Ri | Suddha Ri | R₁ | 90 | 1.053 |
| Chatussruti Ri | Chatussruti Ri | R₂ | 204 | 1.122 |
| Shatsruti Ri | Shatsruti Ri | R₃ | 294 | 1.189 |
| Suddha Ga | Suddha Ga | G₁ | 316 | 1.200 |
| Sadharana Ga | Sadharana Ga | G₂ | 386 | 1.260 |
| Antara Ga | Antara Ga | G₃ | 408 | 1.280 |
| Suddha Ma | Suddha Ma | M₁ | 498 | 1.335 |
| Prati Ma | Prati Ma | M₂ | 612 | 1.414 |
| Panchama | Panchama | Pa (G) | 702 | 1.498 |
| Suddha Dha | Suddha Dha | D₁ | 792 | 1.587 |
| Chatussruti Dha | Chatussruti Dha | D₂ | 906 | 1.681 |
| Shatsruti Dha | Shatsruti Dha | D₃ | 996 | 1.782 |
| Suddha Ni | Suddha Ni | N₁ | 1018 | 1.800 |
| Kaisika Ni | Kaisika Ni | N₂ | 1088 | 1.888 |
| Kakali Ni | Kakali Ni | N₃ | 1110 | 1.920 |

## Implementation Notes

### Frequency Calculation
```javascript
frequency = baseFrequency * Math.pow(2, cents / 1200)
```

### Detection Tolerance
- **Optimal Range**: ±30 cents for precise detection
- **Forgiving Range**: ±60 cents for learning/practice mode
- **Confidence Calculation**: `1 - (deviation / tolerance)`

### Raga Context
Different ragas use specific subsets of the 22 shrutis:
- **Sankarabharanam**: Uses 7 primary shrutis (major scale equivalent)
- **Kharaharapriya**: Natural minor scale shrutis
- **Mayamalavagowla**: Mixed shruti patterns

## Technical Implementation

### JavaScript Detection Logic
```javascript
const shrutiCents = [
    {name: 'Shadja', cents: 0, western: 'Sa'},
    {name: 'Suddha Ri', cents: 90, western: 'R₁'},
    // ... complete mapping
];

function detectShruti(frequency, baseFreq) {
    const cents = 1200 * Math.log2(frequency / baseFreq);
    const normalizedCents = ((cents % 1200) + 1200) % 1200;
    
    // Find closest shruti with minimum deviation
    let closestShruti = null;
    let minDiff = Infinity;
    
    shrutiCents.forEach(shruti => {
        const diff = Math.min(
            Math.abs(normalizedCents - shruti.cents),
            Math.abs(normalizedCents - shruti.cents + 1200),
            Math.abs(normalizedCents - shruti.cents - 1200)
        );
        
        if (diff < minDiff) {
            minDiff = diff;
            closestShruti = shruti;
        }
    });
    
    return {
        shruti: closestShruti,
        deviation: minDiff,
        confidence: Math.max(0.3, 1 - (minDiff / 60))
    };
}
```

## Reference Sources

1. **Sangita Ratnakara** - Primary theoretical source
2. **Modern Carnatic Practice** - Contemporary applications
3. **Digital Music Theory** - Computer music implementations
4. **Acoustic Research** - Psychoacoustic validation

This theoretical foundation ensures our detection system maintains historical accuracy while providing practical modern functionality.