"""
NES audio channel implementations.

Each channel produces a per-sample *DAC level* (pulse/triangle/noise in the
0..15 range, DMC in 0..127) rather than a normalized [-1, 1] waveform.  The
mixer then combines those levels with the console's non-linear formula.  Every
channel runs its output through a short attack/release envelope so that notes
fade in and out over a couple of milliseconds instead of hard-switching, which
removes the clicks the old on/off gate produced.
"""

import numpy as np
from typing import Optional

from .waveforms import generate_pulse, generate_triangle, generate_noise_block
from . import apu
from ..config import SAMPLE_RATE, NES_PULSE_DUTY_CYCLES


class Envelope:
    """Linear attack/sustain/release gain used to de-click note transitions."""

    def __init__(self, sample_rate: int, attack: float = 0.0020,
                 release: float = 0.0060):
        self.attack_samples = max(1, int(attack * sample_rate))
        self.release_samples = max(1, int(release * sample_rate))
        self.gain = 0.0
        self.gate = False
        self.finished = True

    def note_on(self):
        self.gate = True
        self.finished = False

    def note_off(self):
        self.gate = False

    def reset(self):
        self.gain = 0.0
        self.gate = False
        self.finished = True

    def process(self, num_samples: int) -> np.ndarray:
        """Return a length-``num_samples`` gain ramp and advance internal state."""
        if num_samples <= 0:
            return np.zeros(0, dtype=np.float32)

        step = (1.0 / self.attack_samples) if self.gate else (-1.0 / self.release_samples)
        ramp = self.gain + step * np.arange(1, num_samples + 1, dtype=np.float32)
        np.clip(ramp, 0.0, 1.0, out=ramp)

        self.gain = float(ramp[-1])
        if not self.gate and self.gain <= 0.0:
            self.finished = True
        return ramp


class BaseChannel:
    """Base class for all NES audio channels."""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.volume = 0.8
        self.enabled = True
        self.frequency = 0.0
        self.duty_cycle = 0.5
        self._env = Envelope(sample_rate)

    @property
    def level(self) -> int:
        """Current 4-bit (0..15) DAC level for this channel's volume."""
        return apu.volume_to_level(self.volume)

    @property
    def active(self) -> bool:
        """True while the channel is still producing sound."""
        return not self._env.finished

    def set_volume(self, volume: float):
        self.volume = float(np.clip(volume, 0.0, 1.0))

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def note_off(self):
        self._env.note_off()

    def generate(self, num_samples: int) -> np.ndarray:
        return np.zeros(num_samples, dtype=np.float32)


class PulseChannel(BaseChannel):
    """NES Pulse Wave Channel (two available on the NES)."""

    def __init__(self, sample_rate: int = SAMPLE_RATE, channel_id: int = 1):
        super().__init__(sample_rate)
        self.channel_id = channel_id
        self.frequency = 0.0
        self.duty_cycle = 0.5
        self.phase = 0.0

    def set_frequency(self, frequency: float):
        """Set frequency in Hz, snapped to the nearest NES pulse timer period."""
        self.frequency = apu.quantize_pulse_frequency(frequency)
        self._env.note_on()

    def set_duty_cycle(self, duty_cycle: float):
        """Snap to the closest NES duty cycle (0.125, 0.25, 0.5, 0.75)."""
        self.duty_cycle = min(NES_PULSE_DUTY_CYCLES, key=lambda x: abs(x - duty_cycle))

    def generate(self, num_samples: int) -> np.ndarray:
        if not self.enabled or self._env.finished:
            return np.zeros(num_samples, dtype=np.float32)

        gain = self._env.process(num_samples)
        if self.frequency <= 0:
            return np.zeros(num_samples, dtype=np.float32)

        duration = num_samples / self.sample_rate
        shape, self.phase = generate_pulse(
            self.frequency, duration, self.sample_rate, self.duty_cycle, self.phase
        )
        return (shape * self.level) * gain


class TriangleChannel(BaseChannel):
    """NES Triangle Wave Channel (one available on the NES)."""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        super().__init__(sample_rate)
        self.frequency = 0.0
        self.phase = 0.0

    def set_frequency(self, frequency: float):
        """Set frequency in Hz, snapped to the nearest NES triangle timer period."""
        self.frequency = apu.quantize_triangle_frequency(frequency)
        self._env.note_on()

    def generate(self, num_samples: int) -> np.ndarray:
        if not self.enabled or self._env.finished:
            return np.zeros(num_samples, dtype=np.float32)

        gain = self._env.process(num_samples)
        if self.frequency <= 0:
            return np.zeros(num_samples, dtype=np.float32)

        duration = num_samples / self.sample_rate
        shape, self.phase = generate_triangle(
            self.frequency, duration, self.sample_rate, self.phase
        )
        return (shape * self.level) * gain


class NoiseChannel(BaseChannel):
    """NES Noise Channel (one available on the NES)."""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        super().__init__(sample_rate)
        self.period = 8  # 0-15
        self.mode = "random"  # "random" or "periodic"
        self.lfsr_state = 1
        self.accumulator = 0.0
        self.length_remaining = -1  # samples; <0 means "until note_off"

    def set_period(self, period: int):
        self.period = int(np.clip(period, 0, 15))

    def set_mode(self, mode: str):
        if mode in ("random", "periodic"):
            self.mode = mode

    def trigger(self, duration: Optional[float] = None):
        """Start the noise. With ``duration`` it auto-stops (length counter)."""
        self._env.note_on()
        if duration is None:
            self.length_remaining = -1
        else:
            self.length_remaining = int(round(duration * self.sample_rate))

    def note_off(self):
        super().note_off()
        self.length_remaining = -1

    def generate(self, num_samples: int) -> np.ndarray:
        if not self.enabled or self._env.finished:
            return np.zeros(num_samples, dtype=np.float32)

        # Honour a length counter so timed bursts stop on their own.
        if self.length_remaining >= 0:
            if self.length_remaining == 0:
                self._env.note_off()
            else:
                self.length_remaining = max(0, self.length_remaining - num_samples)

        gain = self._env.process(num_samples)
        shape, self.lfsr_state, self.accumulator = generate_noise_block(
            num_samples, self.sample_rate, self.period, self.mode,
            self.lfsr_state, self.accumulator
        )
        return (shape * self.level) * gain


class DMCChannel(BaseChannel):
    """NES DMC (Delta Modulation Channel) - simplified sample playback."""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        super().__init__(sample_rate)
        self.sample_data: Optional[np.ndarray] = None
        self.position = 0
        self.loop = False

    def load_sample(self, data: np.ndarray, loop: bool = False):
        self.sample_data = np.asarray(data, dtype=np.float32)
        self.loop = loop
        self.position = 0

    def trigger(self):
        if self.sample_data is not None:
            self.position = 0
            self._env.note_on()

    def note_off(self):
        super().note_off()
        self.position = 0

    def generate(self, num_samples: int) -> np.ndarray:
        if not self.enabled or self._env.finished or self.sample_data is None:
            return np.zeros(num_samples, dtype=np.float32)

        gain = self._env.process(num_samples)
        sample_len = len(self.sample_data)
        raw = np.zeros(num_samples, dtype=np.float32)

        for i in range(num_samples):
            if self.position < sample_len:
                raw[i] = self.sample_data[self.position]
                self.position += 1
            elif self.loop and sample_len > 0:
                self.position = 0
                raw[i] = self.sample_data[self.position]
                self.position += 1
            else:
                self._env.note_off()
                break

        # Map the -1..1 sample into the DMC's 0..127 delta-counter range.
        dac = np.clip((raw + 1.0) * 0.5, 0.0, 1.0) * 127.0 * self.volume
        return dac * gain


class ChannelManager:
    """Manages all NES audio channels."""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.pulse1 = PulseChannel(sample_rate, channel_id=1)
        self.pulse2 = PulseChannel(sample_rate, channel_id=2)
        self.triangle = TriangleChannel(sample_rate)
        self.noise = NoiseChannel(sample_rate)
        self.dmc = DMCChannel(sample_rate)

        self.channels = [self.pulse1, self.pulse2, self.triangle, self.noise, self.dmc]

    def get_channel(self, name: str) -> Optional[BaseChannel]:
        channel_map = {
            "pulse1": self.pulse1,
            "pulse2": self.pulse2,
            "triangle": self.triangle,
            "noise": self.noise,
            "dmc": self.dmc,
        }
        return channel_map.get(name.lower())

    def reset_all(self):
        """Silence and reset every channel to its default state."""
        for channel in self.channels:
            channel._env.reset()
            if hasattr(channel, "phase"):
                channel.phase = 0.0
        self.noise.lfsr_state = 1
        self.noise.accumulator = 0.0
        self.noise.length_remaining = -1
        self.dmc.position = 0
