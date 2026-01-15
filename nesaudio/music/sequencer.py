"""
Music sequencer for timing and scheduling notes
"""

import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from .parser import Song, Note, NoiseNote, DMCSample


@dataclass
class NoteEvent:
    """Represents a note event (on or off)"""
    time: float  # Time in seconds
    channel: str  # Channel name
    event_type: str  # "note_on" or "note_off"
    frequency: float = 0.0
    volume: float = 1.0
    duty_cycle: float = 0.5
    period: int = 8  # For noise
    sample_id: str = ""  # For DMC


class Sequencer:
    """Manages note timing and event scheduling"""

    def __init__(self):
        self.song: Optional[Song] = None
        self.events: List[NoteEvent] = []
        self.event_index = 0
        self.start_time = 0.0
        self.current_time = 0.0
        self.is_playing = False
        self.loop = False

    def load_song(self, song: Song):
        """
        Load a song and generate event list.

        Args:
            song: Song object to load
        """
        self.song = song
        self.events = []
        self.event_index = 0

        # Generate events from all channels
        for channel_name, channel_data in song.channels.items():
            if not channel_data.enabled:
                continue

            if channel_name in ['pulse1', 'pulse2', 'triangle']:
                # Regular notes
                for note in channel_data.notes:
                    # Note on event
                    self.events.append(NoteEvent(
                        time=note.time,
                        channel=channel_name,
                        event_type="note_on",
                        frequency=note.frequency,
                        volume=note.volume * channel_data.volume,
                        duty_cycle=channel_data.duty_cycle
                    ))

                    # Note off event
                    self.events.append(NoteEvent(
                        time=note.time + note.duration,
                        channel=channel_name,
                        event_type="note_off"
                    ))

            elif channel_name == 'noise':
                # Noise notes
                for note in channel_data.noise_notes:
                    self.events.append(NoteEvent(
                        time=note.time,
                        channel=channel_name,
                        event_type="note_on",
                        period=note.period,
                        volume=note.volume * channel_data.volume
                    ))

                    self.events.append(NoteEvent(
                        time=note.time + note.duration,
                        channel=channel_name,
                        event_type="note_off"
                    ))

            elif channel_name == 'dmc':
                # DMC samples
                for sample in channel_data.dmc_samples:
                    self.events.append(NoteEvent(
                        time=sample.time,
                        channel=channel_name,
                        event_type="note_on",
                        sample_id=sample.sample_id,
                        volume=sample.volume * channel_data.volume
                    ))

        # Sort events by time
        self.events.sort(key=lambda e: e.time)

    def play(self, loop: bool = False):
        """Start playing"""
        self.is_playing = True
        self.start_time = time.time()
        self.event_index = 0
        self.loop = loop

    def pause(self):
        """Pause playback"""
        if self.is_playing:
            self.current_time = time.time() - self.start_time
        self.is_playing = False

    def resume(self):
        """Resume playback"""
        if not self.is_playing:
            self.start_time = time.time() - self.current_time
            self.is_playing = True

    def stop(self):
        """Stop playback"""
        self.is_playing = False
        self.event_index = 0
        self.current_time = 0.0

    def seek(self, time_seconds: float):
        """
        Seek to a specific time in the song.

        Args:
            time_seconds: Time to seek to in seconds
        """
        self.current_time = time_seconds
        self.start_time = time.time() - time_seconds

        # Find the correct event index
        self.event_index = 0
        for i, event in enumerate(self.events):
            if event.time <= time_seconds:
                self.event_index = i + 1
            else:
                break

    def update(self) -> List[NoteEvent]:
        """
        Update sequencer and get events that should trigger now.

        Returns:
            List of events to trigger
        """
        if not self.is_playing or not self.song:
            return []

        # Calculate current time
        self.current_time = time.time() - self.start_time

        # Check for loop
        if self.loop and self.current_time >= self.song.duration:
            self.seek(0)

        # Check if song is finished
        if not self.loop and self.current_time >= self.song.duration:
            self.stop()
            return []

        # Get events that should trigger now
        events_to_trigger = []
        while self.event_index < len(self.events):
            event = self.events[self.event_index]
            if event.time <= self.current_time:
                events_to_trigger.append(event)
                self.event_index += 1
            else:
                break

        return events_to_trigger

    def get_progress(self) -> float:
        """
        Get playback progress.

        Returns:
            Progress as a float from 0.0 to 1.0
        """
        if not self.song or self.song.duration == 0:
            return 0.0

        return min(self.current_time / self.song.duration, 1.0)

    def get_current_time(self) -> float:
        """Get current playback time in seconds"""
        if self.is_playing:
            return time.time() - self.start_time
        return self.current_time

    def get_duration(self) -> float:
        """Get total song duration"""
        return self.song.duration if self.song else 0.0
