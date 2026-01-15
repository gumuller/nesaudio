# 🎮 NESAUDIO - Quick Start Guide

## ✅ What Was Built

A complete NES-style terminal audio application with:

### Core Features
- **5 Authentic NES Audio Channels**: 2 Pulse waves, Triangle, Noise, DMC
- **Real-time Audio Synthesis**: Low-latency audio output (<12ms)
- **Live Keyboard Control**: Play notes like a musical keyboard
- **Spectrum Analyzer**: Real-time frequency visualization
- **6 Preset Sound Effects**: Jump, Coin, Powerup, Shoot, Hit, Explosion
- **WAV Recording**: Record your sessions
- **6 Complete Songs**: Classical (Bach, Mozart) + Video Game music (Mario, Zelda, Mega Man)

### Project Status
✅ All code implemented and tested
✅ Dependencies installed successfully
✅ Audio engine working (no errors!)
✅ Basic tests passing
✅ 6 .nau music files created

## 🚀 How to Run

### Option 1: From Command Line (Recommended)

Open a **new terminal window** (Windows Terminal, PowerShell, or CMD) and run:

```bash
cd C:\Users\gmuller\source\repos\nesaudio
python -m nesaudio
```

### Option 2: Using the installed command

```bash
nesaudio
```

**IMPORTANT**: The app needs to run in an actual terminal window (not captured output) to display the Textual UI properly.

## 🎹 Controls Once Running

### Playing Notes
- **White Keys**: `A` `S` `D` `F` `G` `H` `J` `K` `L` (C-D-E-F-G-A-B-C-D)
- **Black Keys**: `W` `E` `T` `Y` `U` `O` `P` (sharps/flats)

### Octave Control
- `Z` - Octave down
- `X` - Octave up

### Channel Selection
- `1` - Pulse 1 (thin, lead melodies)
- `2` - Pulse 2 (harmony)
- `3` - Triangle (bass)
- `4` - Noise (percussion)

### Sound Effects (F-keys)
- `F1` - Jump sound
- `F2` - Coin pickup
- `F3` - Power-up
- `F4` - Shoot
- `F5` - Hit/damage
- `F6` - Explosion

### Other Controls
- `R` - Toggle recording (saves to `recordings/` folder)
- `Q` or `Esc` - Quit application

## 📊 What You Should See

The UI has two main panels:

### Left Panel - Channel Controls
Shows real-time status of each channel:
```
Pulse 1
┌─────────┐
│Duty: 50%│
│Vol: ███░│
│440 Hz   │
│Status: ●│
└─────────┘
```

### Right Panel - Main Interaction
- **Spectrum Analyzer**: Animated bars showing frequency content
- **Virtual Keyboard**: Visual representation of keys
- **Info Bar**: Current note, octave, channel status

## 🎵 Sample Music Files

Six complete songs ready to play (in `music/` folder):

1. **bach_prelude_c_major.nau** - Bach: Prelude in C Major
2. **bach_minuet_g_major.nau** - Bach: Minuet in G Major
3. **mozart_eine_kleine.nau** - Mozart: Eine Kleine Nachtmusik
4. **mario_overworld.nau** - Super Mario Bros Theme
5. **zelda_overworld.nau** - Legend of Zelda Theme
6. **megaman_stage.nau** - Mega Man 2 Stage Select

## 🧪 Test the Audio Engine

To verify audio works without the UI:

```bash
cd C:\Users\gmuller\source\repos\nesaudio
python -c "from nesaudio.audio.engine import AudioEngine; import time; e = AudioEngine(); e.start(); p = e.channels.pulse1; p.set_frequency(440); time.sleep(1); p.note_off(); e.stop(); print('Audio works!')"
```

You should hear a 1-second tone at 440 Hz (A4).

## 📁 Project Structure

```
nesaudio/
├── nesaudio/           # Main package (all code)
│   ├── audio/          # Audio engine, channels, mixer, spectrum
│   ├── music/          # .nau parser, player, sequencer
│   ├── ui/             # Terminal UI (Textual)
│   └── presets/        # Sound effects
├── music/              # 6 sample .nau files
├── recordings/         # WAV recordings (created when you record)
├── tests/              # Unit tests
└── README.md          # Full documentation
```

## 🔧 Troubleshooting

### No Sound Output
1. Check your system audio isn't muted
2. Close other audio applications
3. Test with the simple audio command above

### Terminal Display Issues
1. Use Windows Terminal (recommended) or a modern terminal
2. Ensure terminal supports 256 colors
3. Make terminal window large enough (minimum 80x24)

### "Module not found" errors
```bash
cd C:\Users\gmuller\source\repos\nesaudio
pip install -e .
```

## 🎯 Quick Test Sequence

1. **Start the app**: `python -m nesaudio`
2. **Play a note**: Press `A` (should hear C4 note)
3. **Try an effect**: Press `F2` (coin sound)
4. **Change octave**: Press `X` then `A` (higher C note)
5. **Switch channel**: Press `2` then `A` (different duty cycle)
6. **Watch spectrum**: The bars should move with sound
7. **Quit**: Press `Q`

## 📝 Creating Your Own Music

See `docs/NAU_FORMAT.md` for the .nau file format specification.

Example `.nau` file:
```yaml
title: "My Song"
composer: "Your Name"
tempo: 120

channels:
  pulse1:
    enabled: true
    duty_cycle: 0.5
    volume: 0.8
    notes:
      - {time: 0.0, pitch: "C4", duration: 0.5}
      - {time: 0.5, pitch: "E4", duration: 0.5}
      - {time: 1.0, pitch: "G4", duration: 1.0}
```

## ✨ Next Steps

1. **Run the app** in your terminal
2. **Try playing notes** with the keyboard
3. **Experiment with channels** and effects
4. **Record a session** (press R)
5. **Create your own .nau file**

---

## Technical Details

- **Audio**: 44.1kHz sample rate, 512-sample buffer, mono output
- **Latency**: ~12ms
- **NES Authentic**: Proper duty cycles, LFSR noise, 4-bit volume quantization
- **Format**: YAML-based .nau files (human-readable)
- **UI**: Textual framework with real-time updates (30 FPS)

## 🎉 Enjoy!

You now have a fully functional NES-style audio synthesizer running in your terminal!

For more details, see `README.md` or explore the code in `nesaudio/`.
