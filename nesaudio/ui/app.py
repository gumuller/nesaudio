"""
Main Textual application for NESAUDIO
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label
from textual.reactive import reactive
from textual import events
from pathlib import Path

from ..audio.engine import AudioEngine
from ..music.player import MusicPlayer
from ..music.pitch import pitch_to_hz
from ..presets.effects import PresetManager
from .widgets.spectrum import SpectrumWidget
from .widgets.channel_control import ChannelControlWidget
from .widgets.keyboard import KeyboardWidget


# Keyboard to note mapping
KEY_TO_NOTE = {
    # White keys (C major scale)
    'a': 'C', 's': 'D', 'd': 'E', 'f': 'F',
    'g': 'G', 'h': 'A', 'j': 'B', 'k': 'C', 'l': 'D',
    # Black keys (sharps)
    'w': 'C#', 'e': 'D#', 't': 'F#', 'y': 'G#', 'u': 'A#',
    'o': 'C#', 'p': 'D#'
}


class NESAudioApp(App):
    """Main NESAUDIO application"""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #left-panel {
        width: 30;
        height: 100%;
        border: solid cyan;
        padding: 1;
    }

    #right-panel {
        width: 1fr;
        height: 100%;
        padding: 1;
    }

    #spectrum-container {
        height: 12;
        border: solid green;
        padding: 1;
        margin-bottom: 1;
    }

    #keyboard-container {
        height: 12;
        border: solid yellow;
        padding: 1;
        margin-bottom: 1;
    }

    #info-container {
        height: auto;
        border: solid magenta;
        padding: 1;
    }

    .channel-widget {
        height: auto;
        margin-bottom: 1;
        padding: 1;
        border: solid blue;
    }

    ChannelControlWidget {
        height: 8;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "toggle_recording", "Record"),
        ("z", "octave_down", "Oct-"),
        ("x", "octave_up", "Oct+"),
        ("1", "select_channel('pulse1')", "Ch1"),
        ("2", "select_channel('pulse2')", "Ch2"),
        ("3", "select_channel('triangle')", "Ch3"),
        ("4", "select_channel('noise')", "Ch4"),
        ("f1", "trigger_effect('jump')", "Jump"),
        ("f2", "trigger_effect('coin')", "Coin"),
        ("f3", "trigger_effect('powerup')", "Powerup"),
        ("f4", "trigger_effect('shoot')", "Shoot"),
        ("f5", "trigger_effect('hit')", "Hit"),
        ("f6", "trigger_effect('explosion')", "Explosion"),
    ]

    current_octave = reactive(4)
    current_channel = reactive("pulse1")
    is_recording = reactive(False)

    def __init__(self):
        super().__init__()
        self.audio_engine = None
        self.music_player = None
        self.preset_manager = None
        self.pressed_keys = {}

        # Widgets
        self.spectrum_widget = None
        self.keyboard_widget = None
        self.channel_widgets = {}
        self.info_label = None

    def compose(self) -> ComposeResult:
        """Create UI layout"""
        yield Header()

        with Container(id="main-container"):
            with Horizontal():
                # Left panel - Channel controls
                with Vertical(id="left-panel"):
                    yield Label("🎵 CHANNELS", classes="section-title")
                    self.channel_widgets['pulse1'] = ChannelControlWidget("Pulse 1", classes="channel-widget")
                    yield self.channel_widgets['pulse1']

                    self.channel_widgets['pulse2'] = ChannelControlWidget("Pulse 2", classes="channel-widget")
                    yield self.channel_widgets['pulse2']

                    self.channel_widgets['triangle'] = ChannelControlWidget("Triangle", classes="channel-widget")
                    yield self.channel_widgets['triangle']

                    self.channel_widgets['noise'] = ChannelControlWidget("Noise", classes="channel-widget")
                    yield self.channel_widgets['noise']

                # Right panel - Main interaction area
                with Vertical(id="right-panel"):
                    # Spectrum analyzer
                    with Container(id="spectrum-container"):
                        yield Label("📊 SPECTRUM ANALYZER")
                        self.spectrum_widget = SpectrumWidget()
                        yield self.spectrum_widget

                    # Keyboard
                    with Container(id="keyboard-container"):
                        self.keyboard_widget = KeyboardWidget()
                        yield self.keyboard_widget

                    # Info panel
                    with Container(id="info-container"):
                        self.info_label = Label("🎹 NESAUDIO v1.0 - Live Mode")
                        yield self.info_label

        yield Footer()

    def on_mount(self) -> None:
        """Initialize audio engine when app starts"""
        try:
            # Initialize audio engine
            self.audio_engine = AudioEngine()
            self.audio_engine.start()

            # Initialize music player
            self.music_player = MusicPlayer(self.audio_engine)

            # Initialize preset manager
            self.preset_manager = PresetManager(self.audio_engine)

            # Start update timer
            self.set_interval(1/30, self.update_display)

            self.update_info(f"Audio engine started | Octave: {self.current_octave} | Channel: {self.current_channel.upper()}")

        except Exception as e:
            self.update_info(f"Error starting audio: {e}")

    def update_display(self):
        """Update display (called periodically)"""
        if not self.audio_engine:
            return

        # Update spectrum
        if self.spectrum_widget:
            spectrum_data = self.audio_engine.get_spectrum_data(32)
            self.spectrum_widget.update_spectrum(spectrum_data)

        # Update channel widgets
        for name, widget in self.channel_widgets.items():
            channel = self.audio_engine.channels.get_channel(name)
            if channel:
                freq = getattr(channel, 'frequency', 0.0) if hasattr(channel, 'active') and channel.active else 0.0
                vol = channel.volume
                duty = getattr(channel, 'duty_cycle', 0.5)
                active = getattr(channel, 'active', False)
                widget.update_state(freq, vol, duty, active)

        # Update music player if playing
        if self.music_player and self.music_player.is_playing():
            self.music_player.update()

    def update_info(self, message: str):
        """Update info label"""
        if self.info_label:
            rec_status = " [●REC]" if self.is_recording else ""
            self.info_label.update(f"{message}{rec_status}")

    async def on_key(self, event: events.Key) -> None:
        """Handle key presses"""
        key = event.key.lower()

        # Check if it's a musical key
        if key in KEY_TO_NOTE:
            await self.play_note(key)
        elif key in ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'w', 'e', 't', 'y', 'u', 'o', 'p']:
            # Already handled above
            pass

    def play_note(self, key: str):
        """Play a note based on key press"""
        if key not in KEY_TO_NOTE:
            return

        note_name = KEY_TO_NOTE[key]

        # Handle upper octave for K and L keys
        octave = self.current_octave
        if key in ['k', 'l', 'o', 'p']:
            octave += 1

        pitch = f"{note_name}{octave}"
        frequency = pitch_to_hz(pitch)

        # Play on current channel
        channel = self.audio_engine.channels.get_channel(self.current_channel)
        if channel and hasattr(channel, 'set_frequency'):
            channel.set_frequency(frequency)
            self.pressed_keys[key] = True

            # Update keyboard widget
            if self.keyboard_widget:
                self.keyboard_widget.press_key(key)

            self.update_info(f"Playing: {pitch} ({frequency:.1f} Hz) on {self.current_channel.upper()} | Oct: {self.current_octave}")

    def action_octave_down(self):
        """Decrease octave"""
        if self.current_octave > 0:
            self.current_octave -= 1
            self.update_info(f"Octave: {self.current_octave}")

    def action_octave_up(self):
        """Increase octave"""
        if self.current_octave < 8:
            self.current_octave += 1
            self.update_info(f"Octave: {self.current_octave}")

    def action_select_channel(self, channel: str):
        """Select active channel"""
        self.current_channel = channel
        self.update_info(f"Channel: {channel.upper()} selected | Octave: {self.current_octave}")

    def action_toggle_recording(self):
        """Toggle recording"""
        if not self.audio_engine:
            return

        if self.is_recording:
            filepath = self.audio_engine.stop_recording()
            self.is_recording = False
            self.update_info(f"Recording saved: {filepath}")
        else:
            self.audio_engine.start_recording()
            self.is_recording = True
            self.update_info("Recording started...")

    def action_trigger_effect(self, effect_name: str):
        """Trigger a sound effect"""
        if self.preset_manager:
            self.preset_manager.trigger(effect_name)
            self.update_info(f"Effect: {effect_name}")

    def on_unmount(self) -> None:
        """Cleanup when app closes"""
        if self.audio_engine:
            self.audio_engine.stop()
