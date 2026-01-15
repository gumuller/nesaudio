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

## Examples

See the `music/` directory for complete examples.

---

For more information, see README.md
