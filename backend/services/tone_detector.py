import numpy as np
from scipy import signal
from scipy.io import wavfile
import librosa
from typing import Tuple, Optional, List
from backend.core.config import get_settings

settings = get_settings()


class ToneDetector:
    """
    Detects two-tone sequential paging signals in audio files.
    Uses Goertzel algorithm for efficient single-frequency detection.
    """

    def __init__(self, tolerance_hz: float = None):
        self.tolerance_hz = tolerance_hz or settings.frequency_tolerance_hz

    def goertzel(self, samples: np.ndarray, sample_rate: int, target_freq: float) -> float:
        """
        Goertzel algorithm for detecting a specific frequency.
        More efficient than FFT for single frequency detection.

        Returns the magnitude of the target frequency.
        """
        n = len(samples)
        k = int(0.5 + (n * target_freq / sample_rate))
        omega = (2.0 * np.pi * k) / n

        cos_omega = np.cos(omega)
        sin_omega = np.sin(omega)
        coeff = 2.0 * cos_omega

        q0 = 0.0
        q1 = 0.0
        q2 = 0.0

        for sample in samples:
            q0 = coeff * q1 - q2 + sample
            q2 = q1
            q1 = q0

        real = q1 - q2 * cos_omega
        imag = q2 * sin_omega
        magnitude = np.sqrt(real * real + imag * imag)

        return magnitude / n

    def detect_tone_in_window(
        self,
        samples: np.ndarray,
        sample_rate: int,
        freq_range: Tuple[float, float] = (200, 3000),
        resolution_hz: float = 0.5
    ) -> Tuple[Optional[float], float]:
        """
        Detects the dominant frequency in a window of samples.

        Returns:
            (frequency, confidence) tuple
        """
        # Generate candidate frequencies
        min_freq, max_freq = freq_range
        test_frequencies = np.arange(min_freq, max_freq, resolution_hz)

        # Test each frequency using Goertzel
        magnitudes = np.array([
            self.goertzel(samples, sample_rate, freq)
            for freq in test_frequencies
        ])

        # Find peak
        peak_idx = np.argmax(magnitudes)
        peak_freq = test_frequencies[peak_idx]
        peak_magnitude = magnitudes[peak_idx]

        # Calculate confidence based on peak prominence
        mean_magnitude = np.mean(magnitudes)
        std_magnitude = np.std(magnitudes)

        if std_magnitude > 0:
            confidence = min(1.0, (peak_magnitude - mean_magnitude) / (5 * std_magnitude))
        else:
            confidence = 0.0

        # Refine frequency estimate around peak
        if peak_idx > 0 and peak_idx < len(magnitudes) - 1:
            refined_freq = self._refine_frequency(
                samples, sample_rate, peak_freq, resolution_hz / 2
            )
            return refined_freq, confidence

        return peak_freq, confidence

    def _refine_frequency(
        self,
        samples: np.ndarray,
        sample_rate: int,
        center_freq: float,
        step: float
    ) -> float:
        """Refine frequency estimate around a peak."""
        test_freqs = np.arange(center_freq - step * 2, center_freq + step * 2, step / 4)
        magnitudes = np.array([
            self.goertzel(samples, sample_rate, freq)
            for freq in test_freqs
        ])
        peak_idx = np.argmax(magnitudes)
        return test_freqs[peak_idx]

    def detect_two_tone_sequence(
        self,
        audio_path: str
    ) -> Tuple[Optional[float], Optional[float], float]:
        """
        Detects two sequential tones in an audio file.

        Returns:
            (tone1_hz, tone2_hz, overall_confidence) tuple
        """
        # Load audio file
        try:
            samples, sample_rate = librosa.load(audio_path, sr=None, mono=True)
        except Exception as e:
            raise ValueError(f"Failed to load audio file: {str(e)}")

        # Normalize samples
        samples = samples / np.max(np.abs(samples))

        # Calculate energy envelope to find tone boundaries
        frame_length = int(sample_rate * 0.01)  # 10ms frames
        energy = np.array([
            np.sum(samples[i:i+frame_length]**2)
            for i in range(0, len(samples) - frame_length, frame_length)
        ])

        # Smooth energy
        energy_smooth = signal.medfilt(energy, kernel_size=5)

        # Find threshold for tone presence
        threshold = np.mean(energy_smooth) + 2 * np.std(energy_smooth)
        tone_active = energy_smooth > threshold

        # Find tone segments
        tone_segments = self._find_tone_segments(tone_active, frame_length, sample_rate)

        if len(tone_segments) < 2:
            return None, None, 0.0

        # Analyze first two tone segments
        tone1_segment = tone_segments[0]
        tone2_segment = tone_segments[1]

        # Extract samples for each tone
        tone1_samples = samples[tone1_segment[0]:tone1_segment[1]]
        tone2_samples = samples[tone2_segment[0]:tone2_segment[1]]

        # Detect frequencies
        tone1_freq, tone1_conf = self.detect_tone_in_window(tone1_samples, sample_rate)
        tone2_freq, tone2_conf = self.detect_tone_in_window(tone2_samples, sample_rate)

        # Overall confidence
        overall_confidence = (tone1_conf + tone2_conf) / 2.0

        return tone1_freq, tone2_freq, overall_confidence

    def _find_tone_segments(
        self,
        tone_active: np.ndarray,
        frame_length: int,
        sample_rate: int
    ) -> List[Tuple[int, int]]:
        """
        Find continuous segments where tones are present.

        Returns list of (start_sample, end_sample) tuples.
        """
        segments = []
        in_tone = False
        start_idx = 0

        min_tone_frames = int(0.1 * sample_rate / frame_length)  # Min 100ms

        for i, active in enumerate(tone_active):
            if active and not in_tone:
                start_idx = i
                in_tone = True
            elif not active and in_tone:
                if i - start_idx >= min_tone_frames:
                    segments.append((
                        start_idx * frame_length,
                        i * frame_length
                    ))
                in_tone = False

        # Handle case where tone extends to end
        if in_tone and len(tone_active) - start_idx >= min_tone_frames:
            segments.append((
                start_idx * frame_length,
                len(tone_active) * frame_length
            ))

        return segments

    def find_matching_tone(
        self,
        detected_tone1: float,
        detected_tone2: float,
        tone_entries: List[Tuple[int, str, float, float]]
    ) -> Optional[Tuple[int, str, float, float]]:
        """
        Find matching tone entry from database.

        Args:
            detected_tone1: First detected frequency in Hz
            detected_tone2: Second detected frequency in Hz
            tone_entries: List of (id, label, tone1_hz, tone2_hz) tuples

        Returns:
            Matching entry tuple or None
        """
        for entry in tone_entries:
            entry_id, label, tone1_hz, tone2_hz = entry

            # Check if both tones match within tolerance
            tone1_match = abs(detected_tone1 - tone1_hz) <= self.tolerance_hz
            tone2_match = abs(detected_tone2 - tone2_hz) <= self.tolerance_hz

            if tone1_match and tone2_match:
                return entry

        return None
