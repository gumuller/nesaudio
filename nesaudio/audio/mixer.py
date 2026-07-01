"""
Audio mixer combining the NES channels with the console's non-linear mixer.

The five channels are summed using Blargg's measured formula (see
:func:`nesaudio.audio.apu.mix_levels`) rather than a plain linear sum, then the
result is passed through the same analog filter chain the real hardware has:
two high-pass filters (90 Hz and 440 Hz) that remove the DAC's DC offset and a
14 kHz low-pass that rolls off the harsh top end.
"""

import numpy as np
from scipy import signal
from typing import List, Optional

from . import apu
from ..config import SAMPLE_RATE

# Order the engine feeds channels in.
_CHANNEL_ORDER = ("pulse1", "pulse2", "triangle", "noise", "dmc")

# Linear make-up gain applied after the (low-level, DC-removed) non-linear mix
# so a typical multi-channel song reaches a healthy listening level.  Applied
# before master volume and the final clip, it preserves channel balance.
_MAKEUP_GAIN = 4.0


def _one_pole_highpass(cutoff: float, sample_rate: int):
    rc = 1.0 / (2.0 * np.pi * cutoff)
    r = rc / (rc + 1.0 / sample_rate)
    b = np.array([r, -r], dtype=np.float64)
    a = np.array([1.0, -r], dtype=np.float64)
    return b, a


def _one_pole_lowpass(cutoff: float, sample_rate: int):
    dt = 1.0 / sample_rate
    rc = 1.0 / (2.0 * np.pi * cutoff)
    alpha = dt / (rc + dt)
    b = np.array([alpha], dtype=np.float64)
    a = np.array([1.0, -(1.0 - alpha)], dtype=np.float64)
    return b, a


class Mixer:
    """Mixes the NES channels into a single filtered mono output."""

    def __init__(self, master_volume: float = 0.7, sample_rate: int = SAMPLE_RATE):
        self.master_volume = float(np.clip(master_volume, 0.0, 1.0))
        self.sample_rate = sample_rate
        self.channel_volumes = {}

        # Approximate NES analog output filters (NESdev "APU Mixer").
        self._filters = [
            _one_pole_highpass(90.0, sample_rate),
            _one_pole_highpass(440.0, sample_rate),
            _one_pole_lowpass(14000.0, sample_rate),
        ]
        self._filter_states = [signal.lfilter_zi(b, a) * 0.0 for b, a in self._filters]

    def set_master_volume(self, volume: float):
        self.master_volume = float(np.clip(volume, 0.0, 1.0))

    def set_channel_volume(self, channel_name: str, volume: float):
        self.channel_volumes[channel_name] = float(np.clip(volume, 0.0, 1.0))

    def _apply_filters(self, x: np.ndarray) -> np.ndarray:
        y = x.astype(np.float64)
        for i, (b, a) in enumerate(self._filters):
            y, self._filter_states[i] = signal.lfilter(b, a, y, zi=self._filter_states[i])
        return y

    def mix(self, channel_outputs: List[np.ndarray],
            channel_names: Optional[List[str]] = None) -> np.ndarray:
        """
        Mix per-sample channel DAC levels into a filtered mono signal in [-1, 1].

        Args:
            channel_outputs: DAC-level arrays (pulse/triangle/noise in 0..15,
                dmc in 0..127).
            channel_names: Names aligned with ``channel_outputs``; defaults to
                the canonical pulse1/pulse2/triangle/noise/dmc order.
        """
        if not channel_outputs:
            return np.array([], dtype=np.float32)

        names = channel_names or list(_CHANNEL_ORDER[:len(channel_outputs)])
        max_len = max(len(arr) for arr in channel_outputs)

        levels = {name: np.zeros(max_len, dtype=np.float32) for name in _CHANNEL_ORDER}
        for output, name in zip(channel_outputs, names):
            arr = np.asarray(output, dtype=np.float32)
            if len(arr) < max_len:
                arr = np.pad(arr, (0, max_len - len(arr)))
            trim = self.channel_volumes.get(name, 1.0)
            if name in levels:
                levels[name] = arr * trim

        mixed = apu.mix_levels(
            levels["pulse1"], levels["pulse2"], levels["triangle"],
            levels["noise"], levels["dmc"],
        )

        mixed = self._apply_filters(mixed)
        mixed = mixed * (_MAKEUP_GAIN * self.master_volume)
        np.clip(mixed, -1.0, 1.0, out=mixed)
        return mixed.astype(np.float32)

    def reset(self):
        """Clear the filter memory (e.g. between songs)."""
        self._filter_states = [signal.lfilter_zi(b, a) * 0.0 for b, a in self._filters]
