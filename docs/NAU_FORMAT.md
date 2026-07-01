# .nau File Format Specification

The `.nau` (NES Audio) format is a YAML-based file format for storing NES-style music compositions.

## Basic Structure

```yaml
title: "Song Title"
composer: "Composer Name"
tempo: 120                    # Beats per minute
time_signature: "4/4"         # Time signature
duration: 0.0                 # Optional, auto-calculated if omitted

channels:
  # Channel definitions here
```

## Channel Types

### Pulse Channels (pulse1, pulse2)

```yaml
pulse1:
  enabled: true
  duty_cycle: 0.5             # 0.125, 0.25, 0.5, or 0.75
  volume: 0.8                 # 0.0 to 1.0
  notes:
    - time: 0.0               # Start time in seconds
      pitch: "C4"             # Scientific pitch notation
      duration: 0.5           # Duration in seconds
      volume: 1.0             # Optional note volume multiplier
```

### Triangle Channel

```yaml
triangle:
  enabled: true
  volume: 0.7
  notes:
    - time: 0.0
      pitch: "C3"
      duration: 1.0
```

### Noise Channel

```yaml
noise:
  enabled: true
  volume: 0.5
  mode: "random"              # "random" or "periodic"
  notes:
    - time: 0.0
      period: 8               # 0-15 (lower = higher pitch)
      duration: 0.2
```

### DMC Channel

```yaml
dmc:
  enabled: false
  volume: 0.5
  samples:
    - time: 0.0
      sample_id: "kick"
      duration: 0.2
```

## Pitch Notation

Use scientific pitch notation:
- Format: `NOTE + OCTAVE` (e.g., "C4", "A#5", "Db3")
- Notes: C, D, E, F, G, A, B
- Sharps: C#, D#, F#, G#, A#
- Flats: Db, Eb, Gb, Ab, Bb
- Rest: "REST"
- Frequency: Direct Hz value (e.g., 440.0)

## Timing: seconds or the tempo grid

Each note/event may be positioned and sized in **either** of two ways, and the
two styles can be mixed freely within a file:

| Field | Meaning | Unit |
|-------|---------|------|
| `time` | Start position | seconds |
| `duration` | Length | seconds |
| `beat` | Start position | beats (converted with `tempo`) |
| `beats` | Length | beats (converted with `tempo`) |

Beat values are converted to seconds using the song `tempo` (BPM), where one
beat = `60 / tempo` seconds. Writing on the beat grid keeps a piece locked to
its true tempo and is the recommended way to transcribe music:

```yaml
tempo: 100          # 1 beat = 0.6 s
channels:
  pulse1:
    duty_cycle: 0.5
    notes:
      # A quarter note on beat 0, an eighth note on beat 1, etc.
      - {beat: 0.0, pitch: "E5", beats: 1.0}
      - {beat: 1.0, pitch: "C5", beats: 0.5}
      - {beat: 1.5, pitch: "G5", beats: 0.5}
```

If both `time` and `beat` are present, `time` wins; likewise `duration` takes
precedence over `beats`. Files that only use `time`/`duration` keep working
unchanged.

## Reproduction accuracy

Playback is sample-accurate: note events are triggered inside the audio
callback by sample index, so onsets are not quantized to the UI frame rate.
Pitches are snapped to the NES 11-bit timer, pulse waves are band-limited, the
triangle uses the 16-level staircase, noise uses the hardware LFSR + period
table, and the channels are combined with the console's non-linear mixer and
analog filter chain.

## Examples

See the `music/` directory for complete examples.

---

For more information, see README.md
