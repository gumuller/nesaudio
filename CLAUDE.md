# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NESAUDIO is a Python-based terminal application that provides authentic Nintendo Entertainment System (NES) audio synthesis and playback. It features real-time audio generation, a Textual-based TUI, and support for custom music files in the .nau format (YAML-based).

## Development Commands

### Running the Application
```bash
# Run from source
python -m nesaudio

# Or if installed
nesaudio
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Testing
```bash
# Run basic tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_basic.py

# Quick audio engine test (no UI)
python -c "from nesaudio.audio.engine import AudioEngine; import time; e = AudioEngine(); e.start(); p = e.channels.pulse1; p.set_frequency(440); time.sleep(1); p.note_off(); e.stop()"
```

### Music Playback
```bash
# Play a .nau music file (requires play_music.py script)
python play_music.py music/mario_overworld.nau
```

## Architecture

### Core Audio System

The audio architecture is built around a real-time synthesis engine that runs in a separate audio thread:

1. **AudioEngine** (`nesaudio/audio/engine.py`): Main coordinator that runs the audio callback in a separate thread via sounddevice. The callback generates audio for all channels, mixes them, updates the spectrum analyzer, and handles recording.

2. **ChannelManager & Channels** (`nesaudio/audio/channels.py`): Manages 5 NES channels:
   - **PulseChannel** (x2): Square waves with 4 duty cycles (12.5%, 25%, 50%, 75%)
   - **TriangleChannel**: Pure triangle wave for bass
   - **NoiseChannel**: LFSR-based noise generator for percussion/effects
   - **DMCChannel**: Delta modulation for sample playback

   Each channel maintains its own state (phase, frequency, volume) and implements `generate(num_samples)` to produce audio buffers.

3. **Mixer** (`nesaudio/audio/mixer.py`): Combines channel outputs with per-channel and master volume control. Uses NES-style 4-bit volume quantization for authenticity.

4. **Waveforms** (`nesaudio/audio/waveforms.py`): Low-level waveform generation functions (pulse, triangle, noise) with phase continuity for click-free audio.

5. **SpectrumAnalyzer** (`nesaudio/audio/spectrum.py`): Real-time FFT analysis for visualization.

6. **Recorder** (`nesaudio/audio/recorder.py`): Captures mixed audio output to WAV files.

### Music System

1. **NAUParser** (`nesaudio/music/parser.py`): Parses .nau files (YAML format) into Song/ChannelData/Note structures. Handles pitch notation conversion and duration calculations.

2. **MusicPlayer** (`nesaudio/music/player.py`): Coordinates playback of .nau files by scheduling notes across channels based on timestamps.

3. **Sequencer** (`nesaudio/music/sequencer.py`): Time-based event scheduling for music playback.

4. **Pitch** (`nesaudio/music/pitch.py`): Converts scientific pitch notation (e.g., "C4", "A#5") to Hz frequencies.

### UI System (Textual)

The application uses the Textual framework for the terminal UI:

1. **NESAudioApp** (`nesaudio/ui/app.py`): Main Textual application that:
   - Handles keyboard input (piano keys, octave control, effects)
   - Manages the AudioEngine lifecycle
   - Coordinates UI updates via reactive properties
   - Maps QWERTY keys to musical notes

2. **Widgets**:
   - **SpectrumWidget** (`nesaudio/ui/widgets/spectrum.py`): Animated frequency visualization
   - **ChannelControlWidget** (`nesaudio/ui/widgets/channel_control.py`): Per-channel status displays
   - **KeyboardWidget** (`nesaudio/ui/widgets/keyboard.py`): Visual keyboard representation

3. **PresetManager** (`nesaudio/presets/effects.py`): Pre-configured sound effects (jump, coin, power-up, shoot, hit, explosion) that can be triggered via F-keys.

### Configuration

All constants are centralized in `nesaudio/config.py`:
- Audio settings (sample rate: 44.1kHz, buffer: 512 samples)
- NES specifications (duty cycles, frequency ranges, noise periods)
- UI settings (update rate: 30 FPS, spectrum bins: 32)
- Color scheme (NES palette-inspired)

## Key Concepts

### Thread Safety
The AudioEngine uses an `RLock` to protect shared state between the audio callback thread and the main thread. Always acquire the lock when modifying channel state from outside the audio callback.

### Phase Continuity
Waveform generators maintain phase state across buffer generations to prevent audio clicks. Each channel stores its current phase and returns the updated phase after generation.

### NES Authenticity
- Duty cycles are quantized to NES-valid values (12.5%, 25%, 50%, 75%)
- Volume is quantized to 4-bit levels (16 steps)
- Noise uses a Linear Feedback Shift Register (LFSR) algorithm
- Frequency ranges match NES hardware limits

### .nau File Format
YAML-based format with:
- Song metadata (title, composer, tempo, time_signature)
- Per-channel configuration (enabled, volume, duty_cycle/mode)
- Time-based note events with pitch, duration, and volume
- See `docs/NAU_FORMAT.md` for specification

### Audio Callback Flow
1. AudioEngine._audio_callback() is called by sounddevice with a buffer size
2. Each channel's generate() method produces samples
3. Outputs are ensured to match exact frame count (pad/trim if needed)
4. Mixer combines all channels with volume control
5. SpectrumAnalyzer processes the mixed output
6. Recorder captures audio if recording is active
7. Final output is written to the audio device

## Important Notes

### Windows-Specific
This codebase was developed on Windows. Terminal display works best with Windows Terminal or a modern terminal emulator that supports 256 colors.

### Audio Latency
The default buffer size of 512 samples at 44.1kHz provides ~12ms latency. This is tuned for real-time keyboard playing.

### Sample Files
Six complete .nau music files are included in the `music/` directory:
- Classical: Bach Prelude in C Major, Bach Minuet in G Major, Mozart Eine Kleine Nachtmusik
- Video game: Super Mario Bros, Legend of Zelda, Mega Man 2

### Dependencies
Core dependencies:
- `numpy`: Audio buffer processing and DSP
- `sounddevice`: Cross-platform audio I/O (wraps PortAudio)
- `textual`: Terminal UI framework
- `pyyaml`: .nau file parsing
- `scipy`: FFT for spectrum analysis
- `rich`: Text formatting (used by Textual)

### Entry Points
- Main application: `nesaudio/__main__.py` (defines `main()` function)
- Console script: `nesaudio` command is installed by setup.py

## Common Patterns

### Adding a New Sound Effect
1. Define the effect in `nesaudio/presets/effects.py` using the PresetManager
2. Add a keybinding in `nesaudio/ui/app.py` BINDINGS
3. Implement the action method that calls `PresetManager.trigger_effect()`

### Adding Support for a New Channel Feature
1. Update the channel class in `nesaudio/audio/channels.py`
2. Add corresponding parameters to ChannelData in `nesaudio/music/parser.py`
3. Update the .nau parser to read the new parameter
4. Update `docs/NAU_FORMAT.md` with the new specification

### Modifying Audio Generation
1. Waveform functions are in `nesaudio/audio/waveforms.py`
2. Always maintain phase continuity (return updated phase)
3. Ensure output length exactly matches requested samples
4. Use float32 dtype for audio buffers

### UI Updates
The Textual app uses reactive properties for UI updates. The spectrum widget updates at 30 FPS via a timer. Channel widgets react to engine state changes.
