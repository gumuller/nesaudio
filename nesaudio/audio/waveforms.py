"""
Waveform generation for NES-style audio synthesis.

All oscillators track phase in *normalized cycles* (0.0..1.0) rather than
radians so that the band-limiting math (PolyBLEP) and the triangle staircase
line up cleanly with the hardware description in :mod:`nesaudio.audio.apu`.

Pulse, triangle and noise generators return a *unipolar* shape in [0, 1]
representing the normalized DAC waveform; the channels multiply that shape by a
4-bit (0..15) level before the non-linear mixer combines them.
"""

import numpy as np

from .apu import (
    CPU_CLOCK_NTSC,
    NOISE_PERIOD_TABLE,
    TRIANGLE_STEPS,
    polyblep,
)


def generate_pulse(frequency: float, duration: float, sample_rate: int,
                   duty_cycle: float = 0.5, phase: float = 0.0) -> tuple[np.ndarray, float]:
    """
    Generate a band-limited pulse (square) wave.

    Args:
        frequency: Frequency in Hz.
        duration: Duration in seconds.
        sample_rate: Sample rate in Hz.
        duty_cycle: Duty cycle (NES supports 0.125, 0.25, 0.5, 0.75).
        phase: Starting phase in normalized cycles (0.0..1.0).

    Returns:
        Tuple of (unipolar [0, 1] waveform, ending phase in cycles).
    """
    num_samples = int(round(duration * sample_rate))
    if num_samples <= 0:
        return np.zeros(0, dtype=np.float32), phase
    if frequency <= 0:
        return np.zeros(num_samples, dtype=np.float32), phase

    dt = frequency / sample_rate
    idx = np.arange(num_samples)
    ph = (phase + dt * idx) % 1.0

    # Canonical bipolar square with PolyBLEP corrections at both edges.
    wave = np.where(ph < duty_cycle, 1.0, -1.0)
    wave += polyblep(ph, dt)
    wave -= polyblep((ph - duty_cycle) % 1.0, dt)

    # Convert to a unipolar DAC shape in [0, 1].
    output = np.clip((wave + 1.0) * 0.5, 0.0, 1.0).astype(np.float32)

    final_phase = float((phase + dt * num_samples) % 1.0)
    return output, final_phase


def generate_triangle(frequency: float, duration: float, sample_rate: int,
                      phase: float = 0.0) -> tuple[np.ndarray, float]:
    """
    Generate the NES 16-level / 32-step triangle staircase.

    Args:
        frequency: Frequency in Hz.
        duration: Duration in seconds.
        sample_rate: Sample rate in Hz.
        phase: Starting phase in normalized cycles (0.0..1.0).

    Returns:
        Tuple of (unipolar [0, 1] waveform, ending phase in cycles).
    """
    num_samples = int(round(duration * sample_rate))
    if num_samples <= 0:
        return np.zeros(0, dtype=np.float32), phase
    if frequency <= 0:
        return np.zeros(num_samples, dtype=np.float32), phase

    dt = frequency / sample_rate
    idx = np.arange(num_samples)
    ph = (phase + dt * idx) % 1.0

    step = np.floor(ph * 32.0).astype(np.int64) % 32
    output = (TRIANGLE_STEPS[step] / 15.0).astype(np.float32)

    final_phase = float((phase + dt * num_samples) % 1.0)
    return output, final_phase


def generate_noise_block(num_samples: int, sample_rate: int, period: int = 8,
                         mode: str = "random", lfsr: int = 1,
                         accumulator: float = 0.0) -> tuple[np.ndarray, int, float]:
    """
    Generate a block of LFSR noise, clocked at the authentic NES rate.

    The 15-bit shift register is clocked once every ``NOISE_PERIOD_TABLE[period]``
    CPU cycles; ``accumulator`` carries the fractional sample position between
    calls so the noise stays phase-continuous across buffer boundaries.

    Args:
        num_samples: Number of samples to generate.
        sample_rate: Output sample rate in Hz.
        period: Noise period index (0..15, lower = higher pitch).
        mode: "random" (long 32767-step sequence) or "periodic" (short/tonal).
        lfsr: Current 15-bit LFSR state.
        accumulator: Fractional sample carry from the previous call.

    Returns:
        Tuple of (unipolar [0, 1] waveform, new LFSR state, new accumulator).
    """
    output = np.zeros(max(0, num_samples), dtype=np.float32)
    if num_samples <= 0:
        return output, lfsr, accumulator

    lfsr &= 0x7FFF
    if lfsr == 0:
        lfsr = 1

    period_cpu = NOISE_PERIOD_TABLE[period % 16]
    samples_per_clock = sample_rate * period_cpu / CPU_CLOCK_NTSC

    i = 0
    acc = accumulator
    while i < num_samples:
        # The channel is silenced whenever bit 0 of the shift register is set.
        value = 0.0 if (lfsr & 1) else 1.0

        remaining = samples_per_clock - acc
        run = int(np.ceil(remaining)) if remaining > 0 else 1
        run = max(1, min(run, num_samples - i))

        output[i:i + run] = value
        i += run
        acc += run

        # Clock the LFSR as many times as the accumulated samples allow.
        while acc >= samples_per_clock:
            acc -= samples_per_clock
            if mode == "periodic":
                feedback = (lfsr ^ (lfsr >> 6)) & 1
            else:
                feedback = (lfsr ^ (lfsr >> 1)) & 1
            lfsr = (lfsr >> 1) | (feedback << 14)

    return output, lfsr, acc


def generate_noise(duration: float, sample_rate: int, period: int = 8,
                   mode: str = "random", lfsr_state: int = 1) -> tuple[np.ndarray, int]:
    """
    Generate noise for ``duration`` seconds (convenience wrapper).

    Returns a unipolar [0, 1] waveform and the final LFSR state.
    """
    num_samples = int(round(duration * sample_rate))
    output, lfsr, _ = generate_noise_block(
        num_samples, sample_rate, period, mode, lfsr_state, 0.0
    )
    return output, lfsr


def generate_silence(duration: float, sample_rate: int) -> np.ndarray:
    """Generate silence (zeros)."""
    num_samples = int(round(duration * sample_rate))
    return np.zeros(max(0, num_samples), dtype=np.float32)


def apply_envelope(waveform: np.ndarray, attack: float = 0.01, release: float = 0.05,
                   sample_rate: int = 44100) -> np.ndarray:
    """Apply a simple linear attack/release envelope to ``waveform``."""
    num_samples = len(waveform)
    envelope = np.ones(num_samples, dtype=np.float32)

    attack_samples = int(attack * sample_rate)
    if 0 < attack_samples < num_samples:
        envelope[:attack_samples] = np.linspace(0.0, 1.0, attack_samples, dtype=np.float32)

    release_samples = int(release * sample_rate)
    if 0 < release_samples < num_samples:
        envelope[-release_samples:] = np.linspace(1.0, 0.0, release_samples, dtype=np.float32)

    return waveform * envelope


def quantize_volume(volume: float, levels: int = 16) -> float:
    """Quantize a 0.0..1.0 volume to NES-style 4-bit levels."""
    quantized = np.round(volume * (levels - 1)) / (levels - 1)
    return float(np.clip(quantized, 0.0, 1.0))
