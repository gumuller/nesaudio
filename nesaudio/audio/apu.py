"""
NES APU (2A03) hardware constants and DSP helpers.

This module centralizes the authentic hardware numbers used across the
synthesis code so every channel and the mixer agree on the same reference:

* NTSC CPU clock and the pulse/triangle timer -> frequency relationship
* The noise channel period lookup table (CPU cycles per LFSR shift)
* The non-linear channel mixer (Blargg's formula from the NESdev wiki)
* The 4-bit volume DAC and the 32-step triangle staircase
* A band-limited step (PolyBLEP) helper for alias-reduced square waves

References (NESdev wiki): APU_Pulse, APU_Triangle, APU_Noise, APU_Mixer.
"""

import numpy as np

# --- Master timing -----------------------------------------------------------

# NTSC 2A03 CPU clock in Hz. Both pulse and triangle timers derive from this.
CPU_CLOCK_NTSC = 1_789_773.0

# Pulse channel:    f = CPU / (16 * (t + 1)),  t is an 11-bit timer (0..2047)
# Triangle channel: f = CPU / (32 * (t + 1)),  t is an 11-bit timer (0..2047)
PULSE_TIMER_DIVIDER = 16.0
TRIANGLE_TIMER_DIVIDER = 32.0
TIMER_MAX = 2047

# On real hardware a pulse channel is silenced when its timer period is below 8.
PULSE_MIN_TIMER = 8

# --- Volume DAC --------------------------------------------------------------

# 4-bit volume: channels output an integer level in [0, 15].
VOLUME_LEVELS = 16
MAX_VOLUME = 15

# --- Noise channel -----------------------------------------------------------

# Number of CPU cycles between LFSR shifts for each of the 16 period settings
# (NTSC).  Lower index -> shorter period -> higher noise pitch.
NOISE_PERIOD_TABLE = [
    4, 8, 16, 32, 64, 96, 128, 160,
    202, 254, 380, 508, 762, 1016, 2034, 4068,
]

# --- Non-linear mixer constants (NESdev "APU Mixer") -------------------------

_PULSE_NUM = 95.88
_PULSE_DEN = 8128.0
_PULSE_OFFSET = 100.0

_TND_NUM = 159.79
_TND_TRIANGLE_DEN = 8227.0
_TND_NOISE_DEN = 12241.0
_TND_DMC_DEN = 22638.0
_TND_OFFSET = 100.0


def pulse_timer(frequency: float) -> int:
    """Return the 11-bit pulse timer period closest to ``frequency``."""
    if frequency <= 0:
        return TIMER_MAX
    t = int(round(CPU_CLOCK_NTSC / (PULSE_TIMER_DIVIDER * frequency) - 1.0))
    return int(np.clip(t, 0, TIMER_MAX))


def triangle_timer(frequency: float) -> int:
    """Return the 11-bit triangle timer period closest to ``frequency``."""
    if frequency <= 0:
        return TIMER_MAX
    t = int(round(CPU_CLOCK_NTSC / (TRIANGLE_TIMER_DIVIDER * frequency) - 1.0))
    return int(np.clip(t, 0, TIMER_MAX))


def quantize_pulse_frequency(frequency: float) -> float:
    """Snap ``frequency`` to the nearest pitch a real NES pulse channel can make.

    Returns 0.0 when the note falls outside the channel's playable range (the
    hardware mutes the channel for timer periods below :data:`PULSE_MIN_TIMER`).
    """
    if frequency <= 0:
        return 0.0
    t = pulse_timer(frequency)
    if t < PULSE_MIN_TIMER:
        return 0.0
    return CPU_CLOCK_NTSC / (PULSE_TIMER_DIVIDER * (t + 1))


def quantize_triangle_frequency(frequency: float) -> float:
    """Snap ``frequency`` to the nearest pitch a real NES triangle can make."""
    if frequency <= 0:
        return 0.0
    t = triangle_timer(frequency)
    return CPU_CLOCK_NTSC / (TRIANGLE_TIMER_DIVIDER * (t + 1))


def volume_to_level(volume: float) -> int:
    """Convert a 0.0..1.0 volume into a 4-bit (0..15) DAC level."""
    return int(np.clip(round(volume * MAX_VOLUME), 0, MAX_VOLUME))


# 32-entry triangle staircase: 15,14,...,1,0,0,1,...,14,15 (values 0..15).
TRIANGLE_STEPS = np.array(
    list(range(15, -1, -1)) + list(range(0, 16)), dtype=np.float32
)


def polyblep(t: np.ndarray, dt: float) -> np.ndarray:
    """PolyBLEP residual used to band-limit a hard step at phase wrap ``t == 0``.

    ``t`` is the fractional phase in cycles [0, 1) and ``dt`` is the per-sample
    phase increment.  Subtracting/adding this correction around each edge of a
    naive square wave removes most of the aliasing that a raw comparator
    produces at 44.1 kHz, matching what a real (heavily filtered) NES sounds
    like far better than point sampling.
    """
    out = np.zeros_like(t)
    if dt <= 0.0:
        return out

    # Just after a rising discontinuity (t in [0, dt)).
    mask = t < dt
    x = t[mask] / dt
    out[mask] = x + x - x * x - 1.0

    # Just before the discontinuity wraps (t in (1 - dt, 1)).
    mask = t > (1.0 - dt)
    x = (t[mask] - 1.0) / dt
    out[mask] = x * x + x + x + 1.0

    return out


def mix_levels(pulse1: np.ndarray, pulse2: np.ndarray, triangle: np.ndarray,
               noise: np.ndarray, dmc: np.ndarray) -> np.ndarray:
    """Combine per-sample channel DAC levels with the NES non-linear mixer.

    Inputs are amplitude arrays: pulse/triangle/noise in [0, 15] and dmc in
    [0, 127].  Returns a mono signal in roughly [0, 1] (still DC-offset; the
    caller is expected to high-pass it, as the real console does).
    """
    p_sum = pulse1 + pulse2
    pulse_out = np.where(
        p_sum > 0.0,
        _PULSE_NUM / (_PULSE_DEN / np.where(p_sum > 0.0, p_sum, 1.0) + _PULSE_OFFSET),
        0.0,
    )

    tnd = (triangle / _TND_TRIANGLE_DEN
           + noise / _TND_NOISE_DEN
           + dmc / _TND_DMC_DEN)
    tnd_out = np.where(
        tnd > 0.0,
        _TND_NUM / (1.0 / np.where(tnd > 0.0, tnd, 1.0) + _TND_OFFSET),
        0.0,
    )

    return (pulse_out + tnd_out).astype(np.float32)
