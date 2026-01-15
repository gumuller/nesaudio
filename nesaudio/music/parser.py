"""
.nau file parser for NES audio files (YAML format)
"""

import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from .pitch import pitch_to_hz


@dataclass
class Note:
    """Represents a single note"""
    time: float  # Start time in seconds
    pitch: str  # Pitch notation or "REST"
    duration: float  # Duration in seconds
    volume: float = 1.0  # Note volume multiplier (0.0 to 1.0)
    frequency: float = 0.0  # Calculated frequency in Hz

    def __post_init__(self):
        # Calculate frequency from pitch
        if self.frequency == 0.0:
            self.frequency = pitch_to_hz(self.pitch)


@dataclass
class NoiseNote:
    """Represents a noise channel note"""
    time: float
    period: int  # 0-15
    duration: float
    volume: float = 1.0


@dataclass
class DMCSample:
    """Represents a DMC sample playback event"""
    time: float
    sample_id: str
    duration: float
    volume: float = 1.0


@dataclass
class ChannelData:
    """Data for a single channel"""
    enabled: bool = True
    volume: float = 0.8
    duty_cycle: float = 0.5  # For pulse channels
    mode: str = "random"  # For noise channel
    notes: List[Note] = field(default_factory=list)
    noise_notes: List[NoiseNote] = field(default_factory=list)
    dmc_samples: List[DMCSample] = field(default_factory=list)


@dataclass
class Song:
    """Complete song data"""
    title: str = "Untitled"
    composer: str = "Unknown"
    tempo: int = 120
    time_signature: str = "4/4"
    duration: float = 0.0
    channels: Dict[str, ChannelData] = field(default_factory=dict)
    samples: Dict[str, List[float]] = field(default_factory=dict)

    def __post_init__(self):
        # Calculate total duration from all notes
        if self.duration == 0.0:
            max_time = 0.0
            for channel_data in self.channels.values():
                for note in channel_data.notes:
                    end_time = note.time + note.duration
                    max_time = max(max_time, end_time)
                for note in channel_data.noise_notes:
                    end_time = note.time + note.duration
                    max_time = max(max_time, end_time)
                for sample in channel_data.dmc_samples:
                    end_time = sample.time + sample.duration
                    max_time = max(max_time, end_time)
            self.duration = max_time


class NAUParser:
    """Parser for .nau files (YAML format)"""

    def parse(self, filepath: str) -> Song:
        """
        Parse a .nau file.

        Args:
            filepath: Path to .nau file

        Returns:
            Song object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML format: {e}")

        return self._parse_song_data(data)

    def _parse_song_data(self, data: Dict[str, Any]) -> Song:
        """Parse song data from dictionary"""
        song = Song(
            title=data.get('title', 'Untitled'),
            composer=data.get('composer', 'Unknown'),
            tempo=data.get('tempo', 120),
            time_signature=data.get('time_signature', '4/4'),
            duration=data.get('duration', 0.0)
        )

        # Parse samples if present
        if 'samples' in data:
            song.samples = self._parse_samples(data['samples'])

        # Parse channels
        if 'channels' in data:
            channels_data = data['channels']

            # Parse each channel
            for channel_name in ['pulse1', 'pulse2', 'triangle', 'noise', 'dmc']:
                if channel_name in channels_data:
                    song.channels[channel_name] = self._parse_channel(
                        channels_data[channel_name],
                        channel_name
                    )

        # Recalculate duration after all channels are parsed
        if song.duration == 0.0:
            max_time = 0.0
            for channel_data in song.channels.values():
                for note in channel_data.notes:
                    end_time = note.time + note.duration
                    max_time = max(max_time, end_time)
                for note in channel_data.noise_notes:
                    end_time = note.time + note.duration
                    max_time = max(max_time, end_time)
                for sample in channel_data.dmc_samples:
                    end_time = sample.time + sample.duration
                    max_time = max(max_time, end_time)
            song.duration = max_time

        return song

    def _parse_channel(self, channel_data: Dict[str, Any], channel_name: str) -> ChannelData:
        """Parse channel data"""
        channel = ChannelData(
            enabled=channel_data.get('enabled', True),
            volume=channel_data.get('volume', 0.8)
        )

        # Parse channel-specific parameters
        if 'duty_cycle' in channel_data:
            channel.duty_cycle = channel_data['duty_cycle']

        if 'mode' in channel_data:
            channel.mode = channel_data['mode']

        # Parse notes
        if 'notes' in channel_data and channel_name != 'noise':
            for note_data in channel_data['notes']:
                note = Note(
                    time=note_data.get('time', 0.0),
                    pitch=note_data.get('pitch', 'C4'),
                    duration=note_data.get('duration', 0.5),
                    volume=note_data.get('volume', 1.0)
                )
                channel.notes.append(note)

        # Parse noise notes
        if channel_name == 'noise' and 'notes' in channel_data:
            for note_data in channel_data['notes']:
                noise_note = NoiseNote(
                    time=note_data.get('time', 0.0),
                    period=note_data.get('period', 8),
                    duration=note_data.get('duration', 0.1),
                    volume=note_data.get('volume', 1.0)
                )
                channel.noise_notes.append(noise_note)

        # Parse DMC samples
        if channel_name == 'dmc' and 'samples' in channel_data:
            for sample_data in channel_data['samples']:
                dmc_sample = DMCSample(
                    time=sample_data.get('time', 0.0),
                    sample_id=sample_data.get('sample_id', 'default'),
                    duration=sample_data.get('duration', 0.2),
                    volume=sample_data.get('volume', 1.0)
                )
                channel.dmc_samples.append(dmc_sample)

        return channel

    def _parse_samples(self, samples_data: Dict[str, Any]) -> Dict[str, List[float]]:
        """Parse sample definitions"""
        samples = {}
        for sample_id, sample_data in samples_data.items():
            if isinstance(sample_data, dict) and 'data' in sample_data:
                samples[sample_id] = sample_data['data']
            elif isinstance(sample_data, list):
                samples[sample_id] = sample_data
        return samples


def validate_nau_file(filepath: str) -> tuple[bool, Optional[str]]:
    """
    Validate a .nau file without fully parsing it.

    Args:
        filepath: Path to .nau file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        parser = NAUParser()
        parser.parse(filepath)
        return True, None
    except Exception as e:
        return False, str(e)
