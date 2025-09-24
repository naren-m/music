# Documentation Directory

This directory contains comprehensive documentation for the Carnatic Music Shruti Detection System.

## Directory Structure

```
docs/
├── README.md              # This file - documentation overview
├── references/            # Reference materials and academic texts
│   ├── Sangita_Ratnakara_Vol1.pdf     # Classical music theory text
│   └── Sangita_Ratnakara_Adyar_Vol1.pdf # Adyar Library edition
├── theory/               # Musical theory documentation
├── api/                  # API documentation
└── guides/               # Implementation guides and tutorials
```

## Reference Materials

### Sangita Ratnakara (संगीतरत्नाकर)
- **Author**: Śārṅgadeva (13th century)
- **Significance**: Foundational text for Indian classical music theory
- **Content**: 22 shruti system, raga classification, tala theory
- **Relevance**: Theoretical foundation for our shruti detection system

#### Available Editions
- `Sangita_Ratnakara_Vol1.pdf` - R.K. Shringy edition from MLBD
- `Sangita_Ratnakara_Adyar_Vol1.pdf` - Subrahmanya Shastri edition from Adyar Library

### Key Concepts for Implementation
- **22 Shrutis**: Microtonal intervals fundamental to Carnatic music
- **Frequency Ratios**: Mathematical precision for note detection
- **Raga Context**: Understanding which shrutis appear in specific ragas
- **Historical Accuracy**: Ensuring detection aligns with traditional theory

## Usage

These reference materials support:
1. **Algorithm Validation**: Verifying shruti detection accuracy
2. **Theoretical Foundation**: Understanding classical music principles
3. **Raga Analysis**: Contextual shruti identification
4. **Educational Context**: Learning resources for users

## Integration with Project

The documentation in this directory directly supports:
- `/templates/carnatic.html` - UI implementation of 22-shruti system
- JavaScript shruti detection algorithms
- Frequency mapping and cent calculations
- Raga context determination logic

For implementation details, see:
- `../CARNATIC_LEARNING_DESIGN.md` - System design
- `../IMPLEMENTATION_PLAN.md` - Development roadmap
- `../ARCHITECTURE.md` - Technical architecture