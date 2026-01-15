"""
Pitch notation and frequency conversion utilities
"""

import re
from typing import Union


# Note to semitone mapping (C0 = 0)
NOTE_TO_SEMITONE = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
    'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
}

# Semitone to note name (using sharps)
SEMITONE_TO_NOTE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def pitch_to_hz(pitch: Union[str, float]) -> float:
    """
    Convert pitch notation to frequency in Hz.

    Args:
        pitch: Scientific pitch notation (e.g., "C4", "A#5", "Db3") or frequency in Hz
              Special values: "REST" or None returns 0

    Returns:
        Frequency in Hz (0 for rest)

    Examples:
        >>> pitch_to_hz("A4")
        440.0
        >>> pitch_to_hz("C4")
        261.63
        >>> pitch_to_hz("REST")
        0.0
        >>> pitch_to_hz(440.0)
        440.0
    """
    # Handle rest
    if pitch is None or (isinstance(pitch, str) and pitch.upper() == "REST"):
        return 0.0

    # If already a number, return it
    if isinstance(pitch, (int, float)):
        return float(pitch)

    # Parse scientific notation
    match = re.match(r'^([A-Ga-g][#b]?)(-?\d+)$', pitch.strip())
    if not match:
        raise ValueError(f"Invalid pitch notation: {pitch}")

    note_name = match.group(1).upper()
    if len(note_name) == 2:
        note_name = note_name[0] + note_name[1].lower()  # Normalize sharps/flats

    octave = int(match.group(2))

    # Get semitone offset from C0
    if note_name not in NOTE_TO_SEMITONE:
        raise ValueError(f"Invalid note name: {note_name}")

    semitone = NOTE_TO_SEMITONE[note_name]
    midi_note = semitone + (octave + 1) * 12

    # Convert MIDI note to frequency
    # A4 (MIDI note 69) = 440 Hz
    # Formula: f = 440 * 2^((n - 69) / 12)
    frequency = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

    return frequency


def hz_to_pitch(frequency: float) -> str:
    """
    Convert frequency in Hz to scientific pitch notation.

    Args:
        frequency: Frequency in Hz

    Returns:
        Scientific pitch notation (e.g., "A4")

    Examples:
        >>> hz_to_pitch(440.0)
        'A4'
        >>> hz_to_pitch(261.63)
        'C4'
    """
    if frequency <= 0:
        return "REST"

    # Convert frequency to MIDI note number
    # n = 69 + 12 * log2(f / 440)
    import math
    midi_note = 69 + 12 * math.log2(frequency / 440.0)
    midi_note = round(midi_note)

    # Convert MIDI note to octave and semitone
    octave = (midi_note // 12) - 1
    semitone = midi_note % 12

    note_name = SEMITONE_TO_NOTE[semitone]
    return f"{note_name}{octave}"


def transpose(pitch: str, semitones: int) -> str:
    """
    Transpose a pitch by a number of semitones.

    Args:
        pitch: Scientific pitch notation
        semitones: Number of semitones to transpose (positive = up, negative = down)

    Returns:
        Transposed pitch notation

    Examples:
        >>> transpose("C4", 12)
        'C5'
        >>> transpose("A4", -2)
        'G4'
    """
    if pitch.upper() == "REST":
        return "REST"

    freq = pitch_to_hz(pitch)
    if freq == 0:
        return "REST"

    # Transpose by multiplying frequency
    transposed_freq = freq * (2.0 ** (semitones / 12.0))
    return hz_to_pitch(transposed_freq)


def get_note_range(start_pitch: str, end_pitch: str) -> list[str]:
    """
    Get all notes in a chromatic range.

    Args:
        start_pitch: Starting pitch (e.g., "C4")
        end_pitch: Ending pitch (e.g., "C5")

    Returns:
        List of pitch notations

    Examples:
        >>> get_note_range("C4", "C5")
        ['C4', 'C#4', 'D4', ... , 'B4', 'C5']
    """
    start_freq = pitch_to_hz(start_pitch)
    end_freq = pitch_to_hz(end_pitch)

    import math
    start_midi = round(69 + 12 * math.log2(start_freq / 440.0))
    end_midi = round(69 + 12 * math.log2(end_freq / 440.0))

    notes = []
    for midi_note in range(start_midi, end_midi + 1):
        octave = (midi_note // 12) - 1
        semitone = midi_note % 12
        note_name = SEMITONE_TO_NOTE[semitone]
        notes.append(f"{note_name}{octave}")

    return notes


def is_valid_pitch(pitch: str) -> bool:
    """
    Check if a pitch string is valid.

    Args:
        pitch: Pitch notation to validate

    Returns:
        True if valid, False otherwise
    """
    if pitch.upper() == "REST":
        return True

    try:
        pitch_to_hz(pitch)
        return True
    except (ValueError, AttributeError):
        return False


# Predefined note frequencies for quick reference
A4 = 440.0
C4 = 261.63
E4 = 329.63
G4 = 392.00
