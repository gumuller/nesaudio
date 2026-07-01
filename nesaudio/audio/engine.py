"""
Main audio engine with sounddevice integration
"""

import numpy as np
import sounddevice as sd
import threading
import logging
from typing import Optional, Callable
from .channels import ChannelManager
from .mixer import Mixer
from .spectrum import SpectrumAnalyzer
from .recorder import Recorder
from .scheduler import EventScheduler
from ..config import SAMPLE_RATE, BUFFER_SIZE

logger = logging.getLogger(__name__)

_CHANNEL_NAMES = ["pulse1", "pulse2", "triangle", "noise", "dmc"]


class AudioEngine:
    """Main audio engine coordinating all audio components"""

    def __init__(self, sample_rate: int = SAMPLE_RATE, buffer_size: int = BUFFER_SIZE):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        # Audio components
        self.channels = ChannelManager(sample_rate)
        self.mixer = Mixer(master_volume=0.7, sample_rate=sample_rate)
        self.spectrum = SpectrumAnalyzer(sample_rate)
        self.recorder = Recorder(sample_rate)

        # Sample-accurate song playback (driven from the audio callback).
        self.scheduler = EventScheduler(sample_rate)
        self.sample_position = 0
        self.paused = False

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
            logger.error("Error starting audio engine: %s", e)
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
            logger.warning("Audio callback status: %s", status)

        try:
            with self.lock:
                if self.scheduler.playing and not self.paused:
                    mixed = self._render_song_block(frames)
                elif self.paused:
                    mixed = np.zeros(frames, dtype=np.float32)
                else:
                    mixed = self._render_freeplay_block(frames)

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
            logger.exception("Error in audio callback: %s", e)
            outdata.fill(0)

    def _render_freeplay_block(self, frames: int) -> np.ndarray:
        """Render a block in interactive (keyboard/effects) mode."""
        outputs = [ch.generate(frames) for ch in self.channels.channels]
        return self.mixer.mix(outputs, _CHANNEL_NAMES)

    def _render_song_block(self, frames: int) -> np.ndarray:
        """
        Render a block during song playback, splitting it at event boundaries so
        every note onset lands on its exact sample.
        """
        outputs = {name: np.zeros(frames, dtype=np.float32) for name in _CHANNEL_NAMES}
        block_start = self.sample_position
        cursor = block_start
        written = 0

        while written < frames:
            self.scheduler.apply_due(cursor, self.channels)

            next_sample = self.scheduler.peek_next_sample()
            if next_sample is None or next_sample >= block_start + frames:
                segment = frames - written
            else:
                segment = min(frames - written, max(1, next_sample - cursor))

            for channel, name in zip(self.channels.channels, _CHANNEL_NAMES):
                outputs[name][written:written + segment] = channel.generate(segment)

            cursor += segment
            written += segment

        mixed = self.mixer.mix([outputs[name] for name in _CHANNEL_NAMES], _CHANNEL_NAMES)
        self.sample_position += frames

        # End-of-song / loop handling at block granularity.
        if self.sample_position >= self.scheduler.total_samples:
            if self.scheduler.loop:
                self.sample_position = 0
                self.scheduler.reset_index()
                self.channels.reset_all()
                self.mixer.reset()
            else:
                self.scheduler.stop()

        return mixed

    # -- Song playback control ---------------------------------------------

    def load_song(self, song):
        """Load a parsed Song for sample-accurate playback."""
        with self.lock:
            self.scheduler.load_song(song)
            self.sample_position = 0

    def play_song(self, loop: bool = False):
        """Start song playback from the beginning."""
        with self.lock:
            self.channels.reset_all()
            self.mixer.reset()
            self.sample_position = 0
            self.paused = False
            self.scheduler.start(loop)

    def stop_song(self):
        """Stop song playback and silence all channels."""
        with self.lock:
            self.scheduler.stop()
            self.paused = False
            self.channels.reset_all()

    def pause_song(self):
        with self.lock:
            self.paused = True

    def resume_song(self):
        with self.lock:
            self.paused = False

    def is_song_playing(self) -> bool:
        return self.scheduler.playing

    def get_song_time(self) -> float:
        return self.sample_position / self.sample_rate

    def get_song_progress(self) -> float:
        if self.scheduler.total_samples <= 0:
            return 0.0
        return min(self.sample_position / self.scheduler.total_samples, 1.0)

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
