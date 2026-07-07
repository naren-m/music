
import { Shruti, shrutiSystem } from './shruti';

/**
 * Configuration for the Carnatic Audio Engine.
 */
export interface AudioEngineConfig {
  sampleRate: number;
  fftSize: number;
  confidenceThreshold: number;
  frequencyRange: [number, number];
}

/**
 * Represents the result of a shruti detection.
 */
export interface DetectionResult {
  shruti: Shruti | null;
  shrutiName?: string; // Convenience property for direct access to shruti.name
  detectedFrequency: number;
  centDeviation: number;
  confidence: number;
  timestamp: number;
}

/**
 * A client-side audio processing engine for Carnatic music analysis.
 * This class is designed to run in the browser using the Web Audio API.
 */
export class CarnaticAudioEngine {
  private config: AudioEngineConfig;
  private baseSaFrequency: number;
  private shrutiSystem: Shruti[];

  constructor(config: AudioEngineConfig, baseSaFrequency = 261.63) { // Default to C4 (Sa), matches backend
    this.config = config;
    this.baseSaFrequency = baseSaFrequency;
    this.shrutiSystem = shrutiSystem.map(s => ({
      ...s,
      frequency: this.baseSaFrequency * s.ratio,
    }));
  }

  /**
   * Returns the current audio engine configuration.
   * @returns The current AudioEngineConfig.
   */
  public getConfig(): AudioEngineConfig {
    return this.config;
  }

  /**
   * Updates the base Sa frequency and recalculates the shruti frequencies.
   * @param frequency The new base frequency for Sa.
   */
  public setBaseSaFrequency(frequency: number): void {
    this.baseSaFrequency = frequency;
    this.shrutiSystem = shrutiSystem.map(s => ({
      ...s,
      frequency: this.baseSaFrequency * s.ratio,
    }));
  }

  /**
   * Detects the dominant frequency from an audio buffer using an FFT-based approach.
   * This is a simplified pitch detection algorithm.
   *
   * @param audioBuffer The raw audio data from the Web Audio API.
   * @returns The detected fundamental frequency, or null if not found.
   */
  private detectFundamentalFrequency(audioBuffer: Float32Array): { frequency: number; confidence: number } | null {
    // In a real implementation, you'd apply a window function here.
    // For now, we'll just copy the data.
    const audioSlice = audioBuffer.slice(0, this.config.fftSize);

    // A proper FFT implementation is required here.
    // The Web Audio API provides `AnalyserNode.getFloatFrequencyData` which is what
    // we should be using. This method is a placeholder for the logic that will
    // process the output of `AnalyserNode`.
    
    // This is a dummy implementation. A real implementation would use a proper
    // pitch detection algorithm (e.g., YIN, McLeod, etc.) on the FFT data.
    const maxVal = Math.max(...audioSlice);
    const maxIndex = audioSlice.indexOf(maxVal);
    
    if (maxIndex === -1) return null;

    const fundamentalFrequency = (maxIndex * this.config.sampleRate) / this.config.fftSize;
    
    if (fundamentalFrequency < this.config.frequencyRange[0] || fundamentalFrequency > this.config.frequencyRange[1]) {
      return null;
    }

    // Dummy confidence value. A real implementation would be more sophisticated.
    const confidence = maxVal > 0.1 ? 0.9 : 0.2;

    return { frequency: fundamentalFrequency, confidence };
  }

  /**
   * Finds the closest Carnatic shruti to a given frequency.
   *
   * @param frequency The frequency to analyze.
   * @returns The closest shruti and the deviation in cents.
   */
  private findClosestShruti(frequency: number): { shruti: Shruti; centDeviation: number } {
    let closestShruti = this.shrutiSystem[0];
    let minDistance = Infinity;

    for (const shruti of this.shrutiSystem) {
      const distance = Math.abs(frequency - shruti.frequency);
      if (distance < minDistance) {
        minDistance = distance;
        closestShruti = shruti;
      }
    }

    const centDeviation = 1200 * Math.log2(frequency / closestShruti.frequency);

    return { shruti: closestShruti, centDeviation };
  }

  /**
   * Processes a chunk of audio data and detects the Carnatic shruti.
   *
   * @param audioBuffer The raw audio data (Float32Array).
   * @returns A DetectionResult, or null if no reliable pitch was detected.
   */
  public detectShruti(audioBuffer: Float32Array): DetectionResult | null {
    const pitch = this.detectFundamentalFrequency(audioBuffer);

    if (!pitch || pitch.confidence < this.config.confidenceThreshold) {
      return null;
    }

    const { shruti, centDeviation } = this.findClosestShruti(pitch.frequency);

    return {
      shruti,
      detectedFrequency: pitch.frequency,
      centDeviation,
      confidence: pitch.confidence,
      timestamp: Date.now(),
    };
  }
}
