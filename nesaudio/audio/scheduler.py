"""
Sample-accurate event scheduler.

Unlike the old wall-clock :class:`~nesaudio.music.sequencer.Sequencer`, which was
polled from the UI at ~30 FPS and therefore quantized note onsets to ~33 ms,
this scheduler is driven from *inside* the audio callback.  Every note event
carries an absolute sample index and is applied exactly when the render cursor
reaches it, so timing is locked to the sound-card clock and immune to UI jitter
or garbage-collection pauses.
"""

from dataclasses import dataclass
from typing import List, Optional

from ..music.parser import Song


@dataclass
class ScheduledEvent:
    """A single channel action to apply at a precise sample position."""
    sample: int
    channel: str
    kind: str  # "note_on", "note_off", "noise_on", "dmc_on"
    frequency: float = 0.0
    volume: float = 1.0
    duty_cycle: float = 0.5
    period: int = 8
    mode: str = "random"
    duration_samples: int = 0


# Apply note_off before note_on when two events land on the same sample, so a
# new note that starts exactly when the previous one ends still wins.
_KIND_ORDER = {"note_off": 0, "note_on": 1, "noise_on": 1, "dmc_on": 1}

# Extra samples appended after the last event so envelope releases don't get cut.
_TAIL_SECONDS = 0.25


class EventScheduler:
    """Holds sample-indexed events and applies them to the channels on demand."""

    def __init__(self, sample_rate: int):
        self.sample_rate = sample_rate
        self.events: List[ScheduledEvent] = []
        self.index = 0
        self.total_samples = 0
        self.playing = False
        self.loop = False

    # -- Building -----------------------------------------------------------

    def load_song(self, song: Song):
        """Flatten a :class:`Song` into a sorted list of sample-indexed events."""
        sr = self.sample_rate
        events: List[ScheduledEvent] = []

        for channel_name, channel_data in song.channels.items():
            if not channel_data.enabled:
                continue

            if channel_name in ("pulse1", "pulse2", "triangle"):
                for note in channel_data.notes:
                    if note.frequency <= 0:  # REST
                        continue
                    start = int(round(note.time * sr))
                    end = int(round((note.time + note.duration) * sr))
                    events.append(ScheduledEvent(
                        sample=start, channel=channel_name, kind="note_on",
                        frequency=note.frequency,
                        volume=note.volume * channel_data.volume,
                        duty_cycle=channel_data.duty_cycle,
                    ))
                    events.append(ScheduledEvent(
                        sample=end, channel=channel_name, kind="note_off",
                    ))

            elif channel_name == "noise":
                for note in channel_data.noise_notes:
                    start = int(round(note.time * sr))
                    dur = max(1, int(round(note.duration * sr)))
                    events.append(ScheduledEvent(
                        sample=start, channel=channel_name, kind="noise_on",
                        volume=note.volume * channel_data.volume,
                        period=note.period, mode=channel_data.mode,
                        duration_samples=dur,
                    ))

            elif channel_name == "dmc":
                for sample_event in channel_data.dmc_samples:
                    start = int(round(sample_event.time * sr))
                    events.append(ScheduledEvent(
                        sample=start, channel=channel_name, kind="dmc_on",
                        volume=sample_event.volume * channel_data.volume,
                    ))

        events.sort(key=lambda e: (e.sample, _KIND_ORDER.get(e.kind, 1)))
        self.events = events
        self.index = 0

        song_end = int(round(song.duration * sr))
        self.total_samples = song_end + int(_TAIL_SECONDS * sr)

    # -- Playback state -----------------------------------------------------

    def start(self, loop: bool = False):
        self.playing = True
        self.loop = loop
        self.index = 0

    def stop(self):
        self.playing = False
        self.index = 0

    def reset_index(self):
        self.index = 0

    # -- Callback-driven application ---------------------------------------

    def peek_next_sample(self) -> Optional[int]:
        if self.index < len(self.events):
            return self.events[self.index].sample
        return None

    def apply_due(self, sample_pos: int, channels):
        """Apply every event whose sample index is <= ``sample_pos``."""
        while self.index < len(self.events) and self.events[self.index].sample <= sample_pos:
            self._apply(self.events[self.index], channels)
            self.index += 1

    def _apply(self, event: ScheduledEvent, channels):
        channel = channels.get_channel(event.channel)
        if channel is None:
            return

        if event.kind == "note_on":
            if hasattr(channel, "set_duty_cycle"):
                channel.set_duty_cycle(event.duty_cycle)
            channel.set_volume(event.volume)
            channel.set_frequency(event.frequency)
        elif event.kind == "note_off":
            channel.note_off()
        elif event.kind == "noise_on":
            channel.set_period(event.period)
            channel.set_mode(event.mode)
            channel.set_volume(event.volume)
            channel.trigger(duration=event.duration_samples / self.sample_rate)
        elif event.kind == "dmc_on":
            channel.set_volume(event.volume)
            channel.trigger()
