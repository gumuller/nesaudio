"""
Channel control widget
"""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.containers import Vertical
from textual.widgets import Static, Label
from rich.text import Text


class ChannelControlWidget(Widget):
    """Display for a single channel's parameters"""

    def __init__(self, channel_name: str, **kwargs):
        super().__init__(**kwargs)
        self.channel_name = channel_name
        self.frequency = 0.0
        self.volume = 0.8
        self.duty_cycle = 0.5
        self.is_active = False

    def render(self) -> Text:
        """Render the channel control"""
        lines = []
        lines.append(f"[bold]{self.channel_name.upper()}[/bold]")

        # Show frequency if available
        if self.frequency > 0 and self.is_active:
            lines.append(f"Freq: {self.frequency:.1f} Hz")
        else:
            lines.append("Freq: ---")

        # Volume bar
        vol_blocks = int(self.volume * 10)
        vol_bar = "█" * vol_blocks + "░" * (10 - vol_blocks)
        lines.append(f"Vol: {vol_bar}")

        # Duty cycle for pulse channels
        if "pulse" in self.channel_name.lower():
            duty_pct = int(self.duty_cycle * 100)
            lines.append(f"Duty: {duty_pct}%")

        # Active indicator
        status = "●" if self.is_active else "○"
        lines.append(f"Status: {status}")

        return Text.from_markup("\n".join(lines))

    def update_state(self, frequency: float, volume: float, duty_cycle: float, is_active: bool):
        """Update channel state"""
        self.frequency = frequency
        self.volume = volume
        self.duty_cycle = duty_cycle
        self.is_active = is_active
        self.refresh()
