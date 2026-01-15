"""
NES audio channel implementations
"""

import numpy as np
from typing import Optional
from .waveforms import generate_pulse, generate_triangle, generate_noise, generate_silence, quantize_volume
from ..config import SAMPLE_RATE, NES_PULSE_DUTY_CYCLES


class BaseChannel:
    """Base class for all NES audio channels"""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.volume = 0.8
        self.enabled = True

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate audio samples. Override in subclasses."""
        return np.zeros(num_samples, dtype=np.float32)

    def set_volume(self, volume: float):
        """Set channel volume (0.0 to 1.0)"""
        self.volume = np.clip(volume, 0.0, 1.0)

    def set_enabled(self, enabled: bool):
        """Enable or disable channel"""
        self.enabled = enabled


class PulseChannel(BaseChannel):
    """NES Pulse Wave Channel (2 available in NES)"""

    def __init__(self, sample_rate: int = SAMPLE_RATE, channel_id: int = 1):
        super().__init__(sample_rate)
        self.channel_id = channel_id
        self.frequency = 440.0  # A4
        self.duty_cycle = 0.5  # 50% duty cycle
        self.phase = 0.0
        self.target_frequency = 440.0  # For smooth frequency transitions
        self.active = False  # Whether a note is currently playing

    def set_frequency(self, frequency: float):
        """Set the frequency in Hz"""
        self.frequency = np.clip(frequency, 27.5, 4186.0)  # A0 to C8
        self.target_frequency = self.frequency
        self.active = True

    def set_duty_cycle(self, duty_cycle: float):
        """Set duty cycle. NES supports 0.125, 0.25, 0.5, 0.75"""
        # Find closest valid NES duty cycle
        valid_cycles = NES_PULSE_DUTY_CYCLES
        self.duty_cycle = min(valid_cycles, key=lambda x: abs(x - duty_cycle))

    def note_off(self):
        """Stop playing note"""
        self.active = False

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate pulse wave audio samples"""
        if not self.enabled or not self.active:
            return np.zeros(num_samples, dtype=np.float32)

        duration = num_samples / self.sample_rate
        output, self.phase = generate_pulse(
            self.frequency,
            duration,
            self.sample_rate,
            self.duty_cycle,
            self.phase
        )

        # Ensure exact length (trim or pad if needed)
        if len(output) > num_samples:
            output = output[:num_samples]
        elif len(output) < num_samples:
            output = np.pad(output, (0, num_samples - len(output)), mode='constant')

        # Apply volume with NES-style quantization
        quantized_vol = quantize_volume(self.volume)
        return output * quantized_vol


class TriangleChannel(BaseChannel):
    """NES Triangle Wave Channel (1 available in NES)"""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        super().__init__(sample_rate)
        self.frequency = 220.0  # A3
        self.phase = 0.0
        self.target_frequency = 220.0
        self.active = False

    def set_frequency(self, frequency: float):
        """Set the frequency in Hz"""
        self.frequency = np.clip(frequency, 27.5, 4186.0)
        self.target_frequency = self.frequency
        self.active = True

    def note_off(self):
        """Stop playing note"""
        self.active = False

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate triangle wave audio samples"""
        if not self.enabled or not self.active:
            return np.zeros(num_samples, dtype=np.float32)

        duration = num_samples / self.sample_rate
        output, self.phase = generate_triangle(
            self.frequency,
            duration,
            self.sample_rate,
            self.phase
        )

        # Ensure exact length (trim or pad if needed)
        if len(output) > num_samples:
            output = output[:num_samples]
        elif len(output) < num_samples:
            output = np.pad(output, (0, num_samples - len(output)), mode='constant')

        # Triangle channel typically doesn't have volume control in NES
        # but we'll allow it for flexibility
        quantized_vol = quantize_volume(self.volume)
        return output * quantized_vol


class NoiseChannel(BaseChannel):
    """NES Noise Channel (1 available in NES)"""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        super().__init__(sample_rate)
        self.period = 8  # 0-15
        self.mode = "random"  # "random" or "periodic"
        self.lfsr_state = 1
        self.active = False
        self.duration_remaining = 0.0

    def set_period(self, period: int):
        """Set noise period (0-15, lower = higher pitch)"""
        self.period = np.clip(period, 0, 15)

    def set_mode(self, mode: str):
        """Set noise mode: 'random' or 'periodic'"""
        if mode in ["random", "periodic"]:
            self.mode = mode

    def trigger(self, duration: float = 0.1):
        """Trigger a noise burst with specified duration"""
        self.active = True
        self.duration_remaining = duration

    def note_off(self):
        """Stop playing noise"""
        self.active = False
        self.duration_remaining = 0.0

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate noise audio samples"""
        if not self.enabled or not self.active:
            return np.zeros(num_samples, dtype=np.float32)

        duration = num_samples / self.sample_rate

        # Don't generate more than remaining duration
        if self.duration_remaining > 0:
            actual_duration = min(duration, self.duration_remaining)
            actual_samples = int(actual_duration * self.sample_rate)
            self.duration_remaining -= actual_duration

            if self.duration_remaining <= 0:
                self.active = False

            output, self.lfsr_state = generate_noise(
                actual_duration,
                self.sample_rate,
                self.period,
                self.mode,
                self.lfsr_state
            )

            # Ensure exact length
            if len(output) > num_samples:
                output = output[:num_samples]
            elif len(output) < num_samples:
                output = np.pad(output, (0, num_samples - len(output)), mode='constant')

            # Apply volume
            quantized_vol = quantize_volume(self.volume)
            return output * quantized_vol
        else:
            self.active = False
            return np.zeros(num_samples, dtype=np.float32)


class DMCChannel(BaseChannel):
    """NES DMC (Delta Modulation Channel) - Simplified sample playback"""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        super().__init__(sample_rate)
        self.sample_data: Optional[np.ndarray] = None
        self.position = 0
        self.active = False
        self.loop = False

    def load_sample(self, data: np.ndarray, loop: bool = False):
        """
        Load a sample for playback.

        Args:
            data: Sample data as numpy array (values between -1.0 and 1.0)
            loop: Whether to loop the sample
        """
        self.sample_data = np.array(data, dtype=np.float32)
        self.loop = loop
        self.position = 0

    def trigger(self):
        """Start playing the loaded sample"""
        if self.sample_data is not None:
            self.position = 0
            self.active = True

    def note_off(self):
        """Stop playing sample"""
        self.active = False
        self.position = 0

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate audio from sample playback"""
        if not self.enabled or not self.active or self.sample_data is None:
            return np.zeros(num_samples, dtype=np.float32)

        output = np.zeros(num_samples, dtype=np.float32)
        sample_len = len(self.sample_data)

        for i in range(num_samples):
            if self.position < sample_len:
                output[i] = self.sample_data[self.position]
                self.position += 1
            elif self.loop:
                # Restart from beginning
                self.position = 0
                if sample_len > 0:
                    output[i] = self.sample_data[self.position]
                    self.position += 1
            else:
                # Sample finished
                self.active = False
                break

        # Ensure exact length (already correct, but ensure float32)
        output = output.astype(np.float32)

        # Apply volume
        quantized_vol = quantize_volume(self.volume)
        return output * quantized_vol


class ChannelManager:
    """Manages all NES audio channels"""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.pulse1 = PulseChannel(sample_rate, channel_id=1)
        self.pulse2 = PulseChannel(sample_rate, channel_id=2)
        self.triangle = TriangleChannel(sample_rate)
        self.noise = NoiseChannel(sample_rate)
        self.dmc = DMCChannel(sample_rate)

        self.channels = [self.pulse1, self.pulse2, self.triangle, self.noise, self.dmc]

    def get_channel(self, name: str) -> Optional[BaseChannel]:
        """Get channel by name"""
        channel_map = {
            "pulse1": self.pulse1,
            "pulse2": self.pulse2,
            "triangle": self.triangle,
            "noise": self.noise,
            "dmc": self.dmc
        }
        return channel_map.get(name.lower())

    def reset_all(self):
        """Reset all channels to default state"""
        for channel in self.channels:
            if hasattr(channel, 'note_off'):
                channel.note_off()
            if hasattr(channel, 'phase'):
                channel.phase = 0.0
