"""
Audio mixer for combining multiple channels
"""

import numpy as np
from typing import List


class Mixer:
    """Mixes multiple audio channels into a single output"""

    def __init__(self, master_volume: float = 0.7):
        self.master_volume = np.clip(master_volume, 0.0, 1.0)
        self.channel_volumes = {}

    def set_master_volume(self, volume: float):
        """Set master output volume (0.0 to 1.0)"""
        self.master_volume = np.clip(volume, 0.0, 1.0)

    def set_channel_volume(self, channel_name: str, volume: float):
        """Set individual channel volume multiplier"""
        self.channel_volumes[channel_name] = np.clip(volume, 0.0, 1.0)

    def mix(self, channel_outputs: List[np.ndarray], channel_names: List[str] = None) -> np.ndarray:
        """
        Mix multiple channel outputs into a single output.

        Args:
            channel_outputs: List of numpy arrays (audio from each channel)
            channel_names: Optional list of channel names for individual volume control

        Returns:
            Mixed audio output
        """
        if not channel_outputs:
            return np.array([], dtype=np.float32)

        # Ensure all arrays are the same length
        max_len = max(len(arr) for arr in channel_outputs)
        padded_outputs = []

        for i, output in enumerate(channel_outputs):
            # Ensure exact length (trim or pad)
            if len(output) > max_len:
                padded = output[:max_len]
            elif len(output) < max_len:
                # Pad with zeros if needed
                padded = np.pad(output, (0, max_len - len(output)), mode='constant')
            else:
                padded = output

            # Apply individual channel volume if specified
            if channel_names and i < len(channel_names):
                channel_name = channel_names[i]
                if channel_name in self.channel_volumes:
                    padded = padded * self.channel_volumes[channel_name]

            padded_outputs.append(padded)

        # Sum all channels - convert to array first to ensure same shapes
        padded_array = np.array(padded_outputs, dtype=np.float32)
        mixed = np.sum(padded_array, axis=0)

        # Apply master volume
        mixed = mixed * self.master_volume

        # Soft clipping to prevent harsh distortion
        # Use tanh for smooth clipping
        mixed = np.tanh(mixed * 0.7) / 0.7

        # Hard clip as final safety
        mixed = np.clip(mixed, -1.0, 1.0)

        return mixed.astype(np.float32)

    def mix_with_limiter(self, channel_outputs: List[np.ndarray],
                        channel_names: List[str] = None,
                        threshold: float = 0.95) -> np.ndarray:
        """
        Mix channels with peak limiting to prevent clipping.

        Args:
            channel_outputs: List of numpy arrays
            channel_names: Optional channel names
            threshold: Peak limit threshold (0.0 to 1.0)

        Returns:
            Mixed and limited audio output
        """
        mixed = self.mix(channel_outputs, channel_names)

        # Peak limiting
        peak = np.max(np.abs(mixed))
        if peak > threshold:
            # Reduce gain to keep within threshold
            mixed = mixed * (threshold / peak)

        return mixed
