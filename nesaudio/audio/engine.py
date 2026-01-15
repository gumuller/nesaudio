"""
Main audio engine with sounddevice integration
"""

import numpy as np
import sounddevice as sd
import threading
from typing import Optional, Callable
from .channels import ChannelManager
from .mixer import Mixer
from .spectrum import SpectrumAnalyzer
from .recorder import Recorder
from ..config import SAMPLE_RATE, BUFFER_SIZE


class AudioEngine:
    """Main audio engine coordinating all audio components"""

    def __init__(self, sample_rate: int = SAMPLE_RATE, buffer_size: int = BUFFER_SIZE):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        # Audio components
        self.channels = ChannelManager(sample_rate)
        self.mixer = Mixer(master_volume=0.7)
        self.spectrum = SpectrumAnalyzer(sample_rate)
        self.recorder = Recorder(sample_rate)

        # Audio stream
        self.stream: Optional[sd.OutputStream] = None
        self.is_running = False

        # Thread safety
        self.lock = threading.RLock()

        # Callback for UI updates (called from audio thread)
        self.update_callback: Optional[Callable] = None

    def start(self):
        """Start the audio engine"""
        if self.is_running:
            return

        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                channels=1,  # Mono
                dtype=np.float32,
                callback=self._audio_callback
            )
            self.stream.start()
            self.is_running = True
        except Exception as e:
            print(f"Error starting audio engine: {e}")
            raise

    def stop(self):
        """Stop the audio engine"""
        if not self.is_running:
            return

        self.is_running = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        # Stop recording if active
        if self.recorder.is_recording:
            self.recorder.stop()

    def _audio_callback(self, outdata: np.ndarray, frames: int, time_info, status):
        """
        Audio callback function called by sounddevice.

        This runs in a separate audio thread.
        """
        if status:
            print(f"Audio callback status: {status}")

        try:
            with self.lock:
                # Generate audio from all channels
                pulse1_out = self.channels.pulse1.generate(frames)
                pulse2_out = self.channels.pulse2.generate(frames)
                triangle_out = self.channels.triangle.generate(frames)
                noise_out = self.channels.noise.generate(frames)
                dmc_out = self.channels.dmc.generate(frames)

                # Ensure all outputs are exactly the right length
                def ensure_length(arr, length):
                    if len(arr) > length:
                        return arr[:length]
                    elif len(arr) < length:
                        return np.pad(arr, (0, length - len(arr)), mode='constant')
                    return arr

                pulse1_out = ensure_length(pulse1_out, frames)
                pulse2_out = ensure_length(pulse2_out, frames)
                triangle_out = ensure_length(triangle_out, frames)
                noise_out = ensure_length(noise_out, frames)
                dmc_out = ensure_length(dmc_out, frames)

                # Mix all channels
                channel_outputs = [pulse1_out, pulse2_out, triangle_out, noise_out, dmc_out]
                channel_names = ["pulse1", "pulse2", "triangle", "noise", "dmc"]
                mixed = self.mixer.mix(channel_outputs, channel_names)

                # Ensure mixed output is exactly frames length
                if len(mixed) > frames:
                    mixed = mixed[:frames]
                elif len(mixed) < frames:
                    mixed = np.pad(mixed, (0, frames - len(mixed)))

                # Update spectrum analyzer
                self.spectrum.update(mixed)

                # Record if enabled
                if self.recorder.is_recording:
                    self.recorder.write(mixed)

                # Output
                outdata[:, 0] = mixed

        except Exception as e:
            import traceback
            print(f"Error in audio callback: {e}")
            traceback.print_exc()
            outdata.fill(0)

    def set_update_callback(self, callback: Callable):
        """Set callback for UI updates (called from audio thread)"""
        self.update_callback = callback

    def get_spectrum_data(self, num_bins: int = 32) -> np.ndarray:
        """Get current spectrum data for visualization"""
        with self.lock:
            return self.spectrum.get_spectrum(num_bins)

    def start_recording(self, filename: Optional[str] = None):
        """Start recording audio output"""
        with self.lock:
            self.recorder.start(filename)

    def stop_recording(self) -> Optional[str]:
        """Stop recording and return filepath"""
        with self.lock:
            return self.recorder.stop()

    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self.recorder.is_recording

    def get_recording_duration(self) -> float:
        """Get current recording duration"""
        with self.lock:
            return self.recorder.get_duration()

    def set_master_volume(self, volume: float):
        """Set master output volume"""
        with self.lock:
            self.mixer.set_master_volume(volume)

    def set_channel_volume(self, channel_name: str, volume: float):
        """Set individual channel volume"""
        with self.lock:
            channel = self.channels.get_channel(channel_name)
            if channel:
                channel.set_volume(volume)

    def reset_all_channels(self):
        """Reset all channels"""
        with self.lock:
            self.channels.reset_all()

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
