"""
Real-time spectrum analyzer using FFT
"""

import numpy as np
from scipy import signal
from ..config import SPECTRUM_FFT_SIZE, SPECTRUM_BINS, SAMPLE_RATE


class SpectrumAnalyzer:
    """Real-time FFT-based spectrum analyzer"""

    def __init__(self, sample_rate: int = SAMPLE_RATE, fft_size: int = SPECTRUM_FFT_SIZE):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.buffer = np.zeros(fft_size, dtype=np.float32)
        self.spectrum = np.zeros(fft_size // 2, dtype=np.float32)
        self.smoothed_spectrum = np.zeros(fft_size // 2, dtype=np.float32)
        self.smoothing_factor = 0.7  # Smoothing for visual appeal

    def update(self, audio_data: np.ndarray):
        """
        Update spectrum with new audio data.

        Args:
            audio_data: New audio samples
        """
        if len(audio_data) == 0:
            return

        # Roll buffer and append new data
        data_len = min(len(audio_data), self.fft_size)
        self.buffer = np.roll(self.buffer, -data_len)
        self.buffer[-data_len:] = audio_data[-data_len:]

        # Apply window function to reduce spectral leakage
        windowed = self.buffer * signal.windows.hann(self.fft_size)

        # Compute FFT
        fft = np.fft.rfft(windowed)
        self.spectrum = np.abs(fft)

        # Ensure smoothed_spectrum matches spectrum size
        if len(self.smoothed_spectrum) != len(self.spectrum):
            self.smoothed_spectrum = np.zeros_like(self.spectrum, dtype=np.float32)

        # Smooth for better visualization
        self.smoothed_spectrum = (
            self.smoothing_factor * self.smoothed_spectrum +
            (1 - self.smoothing_factor) * self.spectrum
        )

    def get_spectrum(self, num_bins: int = SPECTRUM_BINS, use_smoothed: bool = True) -> np.ndarray:
        """
        Get spectrum data binned into specified number of bins.

        Args:
            num_bins: Number of frequency bins for output
            use_smoothed: Use smoothed spectrum for visualization

        Returns:
            Array of spectrum magnitudes (num_bins,)
        """
        spectrum_data = self.smoothed_spectrum if use_smoothed else self.spectrum

        # Use logarithmic spacing for bins (more musically relevant)
        bin_edges = np.logspace(0, np.log10(len(spectrum_data)), num_bins + 1)
        binned = np.zeros(num_bins, dtype=np.float32)

        for i in range(num_bins):
            start = int(bin_edges[i])
            end = int(bin_edges[i + 1])
            if end > start:
                # Take maximum in each bin for better peak visibility
                binned[i] = np.max(spectrum_data[start:end])

        # Normalize to 0-1 range with logarithmic scaling
        if np.max(binned) > 0:
            binned = binned / np.max(binned)

        # Apply logarithmic scaling for better visualization of quiet sounds
        binned = np.log10(binned + 1e-6) + 6  # +6 to make range 0-6
        binned = np.clip(binned / 6.0, 0, 1)  # Normalize to 0-1

        return binned

    def get_frequency_bins(self, num_bins: int = SPECTRUM_BINS) -> np.ndarray:
        """
        Get the center frequencies for each bin.

        Args:
            num_bins: Number of bins

        Returns:
            Array of center frequencies in Hz
        """
        bin_edges = np.logspace(0, np.log10(len(self.spectrum)), num_bins + 1)
        freqs = np.fft.rfftfreq(self.fft_size, 1.0 / self.sample_rate)

        center_freqs = np.zeros(num_bins)
        for i in range(num_bins):
            start = int(bin_edges[i])
            end = int(bin_edges[i + 1])
            if end > start:
                center_freqs[i] = (freqs[start] + freqs[end]) / 2

        return center_freqs

    def get_peak_frequency(self) -> float:
        """
        Get the dominant frequency in the spectrum.

        Returns:
            Peak frequency in Hz
        """
        peak_bin = np.argmax(self.smoothed_spectrum)
        freqs = np.fft.rfftfreq(self.fft_size, 1.0 / self.sample_rate)
        return freqs[peak_bin]

    def reset(self):
        """Reset the analyzer state"""
        self.buffer.fill(0)
        self.spectrum.fill(0)
        self.smoothed_spectrum.fill(0)
