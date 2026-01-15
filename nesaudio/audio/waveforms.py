"""
Waveform generation functions for NES-style audio synthesis
"""

import numpy as np


def generate_pulse(frequency: float, duration: float, sample_rate: int,
                  duty_cycle: float = 0.5, phase: float = 0.0) -> tuple[np.ndarray, float]:
    """
    Generate a pulse wave (square wave) with specified duty cycle.

    Args:
        frequency: Frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        duty_cycle: Duty cycle (0.0 to 1.0). NES supports 0.125, 0.25, 0.5, 0.75
        phase: Starting phase in radians

    Returns:
        Tuple of (waveform array, ending phase)
    """
    num_samples = int(duration * sample_rate)
    t = np.arange(num_samples) / sample_rate

    # Calculate phase progression
    phase_array = (phase + 2 * np.pi * frequency * t) % (2 * np.pi)

    # Generate pulse wave: high when phase < duty_cycle * 2π, low otherwise
    output = np.where(phase_array < (2 * np.pi * duty_cycle), 1.0, -1.0)

    # Return output and final phase for continuity
    final_phase = phase_array[-1] if len(phase_array) > 0 else phase
    return output.astype(np.float32), final_phase


def generate_triangle(frequency: float, duration: float, sample_rate: int,
                      phase: float = 0.0) -> tuple[np.ndarray, float]:
    """
    Generate a triangle wave.

    Args:
        frequency: Frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        phase: Starting phase in radians

    Returns:
        Tuple of (waveform array, ending phase)
    """
    num_samples = int(duration * sample_rate)
    t = np.arange(num_samples) / sample_rate

    # Calculate phase progression
    phase_array = (phase + 2 * np.pi * frequency * t) % (2 * np.pi)

    # Generate triangle wave using absolute value function
    # Convert phase (0 to 2π) to triangle (-1 to 1)
    normalized_phase = phase_array / (2 * np.pi)  # 0 to 1
    output = 2 * np.abs(2 * (normalized_phase - 0.5)) - 1

    # Return output and final phase for continuity
    final_phase = phase_array[-1] if len(phase_array) > 0 else phase
    return output.astype(np.float32), final_phase


def generate_noise(duration: float, sample_rate: int, period: int = 8,
                   mode: str = "random", lfsr_state: int = 1) -> tuple[np.ndarray, int]:
    """
    Generate noise using Linear Feedback Shift Register (LFSR).

    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        period: Period setting (0-15, lower = higher pitch)
        mode: "random" for white noise or "periodic" for tonal noise
        lfsr_state: Initial LFSR state (15-bit)

    Returns:
        Tuple of (waveform array, final LFSR state)
    """
    num_samples = int(duration * sample_rate)
    output = np.zeros(num_samples, dtype=np.float32)

    # NES noise period lookup table (in CPU cycles)
    # Simplified: map to sample intervals
    period_table = [4, 8, 16, 32, 64, 96, 128, 160, 202, 254, 380, 508, 762, 1016, 2034, 4068]
    period_samples = max(1, period_table[period % 16] // 40)  # Approximate conversion

    # LFSR: 15-bit shift register
    lfsr = lfsr_state & 0x7FFF  # Ensure 15-bit
    if lfsr == 0:
        lfsr = 1

    for i in range(num_samples):
        if i % period_samples == 0:
            # Compute feedback bit
            if mode == "periodic":
                # Mode 0: feedback from bits 0 and 6
                feedback = (lfsr & 1) ^ ((lfsr >> 6) & 1)
            else:
                # Mode 1: feedback from bits 0 and 1 (white noise)
                feedback = (lfsr & 1) ^ ((lfsr >> 1) & 1)

            # Shift right and insert feedback at bit 14
            lfsr = (lfsr >> 1) | (feedback << 14)

        # Output is based on bit 0
        output[i] = 1.0 if (lfsr & 1) else -1.0

    return output, lfsr


def generate_silence(duration: float, sample_rate: int) -> np.ndarray:
    """
    Generate silence (zeros).

    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz

    Returns:
        Array of zeros
    """
    num_samples = int(duration * sample_rate)
    return np.zeros(num_samples, dtype=np.float32)


def apply_envelope(waveform: np.ndarray, attack: float = 0.01, release: float = 0.05,
                   sample_rate: int = 44100) -> np.ndarray:
    """
    Apply simple attack/release envelope to waveform.

    Args:
        waveform: Input waveform array
        attack: Attack time in seconds
        release: Release time in seconds
        sample_rate: Sample rate in Hz

    Returns:
        Waveform with envelope applied
    """
    num_samples = len(waveform)
    envelope = np.ones(num_samples, dtype=np.float32)

    # Attack
    attack_samples = int(attack * sample_rate)
    if attack_samples > 0 and attack_samples < num_samples:
        envelope[:attack_samples] = np.linspace(0.0, 1.0, attack_samples, dtype=np.float32)

    # Release
    release_samples = int(release * sample_rate)
    if release_samples > 0 and release_samples < num_samples:
        envelope[-release_samples:] = np.linspace(1.0, 0.0, release_samples, dtype=np.float32)

    return waveform * envelope


def quantize_volume(volume: float, levels: int = 16) -> float:
    """
    Quantize volume to NES-style levels (4-bit = 16 levels).

    Args:
        volume: Volume value (0.0 to 1.0)
        levels: Number of volume levels (NES uses 16)

    Returns:
        Quantized volume
    """
    quantized = np.round(volume * (levels - 1)) / (levels - 1)
    return np.clip(quantized, 0.0, 1.0)
