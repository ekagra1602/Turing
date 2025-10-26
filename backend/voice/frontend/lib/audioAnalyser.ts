/**
 * AudioAnalyser - Analyzes audio stream and extracts volume levels
 * Used for visualizing audio in the voice orb
 */
export class AudioAnalyser {
  private analyser: AnalyserNode;
  private dataArray: Uint8Array;
  private audioContext: AudioContext;

  constructor(source: MediaStreamAudioSourceNode, audioContext: AudioContext) {
    this.audioContext = audioContext;

    // Create analyser node
    this.analyser = audioContext.createAnalyser();
    this.analyser.fftSize = 256;
    this.analyser.smoothingTimeConstant = 0.8;

    // Connect source to analyser
    source.connect(this.analyser);

    // Create data array for frequency data
    const bufferLength = this.analyser.frequencyBinCount;
    this.dataArray = new Uint8Array(bufferLength);
  }

  /**
   * Get current audio level (0-1 scale)
   * Uses RMS (root mean square) for smooth visualization
   */
  getAudioLevel(): number {
    this.analyser.getByteFrequencyData(this.dataArray);

    // Calculate RMS (root mean square) for smoother visualization
    let sum = 0;
    for (let i = 0; i < this.dataArray.length; i++) {
      const normalized = this.dataArray[i] / 255;
      sum += normalized * normalized;
    }

    const rms = Math.sqrt(sum / this.dataArray.length);

    // Apply some smoothing and normalization
    // Emphasize the mid-range frequencies for voice
    return Math.min(1, rms * 2);
  }

  /**
   * Get frequency data for more advanced visualizations
   */
  getFrequencyData(): Uint8Array {
    this.analyser.getByteFrequencyData(this.dataArray);
    return this.dataArray;
  }

  /**
   * Cleanup
   */
  disconnect() {
    this.analyser.disconnect();
  }
}
