"""
Spectrum analyzer widget
"""

from textual.widget import Widget
from rich.text import Text
import numpy as np


class SpectrumWidget(Widget):
    """Visual spectrum analyzer display with color, decay, and peak hold"""

    def __init__(self, bins: int = 32, **kwargs):
        super().__init__(**kwargs)
        self.bins = bins
        self.spectrum_data = np.zeros(bins)
        self.display_data = np.zeros(bins)    # smoothed bars (decay)
        self.peak_data = np.zeros(bins)       # peak hold indicators
        self.decay_rate = 0.12                # bar fall speed per frame
        self.peak_decay_rate = 0.02           # peak fall speed per frame

    def update_spectrum(self, data: np.ndarray):
        """Update spectrum data with decay and peak hold"""
        self.spectrum_data = data

        # Bars rise instantly, fall gradually
        self.display_data = np.maximum(data, self.display_data - self.decay_rate)

        # Peaks rise instantly, fall very slowly
        self.peak_data = np.maximum(data, self.peak_data - self.peak_decay_rate)

        self.refresh()

    @staticmethod
    def _bar_style(value: float) -> str:
        """Color gradient: green (low) -> yellow (mid) -> red (high)"""
        if value > 0.85:
            return "bright_red bold"
        elif value > 0.7:
            return "red"
        elif value > 0.55:
            return "yellow"
        elif value > 0.35:
            return "green"
        elif value > 0.15:
            return "dark_green"
        return "grey37"

    def render(self) -> Text:
        """Render the spectrum analyzer scaled to widget dimensions"""
        width = self.size.width
        height = self.size.height - 2  # reserve rows for peak line + labels
        if height < 1:
            height = 1
        if width < 1:
            width = 1

        blocks = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        bar_width = max(1, width // self.bins)
        usable_width = bar_width * self.bins

        text = Text()

        # Peak indicator row
        for i in range(self.bins):
            peak_val = self.peak_data[i] if i < len(self.peak_data) else 0
            bar_val = self.display_data[i] if i < len(self.display_data) else 0
            if peak_val > 0.05 and peak_val - bar_val > 0.02:
                segment = "▼" * bar_width
                text.append(segment, style=self._bar_style(peak_val))
            else:
                text.append(" " * bar_width)
        # Pad remainder
        text.append(" " * (width - usable_width))
        text.append("\n")

        # Main bars (render from top row to bottom row)
        for row in range(height - 1, -1, -1):
            row_bottom = row / height
            row_top = (row + 1) / height

            for i in range(self.bins):
                value = self.display_data[i] if i < len(self.display_data) else 0

                if value >= row_top:
                    # Full block
                    char = blocks[-1]
                elif value > row_bottom:
                    # Partial block
                    fraction = (value - row_bottom) / (row_top - row_bottom)
                    block_idx = int(fraction * (len(blocks) - 1))
                    block_idx = min(block_idx, len(blocks) - 1)
                    char = blocks[block_idx]
                else:
                    char = " "

                segment = char * bar_width
                if char != " ":
                    text.append(segment, style=self._bar_style(value))
                else:
                    text.append(segment)

            # Pad remainder of the row
            text.append(" " * (width - usable_width))
            if row > 0:
                text.append("\n")

        # Frequency labels row
        text.append("\n")
        label_line = "Low"
        mid_pos = usable_width // 2 - 1
        high_pos = usable_width - 4
        label_line += " " * max(0, mid_pos - len(label_line))
        label_line += "Mid"
        label_line += " " * max(0, high_pos - len(label_line))
        label_line += "High"
        label_line = label_line[:width]
        text.append(label_line, style="dim")

        return text
