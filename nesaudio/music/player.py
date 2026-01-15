"""
Music player integrating sequencer with audio engine
"""

from typing import Optional
from pathlib import Path
from .parser import NAUParser, Song
from .sequencer import Sequencer
import numpy as np


class MusicPlayer:
    """Music player for .nau files"""

    def __init__(self, audio_engine):
        """
        Initialize music player.

        Args:
            audio_engine: AudioEngine instance
        """
        self.audio_engine = audio_engine
        self.sequencer = Sequencer()
        self.parser = NAUParser()
        self.current_song: Optional[Song] = None
        self.current_file: Optional[str] = None

    def load(self, filepath: str):
        """
        Load a .nau file.

        Args:
            filepath: Path to .nau file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid
        """
        self.current_song = self.parser.parse(filepath)
        self.current_file = filepath
        self.sequencer.load_song(self.current_song)

        # Configure channels based on song data
        for channel_name, channel_data in self.current_song.channels.items():
            channel = self.audio_engine.channels.get_channel(channel_name)
            if channel:
                channel.set_enabled(channel_data.enabled)
                channel.set_volume(channel_data.volume)

                # Set channel-specific parameters
                if hasattr(channel, 'set_duty_cycle'):
                    channel.set_duty_cycle(channel_data.duty_cycle)
                if hasattr(channel, 'set_mode'):
                    channel.set_mode(channel_data.mode)

        # Load DMC samples if present
        if 'dmc' in self.current_song.channels and self.current_song.samples:
            dmc_channel = self.audio_engine.channels.dmc
            # For simplicity, we'll load the first sample
            # In a full implementation, we'd handle sample_id lookup
            if self.current_song.samples:
                first_sample_data = list(self.current_song.samples.values())[0]
                dmc_channel.load_sample(np.array(first_sample_data, dtype=np.float32))

    def play(self, loop: bool = False):
        """
        Start playing the loaded song.

        Args:
            loop: Whether to loop the song
        """
        if not self.current_song:
            return

        self.sequencer.play(loop)

    def pause(self):
        """Pause playback"""
        self.sequencer.pause()

    def resume(self):
        """Resume playback"""
        self.sequencer.resume()

    def stop(self):
        """Stop playback"""
        self.sequencer.stop()
        self.audio_engine.reset_all_channels()

    def seek(self, time_seconds: float):
        """
        Seek to a specific time.

        Args:
            time_seconds: Time in seconds
        """
        self.sequencer.seek(time_seconds)

    def update(self):
        """
        Update the music player. Call this regularly (e.g., in UI update loop).

        This processes note events from the sequencer and triggers them on the audio engine.
        """
        if not self.current_song:
            return

        # Get events to trigger
        events = self.sequencer.update()

        # Process events
        for event in events:
            channel = self.audio_engine.channels.get_channel(event.channel)
            if not channel:
                continue

            if event.event_type == "note_on":
                if event.channel in ['pulse1', 'pulse2', 'triangle']:
                    # Regular note
                    channel.set_frequency(event.frequency)
                    if hasattr(channel, 'set_duty_cycle'):
                        channel.set_duty_cycle(event.duty_cycle)

                elif event.channel == 'noise':
                    # Noise note
                    channel.set_period(event.period)
                    channel.trigger(duration=0.1)  # Duration handled by event timing

                elif event.channel == 'dmc':
                    # DMC sample
                    channel.trigger()

            elif event.event_type == "note_off":
                if hasattr(channel, 'note_off'):
                    channel.note_off()

    def is_playing(self) -> bool:
        """Check if currently playing"""
        return self.sequencer.is_playing

    def get_progress(self) -> float:
        """Get playback progress (0.0 to 1.0)"""
        return self.sequencer.get_progress()

    def get_current_time(self) -> float:
        """Get current playback time in seconds"""
        return self.sequencer.get_current_time()

    def get_duration(self) -> float:
        """Get total song duration in seconds"""
        return self.sequencer.get_duration()

    def get_song_info(self) -> dict:
        """
        Get information about the current song.

        Returns:
            Dictionary with song metadata
        """
        if not self.current_song:
            return {}

        return {
            'title': self.current_song.title,
            'composer': self.current_song.composer,
            'tempo': self.current_song.tempo,
            'time_signature': self.current_song.time_signature,
            'duration': self.current_song.duration,
            'file': self.current_file
        }
