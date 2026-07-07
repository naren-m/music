
/**
 * Represents a single shruti in the Carnatic music system.
 */
export interface Shruti {
  name: string;
  ratio: number;
  westernEquiv: string;
  frequency: number; // This will be calculated at runtime
}

/**
 * The 22-shruti system of Carnatic music, defined by their ratios relative to Sa.
 */
export const shrutiSystem: Omit<Shruti, 'frequency'>[] = [
  // Sa (Shadja)
  { name: 'S', ratio: 1.0, westernEquiv: 'C' },
  // Ri (Rishabha)
  { name: 'R1', ratio: 256 / 243, westernEquiv: 'C#' },
  { name: 'R2', ratio: 9 / 8, westernEquiv: 'D' },
  { name: 'R3', ratio: 32 / 27, westernEquiv: 'D#' },
  // Ga (Gandhara)
  { name: 'G1', ratio: 6 / 5, westernEquiv: 'D#' },
  { name: 'G2', ratio: 5 / 4, westernEquiv: 'E' },
  { name: 'G3', ratio: 4 / 3, westernEquiv: 'F' },
  // Ma (Madhyama)
  { name: 'M1', ratio: 45 / 32, westernEquiv: 'F#' },
  { name: 'M2', ratio: 729 / 512, westernEquiv: 'F#' },
  // Pa (Panchama)
  { name: 'P', ratio: 3 / 2, westernEquiv: 'G' },
  // Da (Dhaivata)
  { name: 'D1', ratio: 128 / 81, westernEquiv: 'G#' },
  { name: 'D2', ratio: 27 / 16, westernEquiv: 'A' },
  { name: 'D3', ratio: 16 / 9, westernEquiv: 'A#' },
  // Ni (Nishada)
  { name: 'N1', ratio: 9 / 5, westernEquiv: 'A#' },
  { name: 'N2', ratio: 15 / 8, westernEquiv: 'B' },
  { name: 'N3', ratio: 243 / 128, westernEquiv: 'B' },
];
