"""
Music player integrating the sample-accurate scheduler with the audio engine.
"""

from typing import Optional
from .parser import NAUParser, Song
import numpy as np


class MusicPlayer:
    """Music player for .nau files."""

    def __init__(self, audio_engine):
        """
        Initialize music player.

        Args:
            audio_engine: AudioEngine instance
        """
        self.audio_engine = audio_engine
        self.parser = NAUParser()
        self.current_song: Optional[Song] = None
        self.current_file: Optional[str] = None

    def load(self, filepath: str):
        """
        Load a .nau file and hand it to the engine's scheduler.

        Args:
            filepath: Path to .nau file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid
        """
        self.current_song = self.parser.parse(filepath)
        self.current_file = filepath

        # Configure channel defaults (per-note values still override at play time).
        for channel_name, channel_data in self.current_song.channels.items():
            channel = self.audio_engine.channels.get_channel(channel_name)
            if channel:
                channel.set_enabled(channel_data.enabled)
                channel.set_volume(channel_data.volume)
                if hasattr(channel, "set_duty_cycle"):
                    channel.set_duty_cycle(channel_data.duty_cycle)
                if hasattr(channel, "set_mode"):
                    channel.set_mode(channel_data.mode)

        # Load DMC samples if present.
        if "dmc" in self.current_song.channels and self.current_song.samples:
            dmc_channel = self.audio_engine.channels.dmc
            first_sample_data = list(self.current_song.samples.values())[0]
            dmc_channel.load_sample(np.array(first_sample_data, dtype=np.float32))

        self.audio_engine.load_song(self.current_song)

    def play(self, loop: bool = False):
        """Start playing the loaded song."""
        if not self.current_song:
            return
        self.audio_engine.play_song(loop)

    def pause(self):
        """Pause playback."""
        self.audio_engine.pause_song()

    def resume(self):
        """Resume playback."""
        self.audio_engine.resume_song()

    def stop(self):
        """Stop playback."""
        self.audio_engine.stop_song()

    def update(self):
        """
        Kept for backwards compatibility.

        Triggering is now sample-accurate and handled inside the audio callback,
        so callers no longer need to poll this method; it is a no-op.
        """
        return

    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self.audio_engine.is_song_playing()

    def get_progress(self) -> float:
        """Get playback progress (0.0 to 1.0)."""
        return self.audio_engine.get_song_progress()

    def get_current_time(self) -> float:
        """Get current playback time in seconds."""
        return self.audio_engine.get_song_time()

    def get_duration(self) -> float:
        """Get total song duration in seconds."""
        return self.current_song.duration if self.current_song else 0.0

    def get_song_info(self) -> dict:
        """Get information about the current song."""
        if not self.current_song:
            return {}

        return {
            "title": self.current_song.title,
            "composer": self.current_song.composer,
            "tempo": self.current_song.tempo,
            "time_signature": self.current_song.time_signature,
            "duration": self.current_song.duration,
            "file": self.current_file,
        }
