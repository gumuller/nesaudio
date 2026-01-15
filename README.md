# 🎮 NESAUDIO

**NES-style Terminal Audio Application**

A Python-based terminal application that brings the iconic sound of the Nintendo Entertainment System to your command line. Generate live NES-style audio, play custom music files, and experience authentic 8-bit sound synthesis with a real-time spectrum analyzer.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

### 🎹 Live Sound Generation
- **Keyboard Control**: Play notes in real-time using your QWERTY keyboard
- **5 NES Channels**:
  - 2 Pulse Wave channels (with 4 duty cycle options)
  - 1 Triangle Wave channel (perfect for bass)
  - 1 Noise channel (percussion and effects)
  - 1 DMC channel (sample playback)
- **Channel Mixer**: Adjust volume, duty cycle, and other parameters per channel
- **Octave Control**: Switch between octaves on the fly

### 🎵 Music Playback
- **Custom .nau Format**: YAML-based, human-readable music file format
- **6 Sample Songs Included**:
  - Bach - Prelude in C Major
  - Bach - Minuet in G Major
  - Mozart - Eine Kleine Nachtmusik
  - Super Mario Bros - Overworld Theme
  - The Legend of Zelda - Overworld Theme
  - Mega Man 2 - Stage Select

### 🎨 Real-time Visualization
- **Spectrum Analyzer**: Animated FFT-based frequency visualization
- **Channel Displays**: Live view of each channel's current state
- **Visual Keyboard**: See which keys you're pressing

### 🎬 Recording & Presets
- **WAV Recording**: Capture your sessions to high-quality WAV files
- **Preset Sound Effects**: 6 classic NES sounds (Jump, Coin, Power-up, Shoot, Hit, Explosion)

## 📦 Installation

### Requirements
- Python 3.9 or higher
- Windows, Linux, or macOS
- Audio output device

### Install from source

```bash
# Clone the repository
cd nesaudio

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Dependencies
The following packages will be installed automatically:
- `numpy` - Audio buffer processing
- `sounddevice` - Real-time audio I/O
- `textual` - Terminal UI framework
- `pyyaml` - .nau file parsing
- `scipy` - FFT for spectrum analyzer
- `rich` - Text formatting

## 🚀 Quick Start

### Run the application

```bash
python -m nesaudio
```

Or if installed:

```bash
nesaudio
```

### Basic Controls

**Piano Keys (Play Notes)**
- White keys: `A S D F G H J K L`
- Black keys (sharps): `W E T Y U O P`

**Octave Control**
- `Z` - Octave down
- `X` - Octave up

**Channel Selection**
- `1` - Select Pulse 1
- `2` - Select Pulse 2
- `3` - Select Triangle
- `4` - Select Noise

**Sound Effects**
- `F1` - Jump
- `F2` - Coin
- `F3` - Power-up
- `F4` - Shoot
- `F5` - Hit
- `F6` - Explosion

**Recording**
- `R` - Start/Stop recording

**Application**
- `Q` or `Esc` - Quit

## 📖 Creating .nau Music Files

The `.nau` format is a simple YAML-based format for creating NES-style music. Here's a basic example:

```yaml
title: "My Song"
composer: "Your Name"
tempo: 120
time_signature: "4/4"

channels:
  pulse1:
    enabled: true
    duty_cycle: 0.5  # 12.5%, 25%, 50%, or 75%
    volume: 0.8      # 0.0 to 1.0
    notes:
      - time: 0.0
        pitch: "C4"   # Scientific pitch notation
        duration: 0.5 # seconds
      - time: 0.5
        pitch: "E4"
        duration: 0.5
      - time: 1.0
        pitch: "G4"
        duration: 1.0

  triangle:
    enabled: true
    volume: 0.7
    notes:
      - time: 0.0
        pitch: "C2"
        duration: 2.0

  noise:
    enabled: true
    volume: 0.3
    mode: "random"  # or "periodic"
    notes:
      - time: 1.0
        period: 8    # 0-15, lower = higher pitch
        duration: 0.1
```

Save as `mysong.nau` in the `music/` directory.

## 🎼 NES Audio Specifications

### Pulse Wave Channels (2x)
- **Waveform**: Square wave
- **Duty Cycles**: 12.5%, 25%, 50%, 75%
- **Frequency Range**: 54.6 Hz to 12.4 kHz
- **Use**: Melody and harmony

### Triangle Wave Channel (1x)
- **Waveform**: Pure triangle
- **Frequency Range**: 27.3 Hz to 55.9 kHz
- **Use**: Bass lines

### Noise Channel (1x)
- **Type**: Linear Feedback Shift Register (LFSR)
- **Modes**: Periodic (tonal) and Random (white noise)
- **Use**: Percussion and sound effects

### DMC Channel (1x)
- **Type**: Delta Modulation (sample playback)
- **Use**: Drums and voice samples

## 🛠️ Project Structure

```
nesaudio/
├── nesaudio/           # Main package
│   ├── audio/          # Audio synthesis engine
│   ├── music/          # Music playback system
│   ├── ui/             # Terminal UI (Textual)
│   └── presets/        # Sound effects
├── music/              # Sample .nau files
├── tests/              # Unit tests
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## 🎯 Use Cases

- **Music Composition**: Create authentic NES-style chiptune music
- **Sound Design**: Design retro sound effects for games
- **Education**: Learn about digital audio synthesis and NES hardware
- **Performance**: Live NES sound generation with keyboard control
- **Nostalgia**: Relive the iconic sounds of classic 8-bit games

## 🔧 Troubleshooting

### Audio Issues

**No sound output:**
1. Check your system audio settings
2. Ensure your audio device is not muted
3. Try adjusting the master volume in the app

**High latency:**
- The app uses a 512-sample buffer for low latency (~12ms)
- Close other audio applications
- Check your system audio settings

**Distortion or clipping:**
- Reduce the master volume
- Lower individual channel volumes

### Installation Issues

**sounddevice installation fails:**
```bash
# On Linux, you may need PortAudio development files
sudo apt-get install libportaudio2 portaudio19-dev python3-dev
```

**textual display issues:**
- Ensure your terminal supports 256 colors
- Try a different terminal emulator (Windows Terminal, iTerm2, etc.)

## 🤝 Contributing

Contributions are welcome! Here are some areas where you could help:

- Add more sample .nau music files
- Implement additional UI screens (playback mode, mixer mode)
- Add more preset sound effects
- Improve NES audio authenticity (non-linear mixing, sweep units)
- Create a .nau file editor
- Add MIDI input support

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Nintendo Entertainment System audio hardware designers
- Koji Kondo and other NES composers for inspiration
- The chiptune and demoscene communities
- Python audio and UI library developers

## 📧 Contact

For questions, issues, or feedback, please open an issue on GitHub.

---

**Made with ❤️ and Python**

*Bringing 8-bit sound to the modern terminal*
